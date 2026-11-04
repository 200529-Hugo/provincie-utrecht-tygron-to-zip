import importlib.util
import ast
import io
import json
import re
import shutil
import subprocess
import tokenize
import unittest
from pathlib import Path
from unittest.mock import patch

from scenario_dossier.http.contracts import API_CONTRACTS
from scenario_dossier.models.api.requests.auth import LoginRequest
from scenario_dossier.models.api.requests.workflow import ExportRequest, InspectRequest
from scenario_dossier.models.tygron.api.requests.root import CloseSessionRequest, JoinSessionRequest, StartProjectRequest
from scenario_dossier.models.tygron.api.responses.root import JoinSessionResponse, StartProjectResponse
from scenario_dossier.models.tygron.api.responses.session import ComponentResponse
from scenario_dossier.tygron import TygronError, TygronRootClient
from scenario_dossier.web import create_app

ROOT = Path(__file__).parents[1]


class ApiContractTests(unittest.TestCase):
    def test_every_api_route_has_a_unique_payload_and_response_contract(self):
        app = create_app({'TESTING': True, 'THUMBNAIL_CACHE_DIR': None})
        actual = {(method, rule.rule) for rule in app.url_map.iter_rules()
                  if rule.rule.startswith('/api/') for method in rule.methods - {'HEAD', 'OPTIONS'}}
        declared = {(item.method, item.path) for item in API_CONTRACTS}
        self.assertEqual(actual, declared)
        self.assertEqual(len(API_CONTRACTS), len(declared))
        for rule in app.url_map.iter_rules():
            if rule.rule.startswith('/api/'):
                self.assertTrue(hasattr(app.view_functions[rule.endpoint], 'api_contract'))

    def test_payloads_validate_nested_types_without_mutating_the_input(self):
        values = {'source': 'demo', 'project_id': 'p', 'scenario_id': 's',
                  'components': ['overlays'], 'selected_items': {'overlays': ['id:1']},
                  'dossier': {'owner': 'Team'}}
        original = json.dumps(values)
        model = ExportRequest.from_dict(values)
        self.assertEqual(model.dossier.owner, 'Team')
        self.assertEqual(model.selected_items['overlays'], ['id:1'])
        self.assertEqual(json.dumps(values), original)
        for field, value in [('rasters', 'true'), ('components', 'overlays'),
                             ('selected_items', {'overlays': 'id:1'}), ('dossier', []), ('notes', {})]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                ExportRequest.from_dict(values | {field: value})

    def test_empty_action_payload_keeps_logout_without_a_json_body_working(self):
        app = create_app({'TESTING': True, 'THUMBNAIL_CACHE_DIR': None})
        response = app.test_client().post('/api/auth/logout')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'ok': True})

    def test_private_fields_are_not_in_model_representations(self):
        login = LoginRequest.from_dict({'username': 'u', 'password': 'private-password'})
        workflow = InspectRequest.from_dict({'token': 'private-token', 'login_key': 'private-key'})
        self.assertNotIn('private-password', repr(login))
        self.assertNotIn('private-token', repr(workflow))
        self.assertNotIn('private-key', repr(workflow))
        self.assertNotIn('private-client-token', repr(CloseSessionRequest(1, 'private-client-token')))

    def test_tygron_session_contracts_keep_wire_payloads_and_token_variants(self):
        self.assertEqual(StartProjectRequest('city').to_payload(), ['EDITOR', 'city'])
        self.assertEqual(JoinSessionRequest(123).to_payload(), [123, 'EDITOR', 'ScenarioDossier'])
        self.assertEqual(CloseSessionRequest(123, 'ct').to_payload(), [123, 'ct', False])
        joined = JoinSessionResponse.from_api({'apiToken': 'api', 'client': {'clientToken': 'ct'}})
        self.assertEqual(joined.client_token, 'ct')
        self.assertNotIn('api_token=', repr(joined))
        with self.assertRaises(TygronError):
            StartProjectResponse.from_api(None)

    def test_tygron_domain_lookup_keeps_the_existing_fallback(self):
        client = TygronRootClient('https://engine.tygron.com', 'u', 'k')
        projects = [{'fileName': 'city'}]
        with patch.object(client, '_post', side_effect=[{'domainName': 'Utrecht'}, projects]) as call:
            self.assertEqual(client.list_projects(), projects)
        self.assertIn('get_my_user', call.call_args_list[0].args[0])
        self.assertEqual(call.call_args_list[1].args[1], 'Utrecht')

    def test_malformed_tygron_components_are_rejected_before_inventory(self):
        for value in ({'type': 'FeatureCollection', 'features': None}, [None], 'not a list'):
            with self.subTest(value=value), self.assertRaises(TygronError):
                ComponentResponse.from_api(value, 'measures')

    def test_services_and_models_remain_independent_of_flask(self):
        for folder in ('services', 'models'):
            for path in (ROOT / 'scenario_dossier' / folder).rglob('*.py'):
                for node in ast.walk(ast.parse(path.read_text())):
                    imports = []
                    if isinstance(node, ast.Import):
                        imports = [item.name for item in node.names]
                    elif isinstance(node, ast.ImportFrom):
                        imports = [node.module or '']
                    for name in imports:
                        with self.subTest(path=path, module=name):
                            self.assertNotIn(name.split('.')[0], ('flask', 'werkzeug'))

    def test_configuration_is_passed_to_services_and_public_map_settings(self):
        app = create_app({'TESTING': True, 'THUMBNAIL_CACHE_DIR': None,
                          'AUTH_SESSION_LIFETIME': 300, 'THUMBNAIL_CAPACITY': 8,
                          'THUMBNAIL_FAILURE_LIFETIME': 10,
                          'MAP_STYLE_URL': 'https://maps.example/style.json'})
        self.assertEqual(app.extensions['auth'].lifetime, 300)
        self.assertEqual(app.extensions['thumbnails'].capacity, 8)
        self.assertEqual(app.extensions['thumbnails'].failure_lifetime, 10)
        self.assertEqual(app.test_client().get('/api/map-config').json['style_url'], 'https://maps.example/style.json')

    def test_all_generated_documentation_and_browser_models_are_current(self):
        spec = importlib.util.spec_from_file_location('api_generator', ROOT / 'scripts/generate_api_models.py')
        generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(generator)
        for path, expected in generator.generated_files().items():
            with self.subTest(path=path):
                self.assertEqual(path.read_text(), expected)

    def test_screens_use_the_shared_http_client(self):
        for path in (ROOT / 'static').rglob('*.js'):
            if 'vendor' in path.parts or path.name == 'client.js':
                continue
            with self.subTest(path=path):
                self.assertNotIn('fetch(', path.read_text())

    def test_owned_comments_use_the_requested_style(self):
        python_files = list((ROOT / 'scenario_dossier').rglob('*.py'))
        python_files += list((ROOT / 'scripts').glob('*.py')) + [ROOT / 'app.py', ROOT / 'app-flask.py']
        for path in python_files:
            source = path.read_text()
            comments = [token.string for token in tokenize.generate_tokens(io.StringIO(source).readline)
                        if token.type == tokenize.COMMENT]
            for node in ast.walk(ast.parse(source)):
                if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    docstring = ast.get_docstring(node)
                    if docstring:
                        comments.append(docstring)
            for comment in comments:
                with self.subTest(path=path, comment=comment):
                    self.assertNotIn('—', comment)
                    self.assertNotIn(';', comment)
        for folder in ('static', 'templates'):
            for path in (ROOT / folder).rglob('*'):
                if path.suffix not in ('.js', '.css', '.html') or 'vendor' in path.parts:
                    continue
                comments = re.findall(r'(?m)^\s*//[^\n]*|/\*[\s\S]*?\*/|\{#[\s\S]*?#\}|<!--[\s\S]*?-->', path.read_text())
                for comment in comments:
                    with self.subTest(path=path, comment=comment):
                        self.assertNotIn('—', comment)
                        self.assertNotIn(';', comment)

    @unittest.skipUnless(shutil.which('node'), 'Node is nodig voor browserlogica')
    def test_frontend_http_formats_errors_and_authentication(self):
        result = subprocess.run(['node', str(ROOT / 'tests/frontend_api_client.mjs')],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
