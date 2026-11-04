from dataclasses import dataclass

from .scenario_data import ScenarioData
from .scenario_item import ScenarioItem


@dataclass
class ScenarioInspection:
    project: str
    scenario: str
    data: ScenarioData
    items: list[ScenarioItem]
    warnings: list[str]
