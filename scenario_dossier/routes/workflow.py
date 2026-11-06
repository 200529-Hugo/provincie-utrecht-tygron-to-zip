from flask import current_app, g

from . import api
from ..http.contracts import api_endpoint
from ..models.api.requests.workflow import ExportRequest, InspectRequest
from ..models.api.responses.workflow import ExportResponse, InspectResponse


@api_endpoint(api, '/inspect', InspectRequest, InspectResponse, method='POST')
def inspect(payload):
    return current_app.extensions['controllers']['workflow'].inspect(payload, g.account, g.language)


@api_endpoint(api, '/export', ExportRequest, ExportResponse, method='POST')
def export(payload):
    return current_app.extensions['controllers']['workflow'].export(payload, g.account, g.language)
