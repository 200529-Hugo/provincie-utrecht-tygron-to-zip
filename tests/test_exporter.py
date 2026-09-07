import hashlib
import json
import sqlite3
import tempfile
import unittest
import zipfile
from contextlib import closing
from pathlib import Path

from scenario_dossier.exporter import build_archive, load_demo, slug
from scenario_dossier.validation import validate_archive, validate_dossier_directory


class ExporterTests(unittest.TestCase):
    def setUp(self):
        demo = load_demo()
        self.scenario = demo["projects"][0]["scenarios"][0]

    def test_slug_is_safe(self):
        self.assertEqual(slug("Groen & Gezond 2040!"), "groen-gezond-2040")
        self.assertEqual(slug(""), "scenario")

    def test_archive_is_complete_and_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive, metadata = build_archive(
                Path(tmp),
                "Testproject",
                "Variant A",
                self.scenario["data"],
                "Besluittekst",
                dossier_fields={
                    "reference": "PU-2026-0142",
                    "owner": "Team Gezonde Leefomgeving",
                    "author": "Testopsteller",
                    "decision_date": "2026-09-01",
                    "decision_status": "Vastgesteld",
                    "alternatives": "Variant B",
                    "classification": "Intern",
                    "retention_period": "20 jaar",
                },
            )
            self.assertTrue(archive.exists())
            expected_measures = len(self.scenario["data"]["measures"])
            self.assertEqual(metadata["components"]["measures"], expected_measures)
            extract = Path(tmp) / "unpacked"
            with zipfile.ZipFile(archive) as zf:
                zf.extractall(extract)
            dossier = json.loads((extract / "metadata/dossier.json").read_text())
            self.assertEqual(dossier["notes"], "Besluittekst")
            self.assertEqual(dossier["record"]["reference"], "PU-2026-0142")
            self.assertEqual(dossier["decision"]["status"], "Vastgesteld")
            self.assertFalse(dossier["token_archived"])
            report_html = (extract / "rapport/dossierrapport.html").read_text()
            self.assertIn("Team Gezonde Leefomgeving", report_html)
            self.assertIn("Variant B", report_html)
            report = json.loads((extract / "metadata/validatierapport.json").read_text())
            self.assertEqual(report["status"], "goedgekeurd")
            self.assertEqual(report["checks_failed"], 0)
            self.assertEqual(validate_dossier_directory(extract)["status"], "goedgekeurd")
            with closing(sqlite3.connect(extract / "gis/scenario.gpkg")) as con:
                tables = {r[0] for r in con.execute("SELECT table_name FROM gpkg_contents")}
                self.assertEqual(tables, {"overlays", "indicators", "measures", "alerts"})
                self.assertEqual(con.execute("SELECT count(*) FROM measures").fetchone()[0], expected_measures)
                self.assertEqual(con.execute("SELECT count(geom) FROM measures").fetchone()[0], expected_measures)
            for line in (extract / "metadata/manifest-sha256.txt").read_text().splitlines():
                digest, rel = line.split("  ", 1)
                self.assertEqual(hashlib.sha256((extract / rel).read_bytes()).hexdigest(), digest)
            archive_report = validate_archive(archive)
            self.assertEqual(archive_report["status"], "goedgekeurd")
            self.assertEqual(archive_report["project"], "Testproject")

    def test_changed_archive_fails_manifest_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive, _ = build_archive(root, "P", "S", self.scenario["data"])
            unpacked = root / "changed"
            with zipfile.ZipFile(archive) as package:
                package.extractall(unpacked)
            (unpacked / "bron/alerts.json").write_text("[]", encoding="utf-8")
            changed = root / "changed.zip"
            with zipfile.ZipFile(changed, "w", zipfile.ZIP_DEFLATED) as package:
                for file in unpacked.rglob("*"):
                    if file.is_file():
                        package.write(file, file.relative_to(unpacked))
            report = validate_archive(changed)
            self.assertEqual(report["status"], "afgekeurd")
            manifest = next(item for item in report["checks"] if item["check"] == "SHA-256-manifest")
            self.assertEqual(manifest["status"], "fout")

    def test_archive_rejects_unsafe_member_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "unsafe.zip"
            with zipfile.ZipFile(archive, "w") as package:
                package.writestr("../outside.txt", "unsafe")
            with self.assertRaisesRegex(ValueError, "onveilig bestandspad"):
                validate_archive(archive)

    def test_empty_components_still_create_tables(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive, _ = build_archive(Path(tmp), "P", "S", {k: [] for k in ("overlays", "indicators", "measures", "alerts")})
            self.assertGreater(archive.stat().st_size, 0)

    def test_every_demo_scenario_can_be_archived(self):
        demo = load_demo()
        with tempfile.TemporaryDirectory() as tmp:
            for project in demo["projects"]:
                for scenario in project["scenarios"]:
                    with self.subTest(project=project["id"], scenario=scenario["id"]):
                        archive, summary = build_archive(
                            Path(tmp),
                            project["name"],
                            scenario["name"],
                            scenario["data"],
                        )
                        self.assertEqual(validate_archive(archive)["status"], "goedgekeurd")
                        self.assertEqual(
                            sum(summary["components"].values()),
                            sum(len(items) for items in scenario["data"].values()),
                        )

    def test_geometry_collection_is_written(self):
        data = {k: [] for k in ("overlays", "indicators", "measures", "alerts")}
        data["measures"] = [{
            "type": "Feature",
            "geometry": {
                "type": "GeometryCollection",
                "geometries": [
                    {"type": "Point", "coordinates": [5.1, 52.1]},
                    {"type": "LineString", "coordinates": [[5.1, 52.1], [5.2, 52.2]]},
                ],
            },
            "properties": {"id": 1, "name": "Combinatiemaatregel"},
        }]
        with tempfile.TemporaryDirectory() as tmp:
            archive, _ = build_archive(Path(tmp), "P", "S", data)
            with zipfile.ZipFile(archive) as zf:
                gpkg = Path(tmp) / "scenario.gpkg"
                gpkg.write_bytes(zf.read("gis/scenario.gpkg"))
            with closing(sqlite3.connect(gpkg)) as con:
                blob = con.execute("SELECT geom FROM measures").fetchone()[0]
            self.assertIsNotNone(blob)


if __name__ == "__main__":
    unittest.main()
