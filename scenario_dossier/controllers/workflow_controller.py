"""Controleer accounttoegang en vertaal domeingegevens naar API-antwoorden."""

from dataclasses import replace
from werkzeug.exceptions import Unauthorized

from ..i18n import translate_message
from ..models import ComponentType
from ..models.api.requests.workflow import ExportRequest, InspectRequest
from ..models.api.responses.workflow import (
    ArchiveSummaryResponse, ComponentCountsResponse, ExportResponse,
    InspectResponse, PreviewFeatureResponse, ScenarioItemResponse,
)
from ..services.project_service import ProjectService
from ..services.workflow_service import WorkflowService


class WorkflowController:
    def __init__(self, output_dir):
        self.service = WorkflowService(output_dir)
        self.projects = ProjectService()

    def _authorize(self, payload: InspectRequest, account):
        if payload.source != 'tygron_project' or not payload.authenticated:
            return payload
        if account is None:
            raise Unauthorized()
        project = self.projects.accessible_project(account, payload.project_file)
        credentials = account.credentials
        # Gebruik namen en credentials van de server, niet die uit de browser.
        return replace(payload, base_url=credentials.base_url, username=credentials.username,
                       login_key=credentials.login_key, domain=credentials.domain,
                       project_name=project['name'], scenario_name=project['versions'][0])

    def inspect(self, payload: InspectRequest, account=None, language='nl') -> InspectResponse:
        result = self.service.inspect(self._authorize(payload, account))
        preview = [PreviewFeatureResponse(item.component.value, item.key, item.raw)
                   for item in result.items if item.spatial
                   and item.component in (ComponentType.MEASURES, ComponentType.ALERTS)]
        return InspectResponse(
            project=result.project, scenario=result.scenario,
            counts=ComponentCountsResponse(**result.data.counts()),
            spatial=result.data.get_spatial(),
            warnings=[translate_message(warning, language) for warning in result.warnings],
            preview=preview, items=[ScenarioItemResponse.from_item(item) for item in result.items],
        )

    def export(self, payload: ExportRequest, account=None, language='nl') -> ExportResponse:
        archive = self.service.export(self._authorize(payload, account))
        summary = ArchiveSummaryResponse.from_metadata(archive.metadata)
        summary = replace(summary, warnings=[translate_message(warning, language) for warning in summary.warnings])
        return ExportResponse(filename=archive.filename, download=f'/api/download/{archive.filename}', summary=summary)
