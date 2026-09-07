from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import tempfile
import zipfile
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any

COMPONENTS = ("overlays", "indicators", "measures", "alerts")


def _manifest_status(root: Path) -> tuple[bool, str]:
    manifest = root / "metadata" / "manifest-sha256.txt"
    if not manifest.is_file():
        return False, "manifest ontbreekt"
    try:
        expected: dict[str, str] = {}
        for line in manifest.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            digest, relative = line.split("  ", 1)
            relative_path = PurePosixPath(relative)
            if relative_path.is_absolute() or ".." in relative_path.parts:
                return False, f"ongeldig pad in manifest: {relative}"
            expected[relative] = digest.lower()
        actual_files = {
            item.relative_to(root).as_posix()
            for item in root.rglob("*")
            if item.is_file() and item != manifest
        }
        if set(expected) != actual_files:
            missing = actual_files - set(expected)
            extra = set(expected) - actual_files
            detail = []
            if missing:
                detail.append(f"niet opgenomen: {', '.join(sorted(missing))}")
            if extra:
                detail.append(f"ontbrekende bestanden: {', '.join(sorted(extra))}")
            return False, "; ".join(detail)
        for relative, digest in expected.items():
            actual = hashlib.sha256((root / relative).read_bytes()).hexdigest()
            if actual != digest:
                return False, f"hash wijkt af voor {relative}"
        return True, f"{len(expected)} bestanden zijn ongewijzigd"
    except Exception as exc:
        return False, f"manifest niet leesbaar: {exc}"


def validate_dossier_directory(root: Path, check_manifest: bool = True) -> dict[str, Any]:
    """Controleer een opgebouwd of uitgepakt ScenarioDossier."""
    checks: list[dict[str, Any]] = []

    def record(name: str, valid: bool, detail: str) -> None:
        checks.append({"check": name, "status": "ok" if valid else "fout", "detail": detail})

    metadata_path = root / "metadata" / "dossier.json"
    metadata: dict[str, Any] = {}
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        required = {"schema", "project", "scenario", "exported_at", "source", "crs", "components"}
        missing = sorted(required - metadata.keys())
        record("metadata", not missing, "verplichte velden aanwezig" if not missing else f"ontbreekt: {', '.join(missing)}")
        passport = metadata.get("record")
        decision = metadata.get("decision")
        record("dossierpaspoort", isinstance(passport, dict) and isinstance(decision, dict), "gestructureerde dossier- en besluitgegevens aanwezig")
    except Exception as exc:
        record("metadata", False, f"niet leesbaar: {exc}")

    for component in COMPONENTS:
        source_path = root / "bron" / f"{component}.json"
        csv_path = root / "tabellen" / f"{component}.csv"
        try:
            source = json.loads(source_path.read_text(encoding="utf-8"))
            expected = metadata.get("components", {}).get(component)
            valid = isinstance(source, list) and (expected is None or len(source) == expected)
            record(f"bron/{component}.json", valid, f"{len(source) if isinstance(source, list) else 0} records")
        except Exception as exc:
            record(f"bron/{component}.json", False, f"niet leesbaar: {exc}")
        record(f"tabellen/{component}.csv", csv_path.is_file() and csv_path.stat().st_size > 0, "CSV aanwezig")

        geojson_path = root / "gis" / f"{component}.geojson"
        if geojson_path.exists():
            try:
                collection = json.loads(geojson_path.read_text(encoding="utf-8"))
                valid = collection.get("type") == "FeatureCollection" and isinstance(collection.get("features"), list)
                record(f"gis/{component}.geojson", valid, f"{len(collection.get('features', []))} features")
            except Exception as exc:
                record(f"gis/{component}.geojson", False, f"niet leesbaar: {exc}")

    gpkg_path = root / "gis" / "scenario.gpkg"
    try:
        with closing(sqlite3.connect(gpkg_path)) as connection:
            application_id = connection.execute("PRAGMA application_id").fetchone()[0]
            record("GeoPackage-header", application_id == 1196437808, f"application_id={application_id}")
            tables = {row[0] for row in connection.execute("SELECT table_name FROM gpkg_contents")}
            record("GeoPackage-tabellen", set(COMPONENTS).issubset(tables), ", ".join(sorted(tables)))
            for component in COMPONENTS:
                count = connection.execute(f'SELECT COUNT(*) FROM "{component}"').fetchone()[0]
                expected = metadata.get("components", {}).get(component)
                record(f"GeoPackage-{component}", expected is None or count == expected, f"{count} records")
    except Exception as exc:
        record("GeoPackage", False, f"niet leesbaar: {exc}")

    report_path = root / "rapport" / "dossierrapport.html"
    record(
        "dossierrapport",
        report_path.is_file() and report_path.stat().st_size > 0,
        "zelfstandig HTML-rapport aanwezig",
    )

    if check_manifest:
        valid, detail = _manifest_status(root)
        record("SHA-256-manifest", valid, detail)

    failures = [item for item in checks if item["status"] == "fout"]
    return {
        "schema": "nl.provincie-utrecht.scenariodossier.validation/1.0",
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "status": "goedgekeurd" if not failures else "afgekeurd",
        "checks_ok": len(checks) - len(failures),
        "checks_failed": len(failures),
        "checks": checks,
    }


def validate_archive(archive: Path) -> dict[str, Any]:
    """Pak een ZIP veilig tijdelijk uit en valideer inhoud plus manifest."""
    if not zipfile.is_zipfile(archive):
        raise ValueError("Het bestand is geen geldig ZIP-dossier.")
    with tempfile.TemporaryDirectory(prefix="scenario-dossier-check-") as temp:
        root = Path(temp)
        with zipfile.ZipFile(archive) as package:
            members = package.infolist()
            if len(members) > 5000:
                raise ValueError("Het ZIP-dossier bevat te veel bestanden.")
            if sum(item.file_size for item in members) > 1_000_000_000:
                raise ValueError("De uitgepakte dossierinhoud is te groot.")
            for item in members:
                member = PurePosixPath(item.filename)
                if member.is_absolute() or ".." in member.parts:
                    raise ValueError("Het ZIP-dossier bevat een onveilig bestandspad.")
            package.extractall(root)
        report = validate_dossier_directory(root, check_manifest=True)
        try:
            metadata = json.loads((root / "metadata" / "dossier.json").read_text(encoding="utf-8"))
        except Exception:
            metadata = {}
        return report | {
            "filename": archive.name,
            "archive_size": archive.stat().st_size,
            "project": metadata.get("project", ""),
            "scenario": metadata.get("scenario", ""),
            "exported_at": metadata.get("exported_at", ""),
            "components": metadata.get("components", {}),
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Valideer een uitgepakt ScenarioDossier")
    parser.add_argument("dossier", type=Path, help="Pad naar de uitgepakte dossiermap")
    args = parser.parse_args()
    report = validate_dossier_directory(args.dossier)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "goedgekeurd" else 1


if __name__ == "__main__":
    raise SystemExit(main())
