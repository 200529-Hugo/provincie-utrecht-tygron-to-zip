from flask import current_app, g

from . import api
from ..http.contracts import api_endpoint
from ..models.api.requests.files import DownloadRequest, ValidateArchiveRequest
from ..models.api.responses.files import DownloadResponse, ValidateArchiveResponse


@api_endpoint(api, '/download/<name>', DownloadRequest, DownloadResponse)
def download(payload):
    return current_app.extensions['controllers']['files'].download(payload)


@api_endpoint(api, '/validate', ValidateArchiveRequest, ValidateArchiveResponse, method='POST')
def validate(payload):
    return current_app.extensions['controllers']['files'].validate(payload, g.language)
