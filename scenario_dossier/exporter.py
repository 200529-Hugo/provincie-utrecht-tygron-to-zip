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

'''
This module provides functions to export a scenario dossier into a structured directory and archive format. It includes functionality to create GeoPackage files, generate CSV and JSON representations of the data, and produce an HTML report summarizing the dossier contents. The main function `build_archive` orchestrates the export process, ensuring that all components are correctly formatted and validated before creating a ZIP archive of the dossier.
'''

# Components of the scenario dossier that can be exported
COMPONENTS = ("overlays", "indicators", "measures", "alerts")

# Fields that are expected in the dossier metadata for proper documentation and decision-making
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


# Regular expression pattern to identify invalid characters for slugs
def slug(value: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip()).strip("-").lower()
    return clean[:60] or "scenario"


# Function to load a demo dataset from a JSON file located in the data directory
def load_demo() -> dict[str, Any]:
    path = Path(__file__).parent.parent / "data" / "demo.json"
    return json.loads(path.read_text(encoding="utf-8"))


# Function to ensure that an item is represented as a GeoJSON Feature. If the item is already a Feature, it is returned as-is; otherwise, it is wrapped in a Feature structure with its geometry and properties.
def feature(item: dict[str, Any]) -> dict[str, Any]:
    if item.get("type") == "Feature":
        return item
    geometry = item.get("geometry")
    # If the item is not a Feature, we construct a new Feature dictionary with the geometry and properties extracted from the item. The properties are filtered to exclude the geometry key.
    props = {k: v for k, v in item.items() if k != "geometry"}
    return {"type": "Feature", "geometry": geometry, "properties": props}


# Function to extract the properties of an item. If the item is a GeoJSON Feature, its properties are returned; otherwise, all key-value pairs except for the geometry are returned as properties.
def properties(item: dict[str, Any]) -> dict[str, Any]:
    return item.get("properties", {}) \
        if item.get("type") == "Feature" \
        else {
        k: v for k, v in item.items()
        if k != "geometry"
    }


# Function to extract the geometry of an item. If the item is a GeoJSON Feature, its geometry is returned; otherwise, the geometry key is accessed directly from the item.
def geometry(item: dict[str, Any]) -> dict[str, Any] | None:
    return item.get("geometry") if item.get("type") == "Feature" else item.get("geometry")


# Simple function to convert a value into a string, integer, float, or None. If the value is a boolean, it is converted to an integer (1 for True, 0 for False). For other types, the value is serialized to a JSON string.
def _simple(value: Any) -> str | int | float | None:
    if value is None or isinstance(value, (str, int, float)):
        return value
    if isinstance(value, bool):
        return int(value)
    # For other types, we serialize the value to a JSON string with non-ASCII characters preserved and compact separators.
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


