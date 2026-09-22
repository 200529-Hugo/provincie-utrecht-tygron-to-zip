from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .scenario_data import ScenarioData


@dataclass
class Scenario:
    id: str
    name: str
    description: str
    data: ScenarioData

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Scenario":
        return cls(
            id=str(value.get("id", "")),
            name=str(value.get("name", "")),
            description=str(value.get("description", "")),
            data=ScenarioData.from_dict(value.get("data")),
        )

    def to_public_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
        }
