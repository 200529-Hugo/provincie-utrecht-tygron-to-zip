import json
import unittest
from unittest.mock import patch

from scenario_dossier.tygron import TygronClient, TygronRootClient


class FakeResponse:
    def __init__(self, value):
        self.body = value if isinstance(value, bytes) else json.dumps(value).encode()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return None

    def read(self):
        return self.body


class TygronClientTests(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_fetches_spatial_measures_and_panel_alerts(self, urlopen):
        responses = {
            "overlays": [{"id": 1, "name": "Heat", "warnings": "Te warm"}],
            "indicators": [{"id": 2, "name": "Green"}],
            "measures": {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [5.1, 52.1]},
                    "properties": {"id": 3, "name": "Park"},
                }],
            },
            "panels": [{
                "id": 4,
                "name": "Aandacht",
                "text": "Controleer dit gebied",
                "point": {"type": "Point", "coordinates": [5.2, 52.2]},
                "attributes": {"ATTENTION": [1.0]},
            }],
        }

        def response(request, timeout=0):
            url = request.full_url
            for name, value in responses.items():
                if f"/{name}/" in url:
                    return FakeResponse(value)
            raise AssertionError(url)

        urlopen.side_effect = response
        data, warnings = TygronClient("https://engine.tygron.com", "token").fetch_all()

        self.assertEqual(len(data["measures"]), 1)
        self.assertEqual(data["measures"][0]["geometry"]["type"], "Point")
        self.assertEqual(len(data["alerts"]), 2)
        self.assertEqual(data["alerts"][1]["properties"]["source"], "panels")
        self.assertEqual(warnings, [])
        measure_url = next(
            call.args[0].full_url
            for call in urlopen.call_args_list
            if "/measures/" in call.args[0].full_url
        )
        self.assertIn("f=GEOJSON", measure_url)
        self.assertIn("crs=4326", measure_url)


class TygronRootClientTests(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_lists_opens_joins_and_closes_project(self, urlopen):
        calls = []

        def response(request, timeout=0):
            path = request.full_url
            payload = json.loads(request.data or b"null")
            calls.append((path, payload, request.headers.get("Authorization")))
            if "get_domain_startable_projects" in path:
                return FakeResponse([{"fileName": "demo_project", "versions": ["Base"]}])
            if "/start/" in path:
                return FakeResponse(123)
            if "/join/" in path:
                return FakeResponse({
                    "apiToken": "api-token",
                    "client": {"clientToken": "client-token"},
                })
            if "/close/" in path:
                return FakeResponse(None)
            raise AssertionError(path)

        urlopen.side_effect = response
        root = TygronRootClient("https://engine.tygron.com", "user@example.com", "login-key")

        projects = root.list_projects("Provincie Utrecht")
        self.assertEqual(projects[0]["fileName"], "demo_project")
        with root.open_project("demo_project") as session:
            self.assertEqual(session.client.token, "api-token")

        self.assertEqual(calls[0][1], "Provincie Utrecht")
        self.assertEqual(calls[1][1], ["EDITOR", "demo_project"])
        self.assertEqual(calls[2][1], [123, "EDITOR", "ScenarioDossier"])
        self.assertEqual(calls[3][1], [123, "client-token", False])
        self.assertTrue(all(auth.startswith("Basic ") for _, _, auth in calls))


if __name__ == "__main__":
    unittest.main()
