import io
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlsplit
from xml.etree import ElementTree as ET

from scenario_dossier.models import ProjectCredentials
from scenario_dossier.services.demo_service import DemoService
from scenario_dossier.services.thumbnail_service import Thumbnail, ThumbnailService
from scenario_dossier.services.tygron_service import TygronService
from scenario_dossier.tygron import TygronClient, TygronError, TygronRootClient
from scenario_dossier.web import create_app


def png(width=320, height=200):
    def chunk(name, data):
        return struct.pack('>I', len(data)) + name + data + struct.pack('>I', zlib.crc32(name + data))
    header = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    pixels = (b'\0' + b'\xe8\xef\xdf' * width) * height
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', header) + chunk(b'IDAT', zlib.compress(pixels)) + chunk(b'IEND', b'')


CAPABILITIES = b'''<WMS_Capabilities xmlns="http://www.opengis.net/wms"><Capability><Layer><Name>TOPOGRAPHIC</Name><BoundingBox CRS="EPSG:3857" minx="570000" miny="6800000" maxx="571000" maxy="6801000"/></Layer></Capability></WMS_Capabilities>'''


class WmsThumbnailTests(unittest.TestCase):
    def test_official_getmap_uses_topographic_layer_and_header_authentication(self):
        responses = [CAPABILITIES, png()]
        def respond(request, timeout):
            return io.BytesIO(responses.pop(0))
        with patch('scenario_dossier.tygron._open_authenticated', side_effect=respond) as opening:
            result = TygronClient('https://engine.tygron.com', 'private-token').fetch_map_thumbnail()
        self.assertEqual(result, png())
        calls = [call.args[0] for call in opening.call_args_list]
        for request in calls:
            self.assertEqual(request.get_header('Authorization'), 'Bearer private-token')
            self.assertNotIn('private-token', request.full_url)
        params = parse_qs(urlsplit(calls[1].full_url).query)
        self.assertEqual(urlsplit(calls[1].full_url).path, '/web/wms')
        self.assertEqual(params['REQUEST'], ['GetMap'])
        self.assertEqual(params['LAYERS'], ['TOPOGRAPHIC'])
        self.assertEqual(params['FORMAT'], ['image/png'])
        self.assertEqual(params['CRS'], ['EPSG:3857'])
        self.assertEqual(params['WIDTH'], ['320'])
        self.assertEqual(params['HEIGHT'], ['200'])
        west, south, east, north = map(float, params['BBOX'][0].split(','))
        self.assertLess(west, 570000)
        self.assertGreater(east, 571000)
        self.assertLess(south, 6800000)
        self.assertGreater(north, 6801000)
        self.assertAlmostEqual((east - west) / (north - south), 1.6)

    def test_invalid_extent_and_nonimage_responses_are_rejected(self):
        for capabilities in [b'not XML', b'<xml/>', CAPABILITIES.replace(b'570000', b'nan')]:
            with self.subTest(capabilities=capabilities), patch.object(TygronClient, '_get', return_value=capabilities):
                with self.assertRaises(TygronError):
                    TygronClient('https://engine.tygron.com', 't').fetch_map_thumbnail()
        for body in [b'<ServiceExceptionReport>Private error</ServiceExceptionReport>', png(100, 100), b'']:
            with self.subTest(body=body[:20]), patch.object(TygronClient, '_get', side_effect=[CAPABILITIES, body]):
                with self.assertRaises(TygronError):
                    TygronClient('https://engine.tygron.com', 't').fetch_map_thumbnail()

    def test_remote_response_size_is_bounded(self):
        with patch('scenario_dossier.tygron._open_authenticated', return_value=io.BytesIO(b'123456')):
            with self.assertRaises(TygronError):
                TygronClient('https://engine.tygron.com', 't')._get('/web/wms', binary=True, max_bytes=5)

    def test_temporary_session_closes_after_success_and_wms_failure(self):
        credentials = ProjectCredentials('https://engine.tygron.com', 'u', 'key')
        for failure in (False, True):
            session = MagicMock()
            session.__enter__.return_value = session
            if failure:
                session.client.fetch_map_thumbnail.side_effect = TygronError('No WMS')
            else:
                session.client.fetch_map_thumbnail.return_value = png()
            with patch.object(TygronRootClient, 'open_project', return_value=session):
                if failure:
                    with self.assertRaises(TygronError):
                        TygronService().project_thumbnail(credentials, 'city')
                else:
                    self.assertEqual(TygronService().project_thumbnail(credentials, 'city'), png())
            session.__exit__.assert_called_once()


