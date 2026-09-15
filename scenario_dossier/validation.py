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

'''
This module provides functions to validate a ScenarioDossier directory or ZIP archive.
'''

COMPONENTS = ("overlays", "indicators", "measures", "alerts")


# The _manifest_status function checks the integrity of the manifest file in the ScenarioDossier.
def _manifest_status(root: Path) -> tuple[bool, str]:
    manifest = root / "metadata" / "manifest-sha256.txt"
    if not manifest.is_file():
        return False, "manifest ontbreekt"
    try:
        expected: dict[str, str] = {}
        # Read the manifest file and parse its contents.
        for line in manifest.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            digest, relative = line.split("  ", 1)
            relative_path = PurePosixPath(relative)
            if relative_path.is_absolute() or ".." in relative_path.parts:
                return False, f"ongeldig pad in manifest: {relative}"
            expected[relative] = digest.lower()

        # Compare the expected files from the manifest with the actual files in the directory.
        actual_files = {
            item.relative_to(root).as_posix()
            for item in root.rglob("*")
            if item.is_file() and item != manifest
        }

        # If there are discrepancies between the expected and actual files, return details about missing or extra files.
        if set(expected) != actual_files:
            missing = actual_files - set(expected)
            extra = set(expected) - actual_files
            detail = []
            if missing:
                detail.append(f"niet opgenomen: {', '.join(sorted(missing))}")
            if extra:
                detail.append(f"ontbrekende bestanden: {', '.join(sorted(extra))}")
            return False, "; ".join(detail)

        # If the files match, verify the SHA-256 hashes of each file against the expected hashes from the manifest.
        for relative, digest in expected.items():
            actual = hashlib.sha256((root / relative).read_bytes()).hexdigest()
            if actual != digest:
                return False, f"hash wijkt af voor {relative}"
        # If all files are present and their hashes match, return a success message.
        return True, f"{len(expected)} bestanden zijn ongewijzigd"
    # If any exception occurs during the process, return an error message indicating that the manifest is unreadable.
    except Exception as exc:
        return False, f"manifest niet leesbaar: {exc}"


# The validate_dossier_directory function validates the contents of a ScenarioDossier directory.
def validate_dossier_directory(root: Path, check_manifest: bool = True) -> dict[str, Any]:
    """Controleer een opgebouwd of uitgepakt ScenarioDossier."""
    checks: list[dict[str, Any]] = []

    # Record the result of a validation check.
    def record(name: str, valid: bool, detail: str) -> None:
        checks.append({"check": name, "status": "ok" if valid else "fout", "detail": detail})

    metadata_path = root / "metadata" / "dossier.json"
    metadata: dict[str, Any] = {}
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        required = {"schema", "project", "scenario", "exported_at", "source", "crs", "components"}
        # Check for any required fields that are missing from the metadata.
        missing = sorted(required - metadata.keys())
        # Record the result of the metadata validation, indicating whether all required fields are present or listing any missing fields.
        record("metadata", not missing,
               "verplichte velden aanwezig" if not missing else f"ontbreekt: {', '.join(missing)}")

        passport = metadata.get("record")
        decision = metadata.get("decision")

        # Record the result of the validation for structured dossier and decision data, checking if both 'record' and 'decision' are present and are dictionaries.
        record("dossierpaspoort", isinstance(passport, dict) and isinstance(decision, dict),
               "gestructureerde dossier- en besluitgegevens aanwezig")

    # If any exception occurs while reading or parsing the metadata, record an error indicating that the metadata is unreadable.
    except Exception as exc:
        record("metadata", False, f"niet leesbaar: {exc}")

    # Validate the presence and content of JSON and CSV files for each component in the ScenarioDossier.
    for component in COMPONENTS:
        source_path = root / "bron" / f"{component}.json"
        csv_path = root / "tabellen" / f"{component}.csv"
        try:
            # Read the source JSON file for the component and parse its contents.
            source = json.loads(source_path.read_text(encoding="utf-8"))
            expected = metadata.get("components", {}).get(component)
            # Check if the source is a list and if its length matches the expected count from the metadata (if provided).
            valid = isinstance(source, list) and (expected is None or len(source) == expected)
            # Record the result of the validation for the source JSON file, indicating whether it is valid and providing the number of records found.
            record(f"bron/{component}.json", valid, f"{len(source) if isinstance(source, list) else 0} records")

        # If any exception occurs while reading or parsing the source JSON file, record an error indicating that the file is unreadable.
        except Exception as exc:
            record(f"bron/{component}.json", False, f"niet leesbaar: {exc}")

        # Check if the corresponding CSV file for the component exists and is not empty, and record the result of this validation.
        record(f"tabellen/{component}.csv", csv_path.is_file() and csv_path.stat().st_size > 0, "CSV aanwezig")

        # Validate the presence and content of GeoJSON files for each component in the ScenarioDossier.
        geojson_path = root / "gis" / f"{component}.geojson"
        if geojson_path.exists():
            try:
                collection = json.loads(geojson_path.read_text(encoding="utf-8"))
                valid = collection.get("type") == "FeatureCollection" and isinstance(collection.get("features"), list)
                # Record the result of the validation for the GeoJSON file, indicating whether it is valid and providing the number of features found.
                record(f"gis/{component}.geojson", valid, f"{len(collection.get('features', []))} features")

            # If any exception occurs while reading or parsing the GeoJSON file, record an error indicating that the file is unreadable.
            except Exception as exc:
                record(f"gis/{component}.geojson", False, f"niet leesbaar: {exc}")

    gpkg_path = root / "gis" / "scenario.gpkg"
    # Validate the presence and content of the GeoPackage file in the ScenarioDossier.
    try:
        # Check if the GeoPackage file exists and is not empty, and record the result of this validation.
        with closing(sqlite3.connect(gpkg_path)) as connection:
            # Check if the GeoPackage file is a valid SQLite database and record the result of this validation.
            application_id = connection.execute("PRAGMA application_id").fetchone()[0]
            # Check if the application_id of the GeoPackage matches the expected value (1196437808) and record the result of this validation.
            record("GeoPackage-header", application_id == 1196437808, f"application_id={application_id}")
            # Check if the required tables for each component are present in the GeoPackage and record the result of this validation.
            tables = {row[0] for row in connection.execute("SELECT table_name FROM gpkg_contents")}
            # Record the result of the validation for the presence of component tables in the GeoPackage, indicating whether all required tables are present and listing the actual tables found.
            record("GeoPackage-tabellen", set(COMPONENTS).issubset(tables), ", ".join(sorted(tables)))
            # Validate the number of records in each component table of the GeoPackage against the expected counts from the metadata.
            for component in COMPONENTS:
                count = connection.execute(f'SELECT COUNT(*) FROM "{component}"').fetchone()[0]
                expected = metadata.get("components", {}).get(component)
                # Record the result of the validation for the number of records in each component table, indicating whether it matches the expected count and providing the actual count found.
                record(f"GeoPackage-{component}", expected is None or count == expected, f"{count} records")

    # If any exception occurs while accessing or validating the GeoPackage, record an error indicating that the GeoPackage is unreadable.
    except Exception as exc:
        record("GeoPackage", False, f"niet leesbaar: {exc}")

    # Validate the presence of the standalone HTML report in the ScenarioDossier.
    report_path = root / "rapport" / "dossierrapport.html"
    record(
        "dossierrapport",
        report_path.is_file() and report_path.stat().st_size > 0,
        "zelfstandig HTML-rapport aanwezig",
    )

    # If the check_manifest flag is set to True, validate the integrity of the manifest file in the ScenarioDossier.
    if check_manifest:
        valid, detail = _manifest_status(root)
        record("SHA-256-manifest", valid, detail)

    # Determine the overall validation status based on the individual checks and return a summary report.
    failures = [item for item in checks if item["status"] == "fout"]
    # Return a dictionary containing the validation report, including the schema version, timestamp, overall status, counts of successful and failed checks, and details of each check.
    return {
        "schema": "nl.provincie-utrecht.scenariodossier.validation/1.0",
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "status": "goedgekeurd" if not failures else "afgekeurd",
        "checks_ok": len(checks) - len(failures),
        "checks_failed": len(failures),
        "checks": checks,
    }