# Function to convert a GeoJSON geometry into Well-Known Binary (WKB) format. The function handles different geometry types, including Point, LineString, Polygon, MultiPoint, MultiLineString, MultiPolygon, and GeometryCollection. It constructs the WKB representation based on the geometry type and its coordinates.
def _wkb(geom: dict[str, Any]) -> bytes:
    endian = b"\x01"
    kind = geom["type"]
    coords = geom.get("coordinates", [])
    # The function uses the struct module to pack the geometry data into binary format according to the WKB specification. The endian byte indicates the byte order (little-endian in this case), and the geometry type is represented by an integer code. The coordinates are packed as double-precision floating-point numbers.
    if kind == "Point":
        return endian + struct.pack("<I2d", 1, coords[0], coords[1])

    # The function handles different geometry types by checking the "type" field of the geometry dictionary. For each type, it constructs the appropriate WKB representation, including the number of points or rings and their coordinates.
    if kind == "LineString":
        return endian + struct.pack("<II", 2, len(coords)) + b"".join(struct.pack("<2d", *p[:2]) for p in coords)

    # For Polygon geometries, the function iterates over the rings (outer and inner) and packs their coordinates into the WKB format. The number of rings is included in the WKB representation, followed by the coordinates of each ring.
    if kind == "Polygon":
        rings = b""
        for ring in coords:
            rings += struct.pack("<I", len(ring)) + b"".join(struct.pack("<2d", *p[:2]) for p in ring)
        return endian + struct.pack("<II", 3, len(coords)) + rings

    # The function also handles MultiPoint, MultiLineString, MultiPolygon, and GeometryCollection geometries by recursively calling itself for each individual geometry in the collection. The number of geometries is included in the WKB representation, followed by the WKB representations of each geometry.
    if kind == "MultiPoint":
        return endian + struct.pack("<II", 4, len(coords)) + b"".join(
            _wkb({"type": "Point", "coordinates": p}) for p in coords
        )

    # For MultiLineString geometries, the function constructs the WKB representation by iterating over each LineString in the collection and packing their coordinates into the WKB format.
    if kind == "MultiLineString":
        return endian + struct.pack("<II", 5, len(coords)) + b"".join(
            _wkb({"type": "LineString", "coordinates": p}) for p in coords
        )

    # For MultiPolygon geometries, the function constructs the WKB representation by iterating over each Polygon in the collection and packing their coordinates into the WKB format.
    if kind == "MultiPolygon":
        return endian + struct.pack("<II", 6, len(coords)) + b"".join(
            _wkb({"type": "Polygon", "coordinates": p}) for p in coords
        )

    # For GeometryCollection geometries, the function constructs the WKB representation by iterating over each geometry in the collection and packing their WKB representations into the final output.
    if kind == "GeometryCollection":
        geometries = geom.get("geometries", [])
        return endian + struct.pack("<II", 7, len(geometries)) + b"".join(_wkb(item) for item in geometries)

    # If the geometry type is not recognized, the function raises a ValueError indicating that the geometry type is unsupported.
    raise ValueError(f"Niet-ondersteund geometrietype: {kind}")


# Function to create a GeoPackage geometry blob from a GeoJSON geometry. The function constructs the GeoPackage binary representation by prepending the "GP" signature, version number, and spatial reference system identifier (SRID) to the WKB representation of the geometry. The SRID is set to 4326 for WGS 84 coordinates.
def _gpkg_geometry(geom: dict[str, Any]) -> bytes:
    return b"GP" + bytes((0, 1)) + struct.pack("<i", 4326) + _wkb(geom)


