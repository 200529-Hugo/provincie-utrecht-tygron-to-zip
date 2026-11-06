from dataclasses import replace
from werkzeug.exceptions import NotFound

from ..i18n import translate_message
from ..models.api.requests.files import DownloadRequest, ValidateArchiveRequest
from ..models.api.responses.files import DownloadResponse, ValidateArchiveResponse
from ..services.file_service import FileService
from ..services.validation_service import ValidationService


class FileController:
    def __init__(self, export_dir, docs_dir):
        self.files = FileService(export_dir, docs_dir)
        self.validation = ValidationService()

    def download(self, payload: DownloadRequest) -> DownloadResponse:
        try:
            return DownloadResponse(self.files.archive(payload.name))
        except FileNotFoundError as error:
            raise NotFound() from error

    def validate(self, payload: ValidateArchiveRequest, language='nl') -> ValidateArchiveResponse:
        report = self.validation.validate_bytes(payload.data)
        response = ValidateArchiveResponse.from_report(report.to_dict())
        checks = [replace(check, check=translate_message(check.check, language),
                          detail=translate_message(check.detail, language)) for check in response.checks]
        return replace(response, checks=checks)
