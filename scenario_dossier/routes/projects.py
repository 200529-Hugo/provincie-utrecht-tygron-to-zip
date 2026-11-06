from flask import current_app

from . import api
from ..http.context import current_account
from ..http.contracts import api_endpoint
from ..models.api.requests.projects import AccountProjectsRequest, LegacyProjectsRequest, ProjectThumbnailRequest
from ..models.api.responses.projects import ProjectsResponse, ProjectThumbnailResponse


@api_endpoint(api, '/tygron/projects', AccountProjectsRequest, ProjectsResponse)
def account_projects(payload):
    return current_app.extensions['controllers']['projects'].account_projects(current_account())


@api_endpoint(api, '/tygron/projects', LegacyProjectsRequest, ProjectsResponse, method='POST')
def legacy_projects(payload):
    return current_app.extensions['controllers']['projects'].legacy_projects(payload)


@api_endpoint(api, '/tygron/thumbnail', ProjectThumbnailRequest, ProjectThumbnailResponse, method='POST')
def project_thumbnail(payload):
    return current_app.extensions['controllers']['projects'].project_thumbnail(payload, current_account())