# Function to create a GeoPackage file at the specified path, containing tables for each component of the scenario dossier. The function initializes the GeoPackage with the required metadata tables and inserts the spatial reference system information. It then creates tables for each component (overlays, indicators, measures, alerts) and populates them with the corresponding data, including geometry if present.
def create_geopackage(path: Path, data: dict[str, list[dict[str, Any]]]) -> None:
    con = sqlite3.connect(path)
    # The function executes a series of SQL statements to set up the GeoPackage structure, including creating the necessary tables and inserting spatial reference system information. It uses the `executescript` method to execute multiple SQL statements in one call.
    # 1196437808 means "GP" in ASCII, 10300 is the user version for GeoPackage 1.3.0
    con.executescript("""
        PRAGMA application_id=1196437808;
        PRAGMA user_version=10300;
        CREATE TABLE gpkg_spatial_ref_sys (srs_name TEXT NOT NULL, srs_id INTEGER NOT NULL PRIMARY KEY, organization TEXT NOT NULL, organization_coordsys_id INTEGER NOT NULL, definition TEXT NOT NULL, description TEXT);
        CREATE TABLE gpkg_contents (table_name TEXT NOT NULL PRIMARY KEY, data_type TEXT NOT NULL, identifier TEXT UNIQUE, description TEXT DEFAULT '', last_change DATETIME NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')), min_x DOUBLE, min_y DOUBLE, max_x DOUBLE, max_y DOUBLE, srs_id INTEGER);
        CREATE TABLE gpkg_geometry_columns (table_name TEXT NOT NULL, column_name TEXT NOT NULL, geometry_type_name TEXT NOT NULL, srs_id INTEGER NOT NULL, z TINYINT NOT NULL, m TINYINT NOT NULL, PRIMARY KEY (table_name, column_name));
    """)

    # The function inserts predefined spatial reference system entries into the `gpkg_spatial_ref_sys` table, including undefined Cartesian and geographic systems, as well as the WGS 84 geographic coordinate system. It uses the `executemany` method to insert multiple rows in one call.
    con.executemany("INSERT INTO gpkg_spatial_ref_sys VALUES (?,?,?,?,?,?)", [
        ("Undefined Cartesian", -1, "NONE", -1, "undefined", None),
        ("Undefined Geographic", 0, "NONE", 0, "undefined", None),
        ("WGS 84", 4326, "EPSG", 4326,
         'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]',
         "longitude/latitude coordinates in decimal degrees on WGS 84"),
    ])

    # The function iterates over each component in the `COMPONENTS` list, creating a corresponding table in the GeoPackage for each component. It checks if any items in the component have geometry and adjusts the table schema accordingly. The function then inserts the items into the respective tables, including their properties and geometry (if present) in the appropriate format.
    for name in COMPONENTS:
        items = data.get(name, [])
        spatial = any(geometry(i) for i in items)

        # The function defines the columns for the table based on whether the component has spatial data. If spatial data is present, a geometry column is added to the table schema. The function constructs the SQL statement to create the table with the appropriate columns and executes it.
        columns = [
            "fid INTEGER PRIMARY KEY AUTOINCREMENT",
            "item_id TEXT",
            "name TEXT",
            "status TEXT",
            "value TEXT",
            "unit TEXT",
            "description TEXT",
            "source_json TEXT"
        ]
        if spatial:
            columns.append("geom BLOB")
            con.execute(f'CREATE TABLE "{name}" ({", ".join(columns)})')
            con.execute(
                "INSERT INTO gpkg_contents(table_name,data_type,identifier,description,srs_id) VALUES (?,?,?,?,?)",
                (name, "features" if spatial else "attributes", name, f"Tygron {name}", 4326 if spatial else None)
            )
        if spatial:
            con.execute(
                "INSERT INTO gpkg_geometry_columns VALUES (?,?,?,?,?,?)",
                (name, "geom", "GEOMETRY", 4326, 0, 0)
            )

        # The function iterates over each item in the component's data, extracting its properties and preparing the values for insertion into the table. It constructs a tuple of values for each item, including its ID, name, status, value, unit, description, and a JSON representation of the source data. If the component has spatial data, it converts the geometry to a GeoPackage geometry blob and includes it in the insertion statement. The function executes the insertion statement for each item, committing the changes to the database at the end.
        for item in items:
            p = properties(item)
            vals = (
                str(p.get("id", "")),
                str(p.get("name", p.get("shortName", ""))),
                str(p.get("status", p.get("severity", ""))),
                str(p.get("value", p.get("currentValue", ""))),
                str(p.get("unit", "")),
                str(p.get("description", p.get("warnings", ""))),
                json.dumps(p, ensure_ascii=False, separators=(",", ":"))
            )
            if spatial:
                blob = _gpkg_geometry(geometry(item)) if geometry(item) else None
                con.execute(
                    f'INSERT INTO "{name}"(item_id,name,status,value,unit,description,source_json,geom) VALUES (?,?,?,?,?,?,?,?)',
                    vals + (blob,)
                )
            else:
                con.execute(
                    f'INSERT INTO "{name}"(item_id,name,status,value,unit,description,source_json) VALUES (?,?,?,?,?,?,?)',
                    vals
                )
    con.commit()
    con.close()


# write CSV file from a list of dictionaries. The function extracts the properties of each item and writes them to a CSV file at the specified path. It determines the fieldnames based on the keys present in the items and writes the header row followed by the data rows. The values are converted to simple types (string, integer, float, or None) before writing to the CSV.
def _write_csv(path: Path, items: Iterable[dict[str, Any]]) -> None:
    rows = [properties(i) for i in items]
    keys = sorted({k for row in rows for k in row})
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys or ["geen_records"], extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: _simple(v) for k, v in row.items()})


# write JSON file from an object. The function serializes the object to a JSON string with non-ASCII characters preserved and indented formatting, and writes it to a file at the specified path.
def _write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


