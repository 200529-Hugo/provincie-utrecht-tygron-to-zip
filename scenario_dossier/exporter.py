from __future__ import annotations

import csv
import hashlib
import html
import io
import json
import re
import shutil
import sqlite3
import struct
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .validation import validate_dossier_directory

COMPONENTS = ("overlays", "indicators", "measures", "alerts")

DOSSIER_FIELDS = (
    "reference",
    "owner",
    "author",
    "decision_date",
    "decision_status",
    "alternatives",
    "classification",
    "retention_period",
)


def slug(value: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip()).strip("-").lower()
    return clean[:60] or "scenario"


def load_demo() -> dict[str, Any]:
    path = Path(__file__).parent.parent / "data" / "demo.json"
    return json.loads(path.read_text(encoding="utf-8"))


def feature(item: dict[str, Any]) -> dict[str, Any]:
    if item.get("type") == "Feature":
        return item
    geometry = item.get("geometry")
    props = {k: v for k, v in item.items() if k != "geometry"}
    return {"type": "Feature", "geometry": geometry, "properties": props}


def properties(item: dict[str, Any]) -> dict[str, Any]:
    return item.get("properties", {}) if item.get("type") == "Feature" else {k: v for k, v in item.items() if k != "geometry"}


def geometry(item: dict[str, Any]) -> dict[str, Any] | None:
    return item.get("geometry") if item.get("type") == "Feature" else item.get("geometry")


def _simple(value: Any) -> str | int | float | None:
    if value is None or isinstance(value, (str, int, float)):
        return value
    if isinstance(value, bool):
        return int(value)
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _wkb(geom: dict[str, Any]) -> bytes:
    endian = b"\x01"
    kind = geom["type"]
    coords = geom.get("coordinates", [])
    if kind == "Point":
        return endian + struct.pack("<I2d", 1, coords[0], coords[1])
    if kind == "LineString":
        return endian + struct.pack("<II", 2, len(coords)) + b"".join(struct.pack("<2d", *p[:2]) for p in coords)
    if kind == "Polygon":
        rings = b""
        for ring in coords:
            rings += struct.pack("<I", len(ring)) + b"".join(struct.pack("<2d", *p[:2]) for p in ring)
        return endian + struct.pack("<II", 3, len(coords)) + rings
    if kind == "MultiPoint":
        return endian + struct.pack("<II", 4, len(coords)) + b"".join(_wkb({"type": "Point", "coordinates": p}) for p in coords)
    if kind == "MultiLineString":
        return endian + struct.pack("<II", 5, len(coords)) + b"".join(_wkb({"type": "LineString", "coordinates": p}) for p in coords)
    if kind == "MultiPolygon":
        return endian + struct.pack("<II", 6, len(coords)) + b"".join(_wkb({"type": "Polygon", "coordinates": p}) for p in coords)
    if kind == "GeometryCollection":
        geometries = geom.get("geometries", [])
        return endian + struct.pack("<II", 7, len(geometries)) + b"".join(_wkb(item) for item in geometries)
    raise ValueError(f"Niet-ondersteund geometrietype: {kind}")


def _gpkg_geometry(geom: dict[str, Any]) -> bytes:
    return b"GP" + bytes((0, 1)) + struct.pack("<i", 4326) + _wkb(geom)


