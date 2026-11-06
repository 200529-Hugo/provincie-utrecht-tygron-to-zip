from flask import current_app

from . import api
from ..http.contracts import api_endpoint
from ..models.api.requests.projects import DemoCatalogRequest, DemoProjectsRequest, DemoScenariosRequest, DemoThumbnailRequest
from ..models.api.responses.projects import DemoCatalogResponse, DemoProjectsResponse, DemoScenariosResponse, DemoThumbnailResponse


@api_endpoint(api, '/demo', DemoCatalogRequest, DemoCatalogResponse)
def catalog(payload):
    return current_app.extensions['controllers']['projects'].demo_catalog()


@api_endpoint(api, '/demo/projects', DemoProjectsRequest, DemoProjectsResponse)
def projects(payload):
    return current_app.extensions['controllers']['projects'].demo_projects()


@api_endpoint(api, '/demo/scenarios/<project_id>', DemoScenariosRequest, DemoScenariosResponse)
def scenarios(payload):
    return current_app.extensions['controllers']['projects'].demo_scenarios(payload)


@api_endpoint(api, '/demo/thumbnail/<project_id>', DemoThumbnailRequest, DemoThumbnailResponse)
def thumbnail(payload):
    return current_app.extensions['controllers']['projects'].demo_thumbnail(payload)
