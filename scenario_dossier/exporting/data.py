"""Gedeelde bronconversie en het schrijven van JSON en CSV."""

from __future__ import annotations

import csv
import io
import json
import re
from dataclasses import fields
from pathlib import Path
from typing import Any, Iterable

from ..models.dossier.dossier_details import DossierDetails
from ..models.scenario.component_type import ComponentType

COMPONENTS = tuple(ComponentType.values())
DOSSIER_FIELDS = tuple(item.name for item in fields(DossierDetails))


def slug(value: str) -> str:
    """Maak een korte, veilige naam voor bestanden in het dossier."""
    clean = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip()).strip("-").lower()
    return clean[:60] or "scenario"


def feature(item: dict[str, Any]) -> dict[str, Any]:
    """Zet brongegevens om naar een GeoJSON-feature."""
    if item.get("type") == "Feature":
        return item
    geometry = item.get("geometry")

    props = {k: v for k, v in item.items() if k != "geometry"}
    return {"type": "Feature", "geometry": geometry, "properties": props}


def properties(item: dict[str, Any]) -> dict[str, Any]:
    """Lees eigenschappen zonder de kaartgeometrie."""
    return item.get("properties", {}) \
        if item.get("type") == "Feature" \
        else {
        k: v for k, v in item.items()
        if k != "geometry"
    }


def geometry(item: dict[str, Any]) -> dict[str, Any] | None:
    """Lees de GeoJSON-geometrie van een bronrecord."""
    return item.get('geometry')


def _simple(value: Any) -> str | int | float | None:
    """Maak waarden geschikt voor CSV en SQLite."""
    if value is None or isinstance(value, (str, int, float)):
        return value
    if isinstance(value, bool):
        return int(value)

    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _write_csv(path: Path, items: Iterable[dict[str, Any]]) -> None:
    """Schrijf een tabel met alle beschikbare bronvelden."""
    rows = [properties(i) for i in items]
    keys = sorted({k for row in rows for k in row})
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys or ["geen_records"], extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: _simple(v) for k, v in row.items()})


def _write_json(path: Path, obj: Any) -> None:
    """Schrijf JSON met leesbare inspringing en Nederlandse tekens."""
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def _dossier_fields(value: dict[str, Any] | None) -> dict[str, str]:
    return DossierDetails.from_dict(value).to_dict()
