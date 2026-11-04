from dataclasses import dataclass

from ..base import JsonModel
from .common import FileResponse


@dataclass(frozen=True)
class DownloadResponse(FileResponse):
    pass


@dataclass(frozen=True)
class ValidationCheckResponse(JsonModel):
    check: str
    status: str
    detail: str


@dataclass(frozen=True)
class ValidateArchiveResponse(JsonModel):
    schema: str
    validated_at: str
    status: str
    checks_ok: int
    checks_failed: int
    checks: list[ValidationCheckResponse]
    filename: str
    archive_size: int
    project: str
    scenario: str
    exported_at: str
    components: dict[str, int]

    @classmethod
    def from_report(cls, report: dict) -> 'ValidateArchiveResponse':
        return cls(**(report | {'checks': [ValidationCheckResponse(**check) for check in report['checks']]}))