# The validate_archive function validates the contents of a ZIP archive containing a ScenarioDossier.
def validate_archive(archive: Path) -> dict[str, Any]:
    """Pak een ZIP veilig tijdelijk uit en valideer inhoud plus manifest."""
    if not zipfile.is_zipfile(archive):
        raise ValueError("Het bestand is geen geldig ZIP-dossier.")
    with tempfile.TemporaryDirectory(prefix="scenario-dossier-check-") as temp:
        root = Path(temp)
        # Safely extract the contents of the ZIP archive to a temporary directory, while performing security checks on the file paths and sizes.
        with zipfile.ZipFile(archive) as package:
            members = package.infolist()
            # Check if the number of files in the ZIP archive exceeds the limit of 5000 files, and raise an error if it does.
            if len(members) > 5000:
                raise ValueError("Het ZIP-dossier bevat te veel bestanden.")
            if sum(item.file_size for item in members) > 1_000_000_000:
                raise ValueError("De uitgepakte dossierinhoud is te groot.")
            for item in members:
                member = PurePosixPath(item.filename)
                # Check if the file path in the ZIP archive is absolute or contains ".." (parent directory references), and raise an error if it does, to prevent directory traversal attacks.
                if member.is_absolute() or ".." in member.parts:
                    raise ValueError("Het ZIP-dossier bevat een onveilig bestandspad.")

            # Safely extract all files from the ZIP archive to the temporary directory.
            package.extractall(root)
        # Validate the extracted contents of the ScenarioDossier directory and return a summary report, including additional metadata from the dossier.json file if available.
        report = validate_dossier_directory(root, check_manifest=True)
        try:
            metadata = json.loads((root / "metadata" / "dossier.json").read_text(encoding="utf-8"))
        except Exception:
            metadata = {}

        # Return a dictionary containing the validation report, including the filename of the ZIP archive, its size, and additional metadata from the dossier.json file if available.
        return report | {
            "filename": archive.name,
            "archive_size": archive.stat().st_size,
            "project": metadata.get("project", ""),
            "scenario": metadata.get("scenario", ""),
            "exported_at": metadata.get("exported_at", ""),
            "components": metadata.get("components", {}),
        }

# The main function serves as the entry point for the CLI of the validation script.
def main() -> int:
    parser = argparse.ArgumentParser(description="Valideer een uitgepakt ScenarioDossier")
    parser.add_argument("dossier", type=Path, help="Pad naar de uitgepakte dossiermap")
    args = parser.parse_args()
    report = validate_dossier_directory(args.dossier)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "goedgekeurd" else 1

# If the script is run as the main program, execute the main function and exit with its return code.
if __name__ == "__main__":
    raise SystemExit(main())
