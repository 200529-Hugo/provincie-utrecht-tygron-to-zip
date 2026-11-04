from werkzeug.exceptions import NotFound

from ..models import ProjectCredentials
from ..models.api.requests.projects import DemoScenariosRequest, DemoThumbnailRequest, LegacyProjectsRequest, ProjectThumbnailRequest
from ..models.api.responses.projects import (
    DemoCatalogResponse, DemoProjectResponse, DemoProjectsResponse, DemoScenarioResponse,
    DemoScenariosResponse, DemoThumbnailResponse, ProjectsResponse, ProjectResponse,
    ProjectThumbnailResponse,
)
from ..services.demo_service import DemoService
from ..services.project_preview_service import ProjectPreviewService
from ..services.project_service import ProjectService


class ProjectController:
    def __init__(self, cache):
        self.projects = ProjectService()
        self.previews = ProjectPreviewService(cache)
        self.demo = DemoService()

    def account_projects(self, account) -> ProjectsResponse:
        projects = self.projects.list_for_account(account)
        return ProjectsResponse([ProjectResponse.from_project(project) for project in projects])

    def legacy_projects(self, payload: LegacyProjectsRequest) -> ProjectsResponse:
        credentials = ProjectCredentials(payload.base_url, payload.username, payload.login_key, payload.domain)
        projects = self.projects.list_projects(credentials)
        return ProjectsResponse([ProjectResponse.from_project(project) for project in projects])

    def demo_projects(self) -> DemoProjectsResponse:
        return DemoProjectsResponse([DemoProjectResponse.from_project(project) for project in self.demo.list_projects()])

    def demo_catalog(self) -> DemoCatalogResponse:
        return DemoCatalogResponse(self.demo_projects().projects)

    def demo_scenarios(self, payload: DemoScenariosRequest) -> DemoScenariosResponse:
        return DemoScenariosResponse([DemoScenarioResponse.from_scenario(item)
                                      for item in self.demo.get_scenarios(payload.project_id)])

    def project_thumbnail(self, payload: ProjectThumbnailRequest, account) -> ProjectThumbnailResponse:
        try:
            thumbnail = self.previews.project(account, payload.project_file)
        except ValueError as error:
            raise NotFound() from error
        return self._image(ProjectThumbnailResponse, thumbnail)

    def demo_thumbnail(self, payload: DemoThumbnailRequest) -> DemoThumbnailResponse:
        return self._image(DemoThumbnailResponse, self.previews.demo_project(payload.project_id))

    @staticmethod
    def _image(model, thumbnail):
        return model(thumbnail.data, thumbnail.mimetype) if thumbnail else model(None)