# Function to extract and sanitize dossier fields from a dictionary of values. The function ensures that each field is present in the output dictionary, converting values to strings, stripping whitespace, and truncating to a maximum length of 2000 characters. If a field is missing, it defaults to an empty string.
def _dossier_fields(values: dict[str, Any] | None) -> dict[str, str]:
    source = values if isinstance(values, dict) else {}
    return {
        key: str(source.get(key, "")).strip()[:2000]
        for key in DOSSIER_FIELDS
    }


# Function to generate an HTML table report from a list of items. The function constructs an HTML table with columns for name, value/status, and description. If the list of items is empty, it returns a message indicating that no items are present. The function escapes HTML characters in the item values to prevent injection and ensure proper rendering in the HTML report.
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


# Function to generate an HTML report summarizing the scenario dossier. The function constructs an HTML document with sections for the dossier passport, decision and rationale, included components, indicators, measures, alerts, and technical transfer information. It includes a list of warnings and metrics for each component. The function escapes HTML characters in the metadata and data values to ensure proper rendering in the report.
def _report_html(metadata: dict[str, Any], data: dict[str, list[dict[str, Any]]], warnings: list[str]) -> str:
    record = metadata["record"]
    decision = metadata["decision"]
    components = metadata["components"]

    # Helper function to safely retrieve and escape values from the metadata or data dictionaries. If the value is None or empty, it returns a fallback string indicating that the value is not recorded.
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
    # The function constructs the HTML structure for the report, including the header, main content sections, and footer. It uses the helper functions to generate tables for indicators, measures, and alerts, and includes the dossier passport and decision information. The final HTML string is returned for writing to a file.
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


# Function to build a scenario dossier archive. The function creates a structured directory containing metadata, source data, GIS files, tables, rasters, and a report. It validates the dossier, generates a manifest for integrity checking, and creates a ZIP archive of the entire dossier. The function returns the path to the created archive and a dictionary containing metadata about the export process.
def build_archive(
        output_dir: Path,
        project: str,
        scenario: str,
        data: dict[str, list[dict[str, Any]]],
        notes: str = "",
        source: str = "demo",
        warnings: list[str] | None = None,
        raster_fetcher=None,
        dossier_fields: dict[str, Any] | None = None
) -> tuple[Path, dict[str, Any]]:
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    archive_name = f"{slug(project)}_{slug(scenario)}_{stamp}.zip"
    output_dir.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="scenario-dossier-"))
    try:
        # Create the necessary folder structure for the dossier export, including directories for metadata, source data (bron), GIS files, tables (tabellen), rasters, and the report (rapport).
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

        # Write the dossier metadata to a JSON file in the metadata directory. The metadata includes information about the schema, project, scenario, export timestamp, source, coordinate reference system, component counts, notes, record details, decision details, software version, and token archival status.
        _write_json(work / "metadata" / "dossier.json", metadata)
        export_warnings = list(warnings or [])
        for name, items in selected.items():
            _write_json(work / "bron" / f"{name}.json", items)
            _write_csv(work / "tabellen" / f"{name}.csv", items)
            spatial = [feature(i) for i in items if geometry(i)]
            if spatial:
                _write_json(work / "gis" / f"{name}.geojson", {"type": "FeatureCollection", "name": name,
                                                               "crs": {"type": "name", "properties": {
                                                                   "name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
                                                               "features": spatial})
        create_geopackage(work / "gis" / "scenario.gpkg", selected)

        # If a raster fetcher function is provided, the function attempts to retrieve GeoTIFF overlays for each overlay in the selected data. It iterates over the overlays, extracts their properties, and uses the raster fetcher to obtain the content of the overlay based on its ID. The retrieved content is then written to a GeoTIFF file in the rasters directory. If an error occurs during the fetching process, a warning message is added to the export warnings list.
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

        # Write the export log to a JSON file in the metadata directory, indicating that the export process has completed and including any warnings that were generated during the export.
        _write_json(
            work / "metadata" / "exportlog.json",
            {"status": "completed", "warnings": export_warnings}
        )
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
            manifest_lines.append(
                f"{hashlib.sha256(file.read_bytes()).hexdigest()}  {file.relative_to(work).as_posix()}")
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
