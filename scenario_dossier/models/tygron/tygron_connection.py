from dataclasses import dataclass, field
from typing import Callable

from ..scenario.scenario_data import ScenarioData


@dataclass
class TygronConnection:
    data: ScenarioData
    warnings: list[str] = field(default_factory=list)
    raster_fetcher: Callable[[int], bytes] | None = field(default=None, repr=False)
