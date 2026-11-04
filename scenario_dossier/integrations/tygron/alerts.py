"""Zet Tygron-waarschuwingen en panel-attenties om naar dossieralerts."""

from typing import Any


def _item_properties(item: dict[str, Any]) -> dict[str, Any]:
    if item.get("type") == "Feature":
        return item.get("properties", {})
    return item


def _warning_alert(component: str, item: dict[str, Any]) -> dict[str, Any] | None:
    props = _item_properties(item)
    warning = props.get("warnings") or props.get("warning") or props.get("failText")
    if not warning:
        return None
    return {
        "id": f"{component}-{props.get('id', 'onbekend')}",
        "name": f"Waarschuwing bij {props.get('name', component)}",
        "severity": "warning",
        "status": "open",
        "description": str(warning),
        "source": component,
    }


def _panel_alert(panel: dict[str, Any]) -> dict[str, Any] | None:
    props = _item_properties(panel)
    attention = (props.get("attributes") or {}).get("ATTENTION", [0])
    if not attention or float(attention[0]) <= 0:
        return None

    alert: dict[str, Any] = {
        "id": f"panel-{props.get('id', 'onbekend')}",
        "name": props.get("name") or "Tygron-attentie",
        "severity": "attention",
        "status": "open",
        "description": props.get("warnings") or props.get("text") or "Panel vraagt aandacht.",
        "source": "panels",
    }

    geometry = props.get("point") or props.get("polygons")
    if geometry:
        return {"type": "Feature", "geometry": geometry, "properties": alert}
    return alert
