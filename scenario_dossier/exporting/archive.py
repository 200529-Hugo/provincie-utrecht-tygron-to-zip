"""De volgorde waarin dossierbestanden worden gemaakt en gecontroleerd."""

from __future__ import annotations

import hashlib
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..coordinates import EXPORT_CRS, WGS84, has_wgs84_coordinates
from ..validation import validate_dossier_directory
from .data import COMPONENTS, feature, geometry, properties, slug, _dossier_fields, _write_csv, _write_json
from .geopackage import create_geopackage
from .report import _report_html


def build_archive(
        output_dir: Path,
        project: str,
        scenario: str,
        data: dict[str, list[dict[str, Any]]],
        notes: str = "",
        source: str = "demo",
        warnings: list[str] | None = None,
        raster_fetcher=None,
        dossier_fields: dict[str, Any] | None = None,
        *,
        export_crs: str = WGS84,
        source_crs: str | None = None,
) -> tuple[Path, dict[str, Any]]:
    """Bouw het dossier, controleer het en verpak alle bestanden in een ZIP."""
    if export_crs not in EXPORT_CRS:
        raise ValueError("Kies WGS 84 of RD New als export-CRS.")
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%S.%fZ")
    archive_name = f"{slug(project)}_{slug(scenario)}_{stamp}_epsg{EXPORT_CRS[export_crs]}.zip"
    output_dir.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix=".scenario-dossier-", dir=output_dir))
    try:

        for folder in ("metadata", "bron", "gis", "tabellen", "rasters", "rapport"):
            (work / folder).mkdir()
        selected = {name: list(data.get(name, [])) for name in COMPONENTS}
        fields = _dossier_fields(dossier_fields)
        metadata = {
            "schema": "nl.provincie-utrecht.scenariodossier/1.0",
            "project": project,
            "scenario": scenario,
            "exported_at": now.isoformat(),
            "source": source,
            "source_crs": source_crs,
            "crs": export_crs,
            "geojson_crs": WGS84,
            "components": {name: len(selected[name]) for name in COMPONENTS},
            "notes": notes,
            "record": {
                "reference": fields["reference"],
                "owner": fields["owner"],
                "author": fields["author"],
                "classification": fields["classification"],
                "retention_period": fields["retention_period"],
            },
            "decision": {
                "date": fields["decision_date"],
                "status": fields["decision_status"],
                "selected_scenario": scenario,
                "alternatives": fields["alternatives"],
                "rationale": notes,
            },
            "software": "ScenarioDossier 1.0.0",
            "token_archived": False,
        }


        _write_json(work / "metadata" / "dossier.json", metadata)
        export_warnings = list(warnings or [])
        for name, items in selected.items():
            _write_json(work / "bron" / f"{name}.json", items)
            _write_csv(work / "tabellen" / f"{name}.csv", items)
            spatial = []
            for item in items:
                if geom := geometry(item):
                    if not has_wgs84_coordinates(geom):
                        raise ValueError("Het scenario bevat ongeldige WGS 84-coördinaten.")
                    spatial.append({key: value for key, value in feature(item).items() if key != "crs"})
            if spatial:
                _write_json(work / "gis" / f"{name}.geojson", {"type": "FeatureCollection", "name": name,
                                                               "features": spatial})
        create_geopackage(work / "gis" / "scenario.gpkg", selected, export_crs)


        if raster_fetcher:
            for overlay in selected["overlays"]:
                p = properties(overlay)
                if p.get("id") is None:
                    continue
                try:
                    content = raster_fetcher(int(p["id"]))
                    (work / "rasters" / f"overlay_{p['id']}_{slug(str(p.get('name', 'overlay')))}.tif").write_bytes(
                        content)
                except Exception as exc:
                    export_warnings.append(f"GeoTIFF overlay {p['id']} niet opgehaald: {exc}")


        _write_json(
            work / "metadata" / "exportlog.json",
            {"status": "completed", "warnings": export_warnings}
        )
        (work / "rapport" / "dossierrapport.html").write_text(
            _report_html(metadata, selected, export_warnings),
            encoding="utf-8",
        )
        (work / "README.txt").write_text(
            f"SCENARIODOSSIER\n\nProject: {project}\nScenario: {scenario}\nExportmoment (UTC): {now.isoformat()}\n"
            f"Bron-CRS: {source_crs or 'onbekend'}\nGeoPackage: {export_crs}\n"
            f"GeoJSON en vectorgeometrie in bron/: {WGS84} (lengtegraad, breedtegraad)\n"
            "GeoTIFF: coördinatenstelsel van het ontvangen raster.\n\n"
            "Open rapport/dossierrapport.html voor een leesbaar overzicht. "
            "Open gis/scenario.gpkg in QGIS of ArcGIS Pro. Zie de projectdocumentatie voor de volledige "
            "werkinstructie. Controleer metadata/manifest-sha256.txt om bestandsintegriteit vast te stellen.\n",
            encoding="utf-8",
        )

        validation = validate_dossier_directory(work, check_manifest=False)
        _write_json(work / "metadata" / "validatierapport.json", validation)
        if validation["status"] != "goedgekeurd":
            raise ValueError("Het dossier is niet door de automatische validatie gekomen.")
        manifest_lines = []
        for file in sorted(p for p in work.rglob("*") if p.is_file() and p.name != "manifest-sha256.txt"):
            manifest_lines.append(
                f"{hashlib.sha256(file.read_bytes()).hexdigest()}  {file.relative_to(work).as_posix()}")
        (work / "metadata" / "manifest-sha256.txt").write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
        archive = output_dir / archive_name
        files = sorted(p for p in work.rglob("*") if p.is_file())
        staged_archive = work / archive_name
        with zipfile.ZipFile(staged_archive, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in files:
                zf.write(file, file.relative_to(work))
        staged_archive.replace(archive)
        return archive, metadata | {
            "warnings": export_warnings,
            "validation": validation["status"],
            "size": archive.stat().st_size,
        }
    finally:
        shutil.rmtree(work, ignore_errors=True)
