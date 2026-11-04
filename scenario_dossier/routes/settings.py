from flask import current_app, g

from . import api
from ..http.contracts import api_endpoint
from ..models.api.requests.settings import ManualRequest, MapConfigRequest, TranslationsRequest
from ..models.api.responses.settings import ManualResponse, MapConfigResponse, TranslationsResponse


@api_endpoint(api, '/map-config', MapConfigRequest, MapConfigResponse)
def map_config(payload):
    return current_app.extensions['controllers']['settings'].map_config()


@api_endpoint(api, '/werkinstructie', ManualRequest, ManualResponse)
def manual(payload):
    return current_app.extensions['controllers']['settings'].manual(g.language)


@api_endpoint(api, '/translations/<language>', TranslationsRequest, TranslationsResponse)
def translations(payload):
    return current_app.extensions['controllers']['settings'].translations(payload)
