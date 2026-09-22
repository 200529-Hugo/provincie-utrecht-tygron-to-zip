from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..scenario.scenario import Scenario


@dataclass
class Project:
    id: str
    name: str
    scenarios: list[Scenario] = field(default_factory=list)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Project":
        return cls(
            id=str(value.get("id", "")),
            name=str(value.get("name", "")),
            scenarios=[Scenario.from_dict(item) for item in value.get("scenarios") or []],
        )

    def get_scenario(self, scenario_id: str) -> Scenario:
        for scenario in self.scenarios:
            if scenario.id == scenario_id:
                return scenario
        raise LookupError("Scenario niet gevonden.")

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "scenarios": [scenario.to_public_dict() for scenario in self.scenarios],
        }
