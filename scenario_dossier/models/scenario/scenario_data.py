from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from .component_type import ComponentType


@dataclass
class ScenarioData:
    overlays: list[dict[str, Any]] = field(default_factory=list)
    indicators: list[dict[str, Any]] = field(default_factory=list)
    measures: list[dict[str, Any]] = field(default_factory=list)
    alerts: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, value: dict[str, Any] | None) -> "ScenarioData":
        source = value or {}
        return cls(
            overlays=list(source.get("overlays") or []),
            indicators=list(source.get("indicators") or []),
            measures=list(source.get("measures") or []),
            alerts=list(source.get("alerts") or []),
        )

    def items(self, component: ComponentType | str) -> list[dict[str, Any]]:
        name = component.value if isinstance(component, ComponentType) else component
        if name not in ComponentType.values():
            raise ValueError(f"Onbekend scenario-onderdeel: {name}")
        return getattr(self, name)

    def to_dict(self) -> dict[str, list[dict[str, Any]]]:
        return {name: list(getattr(self, name)) for name in ComponentType.values()}

    def counts(self) -> dict[str, int]:
        return {name: len(getattr(self, name)) for name in ComponentType.values()}

    def total_count(self) -> int:
        return sum(self.counts().values())

    def copy_with(
        self,
        component: ComponentType | str,
        items: Iterable[dict[str, Any]],
    ) -> "ScenarioData":
        values = self.to_dict()
        name = component.value if isinstance(component, ComponentType) else component
        if name not in values:
            raise ValueError(f"Onbekend scenario-onderdeel: {name}")
        values[name] = list(items)
        return ScenarioData.from_dict(values)
