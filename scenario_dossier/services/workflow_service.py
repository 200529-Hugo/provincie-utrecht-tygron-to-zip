"""Open een bron en hergebruik dezelfde controle en export voor alle bronnen."""

from contextlib import contextmanager
from pathlib import Path

from ..models import ActiveSessionCredentials, ArchiveResult, ProjectCredentials
from ..models.api.requests.workflow import ExportRequest, InspectRequest
from ..models.scenario.context import ScenarioContext
from ..models.scenario.inspection import ScenarioInspection
from .demo_service import DemoService
from .dossier_service import DossierService
from .scenario_service import ScenarioService
from .tygron_service import TygronService


class WorkflowService:
    def __init__(self, output_dir: Path):
        self.demo = DemoService()
        self.tygron = TygronService()
        self.scenarios = ScenarioService()
        self.dossiers = DossierService(output_dir)

    @contextmanager
    def resolve(self, payload: InspectRequest):
        if payload.source == 'demo':
            project = self.demo.get_project(payload.project_id)
            scenario = project.get_scenario(payload.scenario_id)
            yield ScenarioContext(project.name, scenario.name, scenario.data)
            return
        if not payload.project_name or not payload.scenario_name:
            raise ValueError('Selecteer een project en scenario.')
        if payload.source == 'tygron_project':
            credentials = ProjectCredentials(payload.base_url, payload.username, payload.login_key, payload.domain)
            with self.tygron.project_connection(credentials, payload.project_file) as connection:
                yield self._context(payload, connection)
        else:
            credentials = ActiveSessionCredentials(payload.base_url, payload.token)
            connection = self.tygron.active_connection(credentials)
            yield self._context(payload, connection)

    @staticmethod
    def _context(payload, connection) -> ScenarioContext:
        return ScenarioContext(payload.project_name, payload.scenario_name, connection.data,
                               connection.warnings, connection.raster_fetcher)

    def inspect(self, payload: InspectRequest) -> ScenarioInspection:
        with self.resolve(payload) as context:
            return ScenarioInspection(context.project, context.scenario, context.data,
                                      self.scenarios.inventory(context.data), context.warnings)

    def export(self, payload: ExportRequest) -> ArchiveResult:
        with self.resolve(payload) as context:
            selected = self.scenarios.select(context.data, payload.components, payload.selected_items)
            return self.dossiers.create(
                context.project, context.scenario, selected,
                notes=payload.notes, source=payload.source, warnings=context.warnings,
                details=payload.dossier,
                raster_fetcher=context.raster_fetcher if payload.rasters else None,
            )