def create_geopackage(path: Path, data: dict[str, list[dict[str, Any]]]) -> None:
    con = sqlite3.connect(path)
    con.executescript("""
        PRAGMA application_id=1196437808;
        PRAGMA user_version=10300;
        CREATE TABLE gpkg_spatial_ref_sys (srs_name TEXT NOT NULL, srs_id INTEGER NOT NULL PRIMARY KEY, organization TEXT NOT NULL, organization_coordsys_id INTEGER NOT NULL, definition TEXT NOT NULL, description TEXT);
        CREATE TABLE gpkg_contents (table_name TEXT NOT NULL PRIMARY KEY, data_type TEXT NOT NULL, identifier TEXT UNIQUE, description TEXT DEFAULT '', last_change DATETIME NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')), min_x DOUBLE, min_y DOUBLE, max_x DOUBLE, max_y DOUBLE, srs_id INTEGER);
        CREATE TABLE gpkg_geometry_columns (table_name TEXT NOT NULL, column_name TEXT NOT NULL, geometry_type_name TEXT NOT NULL, srs_id INTEGER NOT NULL, z TINYINT NOT NULL, m TINYINT NOT NULL, PRIMARY KEY (table_name, column_name));
    """)
    con.executemany("INSERT INTO gpkg_spatial_ref_sys VALUES (?,?,?,?,?,?)", [
        ("Undefined Cartesian", -1, "NONE", -1, "undefined", None),
        ("Undefined Geographic", 0, "NONE", 0, "undefined", None),
        ("WGS 84", 4326, "EPSG", 4326, 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]', "longitude/latitude coordinates in decimal degrees on WGS 84"),
    ])
    for name in COMPONENTS:
        items = data.get(name, [])
        spatial = any(geometry(i) for i in items)
        columns = ["fid INTEGER PRIMARY KEY AUTOINCREMENT", "item_id TEXT", "name TEXT", "status TEXT", "value TEXT", "unit TEXT", "description TEXT", "source_json TEXT"]
        if spatial:
            columns.append("geom BLOB")
        con.execute(f'CREATE TABLE "{name}" ({", ".join(columns)})')
        con.execute("INSERT INTO gpkg_contents(table_name,data_type,identifier,description,srs_id) VALUES (?,?,?,?,?)", (name, "features" if spatial else "attributes", name, f"Tygron {name}", 4326 if spatial else None))
        if spatial:
            con.execute("INSERT INTO gpkg_geometry_columns VALUES (?,?,?,?,?,?)", (name, "geom", "GEOMETRY", 4326, 0, 0))
        for item in items:
            p = properties(item)
            vals = (str(p.get("id", "")), str(p.get("name", p.get("shortName", ""))), str(p.get("status", p.get("severity", ""))), str(p.get("value", p.get("currentValue", ""))), str(p.get("unit", "")), str(p.get("description", p.get("warnings", ""))), json.dumps(p, ensure_ascii=False, separators=(",", ":")))
            if spatial:
                blob = _gpkg_geometry(geometry(item)) if geometry(item) else None
                con.execute(f'INSERT INTO "{name}"(item_id,name,status,value,unit,description,source_json,geom) VALUES (?,?,?,?,?,?,?,?)', vals + (blob,))
            else:
                con.execute(f'INSERT INTO "{name}"(item_id,name,status,value,unit,description,source_json) VALUES (?,?,?,?,?,?,?)', vals)
    con.commit()
    con.close()


def _write_csv(path: Path, items: Iterable[dict[str, Any]]) -> None:
    rows = [properties(i) for i in items]
    keys = sorted({k for row in rows for k in row})
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys or ["geen_records"], extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: _simple(v) for k, v in row.items()})


def _write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def _dossier_fields(values: dict[str, Any] | None) -> dict[str, str]:
    source = values if isinstance(values, dict) else {}
    return {
        key: str(source.get(key, "")).strip()[:2000]
        for key in DOSSIER_FIELDS
    }


def _report_table(items: list[dict[str, Any]], empty: str) -> str:
    if not items:
        return f'<p class="empty">{html.escape(empty)}</p>'
    rows = []
    for item in items:
        props = properties(item)
        name = props.get("name", props.get("shortName", props.get("id", "Onbenoemd")))
        value = props.get("value", props.get("currentValue", props.get("status", "")))
        unit = props.get("unit", "")
        description = props.get("description", props.get("warnings", ""))
        rows.append(
            "<tr>"
            f"<th>{html.escape(str(name))}</th>"
            f"<td>{html.escape(str(value))} {html.escape(str(unit))}</td>"
            f"<td>{html.escape(str(description))}</td>"
            "</tr>"
        )
    return (
        "<div class=\"table-wrap\"><table><thead><tr><th>Naam</th><th>Waarde of status</th>"
        "<th>Toelichting</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></div>"
    )


