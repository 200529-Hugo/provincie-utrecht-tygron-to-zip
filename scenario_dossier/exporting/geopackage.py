"""Binaire geometrie en GeoPackage-tabellen voor GIS-programma’s."""

from __future__ import annotations

import json
import sqlite3
import struct
from pathlib import Path
from typing import Any

from .data import COMPONENTS, geometry, properties, _simple


def _wkb(geom: dict[str, Any]) -> bytes:
    """Schrijf de binaire geometrie volgens het WKB-bestandsformaat."""
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
        return endian + struct.pack("<II", 4, len(coords)) + b"".join(
            _wkb({"type": "Point", "coordinates": p}) for p in coords
        )


    if kind == "MultiLineString":
        return endian + struct.pack("<II", 5, len(coords)) + b"".join(
            _wkb({"type": "LineString", "coordinates": p}) for p in coords
        )


    if kind == "MultiPolygon":
        return endian + struct.pack("<II", 6, len(coords)) + b"".join(
            _wkb({"type": "Polygon", "coordinates": p}) for p in coords
        )


    if kind == "GeometryCollection":
        geometries = geom.get("geometries", [])
        return endian + struct.pack("<II", 7, len(geometries)) + b"".join(_wkb(item) for item in geometries)


    raise ValueError(f"Niet-ondersteund geometrietype: {kind}")


def _gpkg_geometry(geom: dict[str, Any]) -> bytes:
    """Voeg de GeoPackage-header toe aan de binaire geometrie."""
    return b"GP" + bytes((0, 1)) + struct.pack("<i", 4326) + _wkb(geom)


def create_geopackage(path: Path, data: dict[str, list[dict[str, Any]]]) -> None:
    """Schrijf alle componenten naar een GIS-bestand met vaste tabellen."""
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
        ("WGS 84", 4326, "EPSG", 4326,
         'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]',
         "longitude/latitude coordinates in decimal degrees on WGS 84"),
    ])


    for name in COMPONENTS:
        items = data.get(name, [])
        spatial = any(geometry(i) for i in items)


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
