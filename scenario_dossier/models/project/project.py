from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ...coordinates import WGS84
from ..scenario.scenario import Scenario


@dataclass
class Project:
    id: str
    name: str
    scenarios: list[Scenario] = field(default_factory=list)
    source_crs: str = WGS84

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Project":
        return cls(
            id=str(value.get("id", "")),
            name=str(value.get("name", "")),
            scenarios=[Scenario.from_dict(item) for item in value.get("scenarios") or []],
            source_crs=str(value.get("source_crs", WGS84)),
        )

    def get_scenario(self, scenario_id: str) -> Scenario:
        for scenario in self.scenarios:
            if scenario.id == scenario_id:
                return scenario
        raise LookupError("Scenario niet gevonden.")

    def get_scenarios(self) -> list[Scenario]:
        return self.scenarios

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "source_crs": self.source_crs,
            "scenarios": [scenario.to_public_dict() for scenario in self.scenarios],
        }
