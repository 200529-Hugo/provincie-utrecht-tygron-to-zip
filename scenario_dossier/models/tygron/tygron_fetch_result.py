from dataclasses import dataclass, field

from ..scenario.scenario_data import ScenarioData


@dataclass
class TygronFetchResult:
    data: ScenarioData
    warnings: list[str] = field(default_factory=list)