class ThumbnailCacheTests(unittest.TestCase):
    def test_repeated_requests_reuse_image_and_expired_images_reload(self):
        cache = ThumbnailService(lifetime=10)
        loader = MagicMock(return_value=Thumbnail(png(), 'image/png'))
        with patch('scenario_dossier.services.thumbnail_service.monotonic', return_value=100):
            self.assertIs(cache.get('city', loader), cache.get('city', loader))
        self.assertEqual(loader.call_count, 1)
        with patch('scenario_dossier.services.thumbnail_service.monotonic', return_value=111):
            cache.get('city', loader)
        self.assertEqual(loader.call_count, 2)

    def test_failures_are_throttled_and_cache_is_bounded(self):
        cache = ThumbnailService(capacity=2)
        failure = MagicMock(side_effect=TygronError('unavailable'))
        self.assertIsNone(cache.get('bad', failure))
        self.assertIsNone(cache.get('bad', failure))
        failure.assert_called_once()
        for key in ('one', 'two', 'three'):
            cache.get(key, lambda: Thumbnail(png(), 'image/png'))
        self.assertEqual(list(cache._cache), ['two', 'three'])

    def test_slow_project_does_not_block_other_projects_or_memory_hits(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Event
        cache = ThumbnailService(max_parallel=3)
        image = Thumbnail(png(), 'image/png')
        cache.get('cached', lambda: image)
        entered, release = Event(), Event()
        def slow():
            entered.set()
            release.wait(3)
            return image
        with ThreadPoolExecutor(max_workers=3) as pool:
            first = pool.submit(cache.get, 'slow', slow)
            try:
                self.assertTrue(entered.wait(1))
                fast = pool.submit(cache.get, 'fast', lambda: image)
                hit = pool.submit(cache.get, 'cached', lambda: self.fail('Cache hit regenerated'))
                self.assertEqual(fast.result(timeout=1), image)
                self.assertEqual(hit.result(timeout=1), image)
                self.assertFalse(first.done())
            finally:
                release.set()
            self.assertEqual(first.result(timeout=1), image)

    def test_parallel_generation_is_bounded_and_same_key_is_deduplicated(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Event, Lock
        cache = ThumbnailService(max_parallel=3)
        release, three_started = Event(), Event()
        guard = Lock()
        counts = {'active': 0, 'maximum': 0, 'calls': 0}
        def loader():
            with guard:
                counts['active'] += 1
                counts['calls'] += 1
                counts['maximum'] = max(counts['maximum'], counts['active'])
                if counts['active'] == 3:
                    three_started.set()
            release.wait(3)
            with guard:
                counts['active'] -= 1
            return Thumbnail(png(), 'image/png')
        with ThreadPoolExecutor(max_workers=34) as pool:
            requests = [pool.submit(cache.get, ('project', index), loader) for index in range(33)]
            duplicate = pool.submit(cache.get, ('project', 0), loader)
            try:
                self.assertTrue(three_started.wait(1))
                self.assertEqual(counts['active'], 3)
            finally:
                release.set()
            images = [result.result(timeout=3) for result in requests]
            self.assertEqual(duplicate.result(timeout=1), images[0])
        self.assertEqual(counts['calls'], 33)
        self.assertEqual(counts['maximum'], 3)

    def test_disk_cache_survives_restart_and_expired_or_corrupt_files_reload(self):
        import os
        from time import time
        image = Thumbnail(png(), 'image/png')
        key = ('tygron', 'engine', 'user', 'domain', 'city', 'Current', 'revision')
        with tempfile.TemporaryDirectory() as directory:
            first = ThumbnailService(cache_dir=directory, lifetime=100)
            first.get(key, lambda: image)
            files = list(Path(directory).glob('*.thumbnail'))
            self.assertEqual(len(files), 1)
            self.assertNotIn('user', files[0].name)
            second = ThumbnailService(cache_dir=directory, lifetime=100)
            self.assertEqual(second.get(key, lambda: self.fail('Restart regenerated image')), image)
            os.utime(files[0], (time() - 101, time() - 101))
            loader = MagicMock(return_value=image)
            ThumbnailService(cache_dir=directory, lifetime=100).get(key, loader)
            loader.assert_called_once()
            files[0].write_bytes(b'broken cache')
            loader.reset_mock()
            ThumbnailService(cache_dir=directory, lifetime=100).get(key, loader)
            loader.assert_called_once()

    def test_disk_hits_are_available_while_generation_slots_are_full(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Event
        image = Thumbnail(png(), 'image/png')
        with tempfile.TemporaryDirectory() as directory:
            ThumbnailService(cache_dir=directory).get('saved', lambda: image)
            cache = ThumbnailService(cache_dir=directory, max_parallel=1)
            entered, release = Event(), Event()
            def slow():
                entered.set()
                release.wait(3)
                return image
            with ThreadPoolExecutor(max_workers=2) as pool:
                pending = pool.submit(cache.get, 'slow', slow)
                try:
                    self.assertTrue(entered.wait(1))
                    disk_hit = pool.submit(cache.get, 'saved', lambda: self.fail('Disk hit regenerated'))
                    self.assertEqual(disk_hit.result(timeout=1), image)
                    self.assertFalse(pending.done())
                finally:
                    release.set()
                pending.result(timeout=1)

    def test_demo_previews_contain_actual_shapes_without_external_resources(self):
        for project in DemoService().list_projects():
            image = ThumbnailService.demo(project)
            self.assertEqual(image.mimetype, 'image/svg+xml')
            root = ET.fromstring(image.data)
            self.assertTrue(any(node.tag.endswith(('path', 'circle')) for node in root))
            self.assertNotIn(b'<script', image.data)
            self.assertNotIn(b'href=', image.data)
            self.assertNotIn(b'http', image.data.replace(b'http://www.w3.org/2000/svg', b''))


class ThumbnailRouteTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.app = create_app({'TESTING': True, 'THUMBNAIL_CACHE_DIR': None, 'SECRET_KEY': 'test', 'EXPORT_DIR': Path(self.directory.name)})
        self.client = self.app.test_client()

    def login_and_catalog(self):
        with patch.object(TygronRootClient, 'get_login_key', return_value='private-login-key'):
            self.client.post('/api/auth/login', json={'username': 'user', 'password': 'password'})
        with patch.object(TygronRootClient, 'list_projects', return_value=[{'fileName': 'city', 'name': 'City', 'versions': ['Current']}]):
            self.client.get('/api/tygron/projects')

    def test_authentication_and_project_access_are_checked_before_generation(self):
        with patch.object(TygronService, 'project_thumbnail') as generate:
            self.assertEqual(self.client.post('/api/tygron/thumbnail', json={'project_file': 'city'}).status_code, 401)
            self.login_and_catalog()
            self.assertEqual(self.client.post('/api/tygron/thumbnail', json={'project_file': 'other'}).status_code, 404)
            generate.assert_not_called()
        self.assertEqual(self.client.get('/api/tygron/thumbnail').status_code, 404)

    def test_image_cache_and_logout_never_expose_or_bypass_credentials(self):
        self.login_and_catalog()
        with patch.object(TygronService, 'project_thumbnail', return_value=png()) as generate:
            for _ in range(2):
                result = self.client.post('/api/tygron/thumbnail', json={'project_file': 'city', 'login_key': 'attacker'})
                self.assertEqual(result.status_code, 200)
                self.assertEqual(result.mimetype, 'image/png')
                self.assertEqual(result.data, png())
                self.assertEqual(result.headers['Cache-Control'], 'no-store')
                self.assertNotIn(b'private-login-key', result.data)
            generate.assert_called_once()
            self.assertEqual(generate.call_args.args[0].login_key, 'private-login-key')
        self.client.post('/api/auth/logout', json={})
        self.assertEqual(self.client.post('/api/tygron/thumbnail', json={'project_file': 'city'}).status_code, 401)

    def test_relogin_reuses_image_but_changed_project_revision_regenerates(self):
        self.login_and_catalog()
        with patch.object(TygronService, 'project_thumbnail', return_value=png()) as generate:
            self.assertEqual(self.client.post('/api/tygron/thumbnail', json={'project_file': 'city'}).status_code, 200)
            self.client.post('/api/auth/logout', json={})
            self.login_and_catalog()
            self.assertEqual(self.client.post('/api/tygron/thumbnail', json={'project_file': 'city'}).status_code, 200)
            self.assertEqual(generate.call_count, 1)
            with patch.object(TygronRootClient, 'list_projects', return_value=[{
                'fileName': 'city', 'name': 'City', 'versions': ['Current'], 'lastActivity': 12345
            }]):
                self.client.get('/api/tygron/projects')
            self.assertEqual(self.client.post('/api/tygron/thumbnail', json={'project_file': 'city'}).status_code, 200)
            self.assertEqual(generate.call_count, 2)

    def test_optional_image_failure_does_not_invalidate_account(self):
        self.login_and_catalog()
        with patch.object(TygronService, 'project_thumbnail', side_effect=TygronError('secret internal error', status_code=401)):
            result = self.client.post('/api/tygron/thumbnail', json={'project_file': 'city'})
        self.assertEqual(result.status_code, 204)
        self.assertTrue(self.client.get('/api/auth/session').json['authenticated'])
        self.assertNotIn('secret', result.text)

    def test_demo_images_work_without_login(self):
        for project in self.client.get('/api/demo/projects').json:
            result = self.client.get('/api/demo/thumbnail/' + project['id'])
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.mimetype, 'image/svg+xml')
            ET.fromstring(result.data)
        self.assertEqual(self.client.get('/api/demo/thumbnail/missing').status_code, 400)


class ThumbnailQueueFrontendTests(unittest.TestCase):
    def test_33_project_queue_is_parallel_and_does_not_wait_for_first_image(self):
        import shutil
        import subprocess
        executable = shutil.which('node')
        if executable is None:
            self.skipTest('Node is optional; queue checks can be performed in the browser.')
        result = subprocess.run([executable, str(Path(__file__).with_name('frontend_thumbnail_queue.mjs'))], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
