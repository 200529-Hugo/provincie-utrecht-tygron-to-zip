from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .component_type import ComponentType


@dataclass(frozen=True)
class ScenarioItem:
    key: str
    component: ComponentType
    name: str
    detail: str = ""
    spatial: bool = False
    geometry_type: str = ""
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_raw(
        cls,
        component: ComponentType,
        raw: dict[str, Any],
        index: int,
    ) -> "ScenarioItem":
        properties = raw.get("properties") or {} if raw.get("type") == "Feature" else raw
        item_id = properties.get("id")
        key = f"id:{item_id}" if item_id is not None else f"index:{index}"
        value = properties.get("value", properties.get("currentValue"))
        parts = (
            properties.get("type", properties.get("overlayType", "")),
            properties.get("status", properties.get("severity", "")),
            value,
            properties.get("unit", ""),
        )
        geometry = raw.get("geometry")
        return cls(
            key=key,
            component=component,
            name=str(
                properties.get(
                    "name",
                    properties.get("shortName", f"{component.value} {index + 1}"),
                )
            ),
            detail=" ".join(str(part) for part in parts if part not in (None, ""))[:240],
            spatial=bool(geometry),
            geometry_type=geometry.get("type", "") if isinstance(geometry, dict) else "",
            raw=raw,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "component": self.component.value,
            "name": self.name,
            "detail": self.detail,
            "spatial": self.spatial,
            "geometry_type": self.geometry_type,
        }
