import base64
import io
import json
import tempfile
import unittest
import urllib.error
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from scenario_dossier.i18n import CATALOGS, translate, translate_message
from scenario_dossier.models import ScenarioData, TygronConnection, ProjectCredentials
from scenario_dossier.tygron import TygronRootClient, TygronClient, TygronError, _validate_base_url
from scenario_dossier.web import create_app


class ApplicationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.app = create_app({'TESTING': True, 'THUMBNAIL_CACHE_DIR': None, 'SECRET_KEY': 'test-secret', 'EXPORT_DIR': Path(self.directory.name)})
        self.client = self.app.test_client()

    def login(self):
        with patch.object(TygronRootClient, 'get_login_key', return_value='private-login-key'):
            response = self.client.post('/api/auth/login', json={'username': 'test-user', 'password': 'private-password'})
        self.assertEqual(response.status_code, 200)
        return response

    def catalog(self, projects=None):
        if projects is None:
            projects = [{'fileName': 'city', 'name': 'City', 'description': 'Planning', 'versions': ['Old', 'Current'], 'activeVersion': 1, 'login_key': 'must-not-leak'}]
        with patch.object(TygronRootClient, 'list_projects', return_value=projects):
            return self.client.get('/api/tygron/projects')

    def test_start_pages_and_restored_assets(self):
        for url, content in [('/', 'loginForm'), ('/workflow?mode=legacy', 'liveProject'), ('/controle', 'archiveInput'), ('/werkinstructie', 'markdown')]:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertIn(content, response.text)
        for url in ['/static/app.js', '/static/vendor/maplibre-gl.mjs', '/provincie-utrecht-logo.svg', '/api/map-config']:
            with self.client.get(url) as response:
                self.assertEqual(response.status_code, 200)

    def test_default_navigation_opens_projects_instead_of_legacy_source_form(self):
        self.assertEqual(self.client.get('/workflow').location, '/login')
        self.assertEqual(self.client.get('/workflow?mode=demo').location, '/projecten?mode=demo')
        self.assertEqual(self.client.get('/workflow?mode=account').location, '/login')
        self.login()
        self.assertEqual(self.client.get('/workflow').location, '/projecten')
        self.assertEqual(self.client.get('/index.html').location, '/projecten')
        projects = self.client.get('/projecten')
        self.assertIn('id="projectList"', projects.text)
        self.assertIn('data-source="tygron"', projects.text)
        self.assertNotIn('id="liveProject"', projects.text)
        self.assertIn('href="/projecten"', projects.text)

    def test_demo_uses_same_project_dashboard_and_enters_map_at_step_three(self):
        page = self.client.get('/projecten?mode=demo')
        self.assertEqual(page.status_code, 200)
        self.assertIn('id="projectList"', page.text)
        self.assertIn('data-source="demo"', page.text)
        self.assertIn('id="projectSearch"', page.text)
        self.assertNotIn('id="liveProject"', page.text)
        project = self.client.get('/api/demo/projects').json[0]
        url = f"/workflow?mode=demo&project_id={project['id']}&scenario_id={project['scenarios'][0]['id']}"
        workflow = self.client.get(url)
        self.assertEqual(workflow.status_code, 200)
        self.assertIn('class="panel active" id="step3"', workflow.text)
        self.assertNotIn('class="panel active" id="step2"', workflow.text)
        self.assertIn('id="reviewScenario"', workflow.text)
        for mode in ('tygron', 'legacy'):
            self.assertEqual(self.client.get(f'/workflow?mode={mode}').status_code, 200)

    def test_login_cookie_and_server_memory_never_contain_password(self):
        response = self.login()
        cookie = response.headers['Set-Cookie']
        self.assertIn('HttpOnly', cookie)
        self.assertIn('SameSite=Lax', cookie)
        for secret in ['private-password', 'private-login-key', 'test-user']:
            self.assertNotIn(secret, response.text + cookie)
        with self.client.session_transaction() as browser_session:
            self.assertEqual(set(browser_session), {'account_id'})
            account = self.app.extensions['auth'].get(browser_session['account_id'])
        self.assertEqual(account.credentials.login_key, 'private-login-key')
        self.assertNotIn('private-password', repr(self.app.extensions['auth'].__dict__))
        self.assertNotIn('private-login-key', repr(account))
        self.assertEqual(self.client.get('/').location, '/projecten')
        self.assertEqual(self.client.get('/projecten').status_code, 200)

    def test_failed_login_does_not_create_session_or_leak_upstream_text(self):
        with patch.object(TygronRootClient, 'get_login_key', side_effect=TygronError('secret upstream password', status_code=401)):
            response = self.client.post('/api/auth/login', json={'username': 'bad', 'password': 'wrong'})
        self.assertEqual(response.status_code, 401)
        self.assertIn('Inloggen mislukt', response.json['error'])
        self.assertNotIn('secret', response.text)
        self.assertFalse(self.client.get('/api/auth/session').json['authenticated'])

    def test_bad_login_response_and_network_failure(self):
        for error in [TygronError('raw private response'), TygronError('unreachable')]:
            with patch.object(TygronRootClient, 'get_login_key', side_effect=error):
                response = self.client.post('/api/auth/login', json={'username': 'u', 'password': 'p'})
            self.assertEqual(response.status_code, 502)
            self.assertNotIn('private', response.text)
        self.assertEqual(self.client.post('/api/auth/login', json={'username': 'u', 'password': ''}).status_code, 400)

    def test_session_rotation_logout_and_expiry(self):
        self.login()
        with self.client.session_transaction() as state:
            first = state['account_id']
        self.login()
        self.assertIsNone(self.app.extensions['auth'].get(first))
        with self.client.session_transaction() as state:
            current = state['account_id']
        self.app.extensions['auth'].get(current).expires_at = 0
        self.assertEqual(self.client.get('/api/tygron/projects').status_code, 401)
        self.assertIsNone(self.app.extensions['auth'].get(current))
        self.login()
        self.assertEqual(self.client.post('/api/auth/logout', json={}).status_code, 200)
        self.assertFalse(self.client.get('/api/auth/session').json['authenticated'])
        self.assertEqual(self.client.get('/projecten').location, '/login')

    def test_projects_metadata_and_only_active_version(self):
        self.login()
        response = self.catalog()
        self.assertEqual(response.status_code, 200)
        project = response.json['projects'][0]
        self.assertEqual(project['versions'], ['Current'])
        self.assertEqual(project['active_version'], 0)
        self.assertEqual(project['description'], 'Planning')
        self.assertNotIn('login_key', response.text)
        self.assertNotIn('private-login-key', response.text)

    def test_empty_projects_and_upstream_failures(self):
        self.login()
        self.assertEqual(self.catalog([]).json, {'projects': []})
        with patch.object(TygronRootClient, 'list_projects', side_effect=TygronError('private reason')):
            response = self.client.get('/api/tygron/projects')
        self.assertEqual(response.status_code, 502)
        self.assertNotIn('private reason', response.text)
        with patch.object(TygronRootClient, 'list_projects', side_effect=TygronError('denied', status_code=403)):
            response = self.client.get('/api/tygron/projects')
        self.assertEqual(response.status_code, 401)
        self.assertFalse(self.client.get('/api/auth/session').json['authenticated'])

    def test_account_selection_uses_server_credentials_and_project_names(self):
        self.login()
        self.catalog()
        context = MagicMock()
        context.__enter__.return_value = TygronConnection(ScenarioData(overlays=[{'id': 1}]))
        with patch('scenario_dossier.services.tygron_service.TygronService.project_connection', return_value=context) as connect:
            response = self.client.post('/api/inspect', json={'source': 'tygron_project', 'authenticated': True,
                'project_file': 'city', 'project_name': 'spoofed', 'scenario_name': 'historical',
                'username': 'attacker', 'login_key': 'attacker-key', 'base_url': 'https://wrong.example'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual((response.json['project'], response.json['scenario']), ('City', 'Current'))
        self.assertEqual(connect.call_args.args[0].login_key, 'private-login-key')
        self.assertEqual(connect.call_args.args[0].base_url, 'https://engine.tygron.com')
        context.__exit__.assert_called_once()
        bad = self.client.post('/api/inspect', json={'source': 'tygron_project', 'authenticated': True, 'project_file': 'hidden'})
        self.assertEqual(bad.status_code, 400)

    def test_legacy_login_key_project_route_is_preserved(self):
        with patch.object(TygronRootClient, 'list_projects', return_value=[]) as call:
            response = self.client.post('/api/tygron/projects', json={'base_url': 'https://engine.tygron.com', 'username': 'u', 'login_key': 'k', 'domain': 'my-domain'})
        self.assertEqual(response.status_code, 200)
        call.assert_called_once_with('my-domain')

    def test_login_key_has_its_own_page_and_legacy_url_still_works(self):
        for url in ('/login-key', '/workflow?mode=legacy'):
            with self.subTest(url=url):
                page = self.client.get(url)
                self.assertEqual(page.status_code, 200)
                for field in ('loginKeyForm', 'loginKey', 'showLoginKey', 'liveProject', 'liveScenario', 'step3', 'step4'):
                    self.assertIn(f'id="{field}"', page.text)
                for unrelated in ('source-tabs', 'activeSessionForm', 'demoFields'):
                    self.assertNotIn(unrelated, page.text)
        for url in ('/login', '/projecten?mode=demo'):
            self.assertIn('href="/login-key"', self.client.get(url).text)

    def test_active_session_uses_existing_connection_and_raster_fetcher(self):
        with patch('scenario_dossier.services.tygron_service.TygronService.active_connection', return_value=TygronConnection(ScenarioData(measures=[{'id': 7}]))):
            response = self.client.post('/api/inspect', json={'source': 'tygron', 'base_url': 'https://engine.tygron.com', 'token': 'secret', 'project_name': 'P', 'scenario_name': 'S'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['counts']['measures'], 1)

    def test_active_session_has_its_own_form_and_reuses_review_and_export(self):
        page = self.client.get('/workflow?mode=tygron')
        self.assertEqual(page.status_code, 200)
        for field in ('activeSessionForm', 'baseUrl', 'token', 'projectName', 'scenarioName', 'showSessionToken', 'sessionConnectionStatus', 'step3', 'step4'):
            self.assertIn(f'id="{field}"', page.text)
        for unrelated in ('source-tabs', 'id="project"', 'id="scenario"', 'id="liveProject"', 'id="loginKey"', 'data-source="demo"'):
            self.assertNotIn(unrelated, page.text)
        self.assertIn('Verbind met je actieve sessie.', page.text)
        self.assertIn('data-step-href="/workflow?mode=tygron"', page.text)
        self.assertIn('Terug naar actieve sessie', page.text)
        self.assertIn('id="liveProject"', self.client.get('/workflow?mode=legacy').text)
        self.client.set_cookie('language', 'en')
        english = self.client.get('/workflow?mode=tygron').text
        self.assertIn('Connect to your active session.', english)
        self.assertIn('Back to active session', english)

    def test_invalid_active_session_token_has_scoped_error_and_keeps_account(self):
        self.login()
        payload = {'source': 'tygron', 'base_url': 'https://engine.tygron.com', 'token': 'private-token', 'project_name': 'P', 'scenario_name': 'S'}
        for endpoint in ('/api/inspect', '/api/export'):
            with self.subTest(endpoint=endpoint), patch('scenario_dossier.services.tygron_service.TygronService.active_connection', side_effect=TygronError('upstream private-token', status_code=401)):
                response = self.client.post(endpoint, json=payload)
                self.assertEqual(response.status_code, 401)
                self.assertIn('Controleer de sessie-URL en het API-token', response.json['error'])
                self.assertNotIn('private-token', response.text)
                self.assertTrue(self.client.get('/api/auth/session').json['authenticated'])

    def test_demo_selection_export_download_and_validate(self):
        projects = self.client.get('/api/demo/projects').json
        self.assertNotIn('data', projects[0]['scenarios'][0])
        self.assertEqual(self.client.get('/api/demo').json['projects'], projects)
        payload = {'source': 'demo', 'project_id': projects[0]['id'], 'scenario_id': projects[0]['scenarios'][0]['id']}
        inspected = self.client.post('/api/inspect', json=payload)
        self.assertEqual(inspected.status_code, 200)
        key = next(item['key'] for item in inspected.json['items'] if item['component'] == 'overlays')
        payload.update(components=['overlays'], selected_items={'overlays': [key]}, username='should-not-export', password='do-not-export', login_key='neither-this')
        exported = self.client.post('/api/export', json=payload)
        self.assertEqual(exported.status_code, 200)
        download = self.client.get(exported.json['download'])
        self.addCleanup(download.close)
        self.assertEqual(download.status_code, 200)
        with zipfile.ZipFile(io.BytesIO(download.data)) as archive:
            self.assertEqual(len(json.loads(archive.read('bron/overlays.json'))), 1)
            self.assertEqual(json.loads(archive.read('bron/measures.json')), [])
            contents = b''.join(archive.read(name) for name in archive.namelist())
            for secret in (b'should-not-export', b'do-not-export', b'neither-this'):
                self.assertNotIn(secret, contents)
        validated = self.client.post('/api/validate', data=download.data, content_type='application/zip')
        self.assertEqual(validated.status_code, 200)
        self.assertEqual(validated.json['status'], 'goedgekeurd')

    def test_json_validation_upload_errors_and_cross_origin_protection(self):
        self.assertEqual(self.client.post('/api/inspect', json=[]).status_code, 400)
        self.assertEqual(self.client.post('/api/auth/login', data='username=a&password=b', content_type='application/x-www-form-urlencoded').status_code, 415)
        self.assertEqual(self.client.post('/api/auth/logout', json={}, headers={'Origin': 'https://other.example'}).status_code, 403)
        self.assertEqual(self.client.post('/api/validate', data=b'bad zip').status_code, 400)
        self.assertEqual(self.client.get('/api/download/README.md').status_code, 400)
        self.assertEqual(self.client.get('/api/download/../../README.md').status_code, 404)

    def test_language_cookie_all_pages_and_fallback(self):
        self.assertIn('Inloggen', self.client.get('/').text)
        self.client.set_cookie('language', 'en')
        for path, text in [('/', 'Log in'), ('/workflow?mode=legacy', 'Check connection'), ('/controle', 'Validate dossier'), ('/werkinstructie', 'User guide')]:
            page = self.client.get(path).text
            self.assertIn('<html lang="en">', page)
            self.assertIn(text, page)
            self.assertIn('data-language="en" aria-pressed="true"', page)
        with self.client.get('/api/werkinstructie') as response:
            self.assertIn('# ScenarioDossier user guide', response.text)
        self.login()
        self.assertIn('Projects', self.client.get('/projecten').text)
        self.client.set_cookie('language', 'xx')
        self.assertIn('<html lang="nl">', self.client.get('/workflow?mode=legacy').text)
        self.assertEqual(translate('untranslated', 'en'), 'untranslated')
        self.assertEqual(set(CATALOGS['nl']), set(CATALOGS['en']))
        self.assertEqual(self.client.get('/api/translations/en').json['Inloggen'], 'Log in')
        self.assertEqual(self.client.get('/api/translations/xx').status_code, 400)
        self.assertEqual(translate_message('12 bestanden zijn ongewijzigd', 'en'), '12 files are unchanged')


class TygronAuthenticationTests(unittest.TestCase):
    def test_official_login_key_event_uses_basic_header_and_no_url_credentials(self):
        response = MagicMock()
        response.read.return_value = b'"returned-key"'
        response.__enter__.return_value = response
        with patch('scenario_dossier.tygron._open_authenticated', return_value=response) as opening:
            key = TygronRootClient('https://engine.tygron.com', 'username', 'password').get_login_key()
        self.assertEqual(key, 'returned-key')
        request = opening.call_args.args[0]
        self.assertEqual(request.full_url, 'https://engine.tygron.com/api/event/user/get_my_login_key/?f=JSON')
        self.assertEqual(request.get_header('Authorization'), 'Basic ' + base64.b64encode(b'username:password').decode())
        self.assertEqual(request.method, 'POST')
        self.assertNotIn('password', request.full_url)
        self.assertEqual(request.data, b'')

    def test_invalid_login_key_response(self):
        for value in [None, {}, [], '', '<html>login</html>', 'line\nbreak']:
            with self.subTest(value=value), patch.object(TygronRootClient, '_post', return_value=value):
                with self.assertRaises(TygronError):
                    TygronRootClient('https://engine.tygron.com', 'u', 'p').get_login_key()

    def test_credentials_are_not_forwarded_to_redirect_targets(self):
        from scenario_dossier.tygron import _CredentialRedirectHandler
        from urllib.request import Request
        handler = _CredentialRedirectHandler()
        request = Request('https://engine.tygron.com/api/', headers={'Authorization': 'Basic secret'})
        with self.assertRaises(urllib.error.HTTPError):
            handler.redirect_request(request, None, 302, 'Found', {}, 'https://other.example/')

    def test_http_authentication_status_is_preserved(self):
        error = urllib.error.HTTPError('https://engine.tygron.com/api/', 401, 'Denied', {}, None)
        with patch('scenario_dossier.tygron._open_authenticated', side_effect=error):
            with self.assertRaises(TygronError) as raised:
                TygronRootClient('https://engine.tygron.com', 'u', 'p').get_login_key()
        self.assertEqual(raised.exception.status_code, 401)

    def test_base_url_rejects_userinfo_plain_http_and_localhost_prefix_trick(self):
        for url in ['https://user:password@engine.tygron.com', 'https://engine.tygron.com?token=secret', 'http://localhost.attacker.example', 'http://engine.tygron.com']:
            with self.subTest(url=url), self.assertRaises(TygronError):
                _validate_base_url(url)
        self.assertEqual(_validate_base_url('http://127.0.0.1:8000/'), 'http://127.0.0.1:8000')

    def test_bad_json_is_reported_as_tygron_error(self):
        response = MagicMock()
        response.read.return_value = b'not json'
        response.__enter__.return_value = response
        with patch('scenario_dossier.tygron._open_authenticated', return_value=response):
            with self.assertRaises(TygronError):
                TygronClient('https://engine.tygron.com', 'token').fetch_component('overlays')


class FrontendTranslationTests(unittest.TestCase):
    def test_switch_preserves_form_state_and_translates_dynamic_counts(self):
        import shutil
        import subprocess
        executable = shutil.which('node')
        if executable is None:
            self.skipTest('Node is optional; browser translation checks can be run manually.')
        result = subprocess.run([executable, str(Path(__file__).with_name('frontend_i18n.mjs'))], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class ProjectCatalogFrontendTests(unittest.TestCase):
    def test_project_search_and_selection_for_account_and_demo(self):
        import shutil
        import subprocess
        executable = shutil.which('node')
        if executable is None:
            self.skipTest('Node is optional; project search can be checked in the browser.')
        result = subprocess.run([executable, str(Path(__file__).with_name('frontend_projects.mjs'))], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class ReviewSelectionFrontendTests(unittest.TestCase):
    def test_large_selection_search_filters_and_component_scoped_keys(self):
        import shutil
        import subprocess
        executable = shutil.which('node')
        if executable is None:
            self.skipTest('Node is optional; selection can be checked in the browser.')
        result = subprocess.run([executable, str(Path(__file__).with_name('frontend_review_selection.mjs'))], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
