from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from ..exporter import build_archive
from ..models import ArchiveResult, DossierDetails, ScenarioData


class DossierService:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def create(
        self,
        project_name: str,
        scenario_name: str,
        data: ScenarioData,
        notes: str = "",
        source: str = "demo",
        warnings: list[str] | None = None,
        details: DossierDetails | None = None,
        raster_fetcher: Callable[[int], bytes] | None = None,
    ) -> ArchiveResult:
        if not project_name.strip() or not scenario_name.strip():
            raise ValueError("Projectnaam en scenarionaam zijn verplicht.")
        archive, metadata = build_archive(
            self.output_dir,
            project_name.strip(),
            scenario_name.strip(),
            data.to_dict(),
            notes=notes.strip(),
            source=source,
            warnings=warnings,
            raster_fetcher=raster_fetcher,
            dossier_fields=(details or DossierDetails()).to_dict(),
        )
        return ArchiveResult(archive, metadata)