def _report_html(metadata: dict[str, Any], data: dict[str, list[dict[str, Any]]], warnings: list[str]) -> str:
    record = metadata["record"]
    decision = metadata["decision"]
    components = metadata["components"]

    def value(item: Any, fallback: str = "Niet vastgelegd") -> str:
        text = str(item or "").strip()
        return html.escape(text or fallback)

    warning_html = "".join(f"<li>{html.escape(item)}</li>" for item in warnings)
    if not warning_html:
        warning_html = "<li>Geen technische waarschuwingen.</li>"
    component_labels = {
        "overlays": "overlays",
        "indicators": "indicatoren",
        "measures": "maatregelen",
        "alerts": "alerts",
    }
    counts = "".join(
        f'<div class="metric"><strong>{count}</strong><span>{component_labels.get(name, html.escape(name))}</span></div>'
        for name, count in components.items()
    )
    return f"""<!doctype html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Dossierrapport · {value(metadata['project'])} · {value(metadata['scenario'])}</title>
<style>
:root{{--red:#ec0000;--ink:#231b1b;--muted:#6c6868;--line:#dedbd9;--soft:#f4f2f1}}
*{{box-sizing:border-box}}body{{margin:0;color:var(--ink);font:15px/1.55 Arial,sans-serif;background:var(--soft)}}
header{{padding:34px max(6vw,28px);color:#fff;background:var(--ink);border-top:10px solid var(--red)}}
header small{{display:block;margin-bottom:8px;text-transform:uppercase;letter-spacing:.12em}}header h1{{max-width:850px;margin:0;font-size:38px;line-height:1.1}}
main{{max-width:1100px;margin:auto;padding:34px 28px 70px}}section{{margin-bottom:24px;padding:26px;background:#fff;border-top:5px solid var(--red)}}
h2{{margin:0 0 18px;font-size:22px}}dl{{display:grid;grid-template-columns:220px 1fr;margin:0}}dt,dd{{margin:0;padding:9px 0;border-bottom:1px solid var(--line)}}dt{{font-weight:700}}dd{{overflow-wrap:anywhere}}
.metrics{{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line);border:1px solid var(--line)}}.metric{{padding:18px;background:#fff}}.metric strong,.metric span{{display:block}}.metric strong{{color:var(--red);font-size:30px}}.metric span{{color:var(--muted)}}
.table-wrap{{overflow:auto}}table{{width:100%;border-collapse:collapse}}th,td{{padding:10px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}}thead th{{background:var(--ink);color:#fff}}tbody th{{width:25%}}.empty{{color:var(--muted)}}
.notice{{padding:16px;background:#fde9eb;border-left:6px solid var(--red)}}code{{font-size:13px}}footer{{color:var(--muted);font-size:13px}}@media print{{body{{background:#fff}}section{{break-inside:avoid}}}}
@media(max-width:700px){{dl{{grid-template-columns:1fr}}dt{{border-bottom:0;padding-bottom:0}}.metrics{{grid-template-columns:1fr 1fr}}header h1{{font-size:30px}}}}
</style>
</head>
<body>
<header><small>Provincie Utrecht · ScenarioDossier</small><h1>{value(metadata['project'])}<br>{value(metadata['scenario'])}</h1></header>
<main>
<section><h2>Dossierpaspoort</h2><dl>
<dt>Referentie</dt><dd>{value(record['reference'])}</dd><dt>Dossiereigenaar</dt><dd>{value(record['owner'])}</dd>
<dt>Opsteller</dt><dd>{value(record['author'])}</dd><dt>Classificatie</dt><dd>{value(record['classification'])}</dd>
<dt>Bewaartermijn</dt><dd>{value(record['retention_period'])}</dd><dt>Exportmoment</dt><dd>{value(metadata['exported_at'])}</dd>
<dt>Bron</dt><dd>{value(metadata['source'])}</dd><dt>Coördinatenstelsel</dt><dd>{value(metadata['crs'])}</dd>
</dl></section>
<section><h2>Besluit en afweging</h2><dl>
<dt>Besluitdatum</dt><dd>{value(decision['date'])}</dd><dt>Status</dt><dd>{value(decision['status'])}</dd>
<dt>Gekozen scenario</dt><dd>{value(decision['selected_scenario'])}</dd><dt>Andere alternatieven</dt><dd>{value(decision['alternatives'])}</dd>
<dt>Onderbouwing</dt><dd>{value(decision['rationale'])}</dd>
</dl></section>
<section><h2>Opgenomen onderdelen</h2><div class="metrics">{counts}</div></section>
<section><h2>Indicatoren</h2>{_report_table(data['indicators'], 'Geen indicatoren opgenomen.')}</section>
<section><h2>Maatregelen</h2>{_report_table(data['measures'], 'Geen maatregelen opgenomen.')}</section>
<section><h2>Alerts</h2>{_report_table(data['alerts'], 'Geen alerts opgenomen.')}</section>
<section><h2>Technische overdracht</h2><p class="notice">Open <code>../gis/scenario.gpkg</code> in QGIS of ArcGIS Pro. Gebruik de bronbestanden in dit dossier alleen-lezen en voer analyses uit op een werkkopie.</p><h3>Exportmeldingen</h3><ul>{warning_html}</ul></section>
<footer>Dit rapport is automatisch gegenereerd door {value(metadata['software'])}. Controleer <code>../metadata/manifest-sha256.txt</code> om de integriteit van het volledige dossier vast te stellen.</footer>
</main>
</body>
</html>"""


