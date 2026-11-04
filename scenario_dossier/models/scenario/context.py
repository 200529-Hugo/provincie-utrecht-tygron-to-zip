from dataclasses import dataclass, field
from typing import Callable

from .scenario_data import ScenarioData


@dataclass
class ScenarioContext:
    """Dezelfde gegevens, ongeacht of de bron demo, project of actieve sessie is."""

    project: str
    scenario: str
    data: ScenarioData
    warnings: list[str] = field(default_factory=list)
    raster_fetcher: Callable[[int], bytes] | None = field(default=None, repr=False)