def build_archive(output_dir: Path, project: str, scenario: str, data: dict[str, list[dict[str, Any]]], notes: str = "", source: str = "demo", warnings: list[str] | None = None, raster_fetcher=None, dossier_fields: dict[str, Any] | None = None) -> tuple[Path, dict[str, Any]]:
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    archive_name = f"{slug(project)}_{slug(scenario)}_{stamp}.zip"
    output_dir.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="scenario-dossier-"))
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
            "crs": "EPSG:4326",
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
            spatial = [feature(i) for i in items if geometry(i)]
            if spatial:
                _write_json(work / "gis" / f"{name}.geojson", {"type": "FeatureCollection", "name": name, "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}}, "features": spatial})
        create_geopackage(work / "gis" / "scenario.gpkg", selected)

        if raster_fetcher:
            for overlay in selected["overlays"]:
                p = properties(overlay)
                if p.get("id") is None:
                    continue
                try:
                    content = raster_fetcher(int(p["id"]))
                    (work / "rasters" / f"overlay_{p['id']}_{slug(str(p.get('name', 'overlay')))}.tif").write_bytes(content)
                except Exception as exc:
                    export_warnings.append(f"GeoTIFF overlay {p['id']} niet opgehaald: {exc}")

        _write_json(work / "metadata" / "exportlog.json", {"status": "completed", "warnings": export_warnings})
        (work / "rapport" / "dossierrapport.html").write_text(
            _report_html(metadata, selected, export_warnings),
            encoding="utf-8",
        )
        (work / "README.txt").write_text(
            f"SCENARIODOSSIER\n\nProject: {project}\nScenario: {scenario}\nExportmoment (UTC): {now.isoformat()}\n\nOpen rapport/dossierrapport.html voor een leesbaar overzicht. Open gis/scenario.gpkg in QGIS of ArcGIS Pro. Zie de projectdocumentatie voor de volledige werkinstructie. Controleer metadata/manifest-sha256.txt om bestandsintegriteit vast te stellen.\n",
            encoding="utf-8",
        )
        validation = validate_dossier_directory(work, check_manifest=False)
        _write_json(work / "metadata" / "validatierapport.json", validation)
        if validation["status"] != "goedgekeurd":
            raise ValueError("Het dossier is niet door de automatische validatie gekomen.")
        manifest_lines = []
        for file in sorted(p for p in work.rglob("*") if p.is_file() and p.name != "manifest-sha256.txt"):
            manifest_lines.append(f"{hashlib.sha256(file.read_bytes()).hexdigest()}  {file.relative_to(work).as_posix()}")
        (work / "metadata" / "manifest-sha256.txt").write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
        archive = output_dir / archive_name
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in sorted(p for p in work.rglob("*") if p.is_file()):
                zf.write(file, file.relative_to(work))
        return archive, metadata | {
            "warnings": export_warnings,
            "validation": validation["status"],
            "size": archive.stat().st_size,
        }
    finally:
        shutil.rmtree(work, ignore_errors=True)
