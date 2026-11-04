from dataclasses import dataclass, field
from pathlib import Path

from ..base import JsonModel


@dataclass(frozen=True)
class ErrorResponse(JsonModel):
    error: str


@dataclass(frozen=True)
class ImageResponse:
    """Geen afbeelding is een geldig antwoord met HTTP-status 204."""

    data: bytes | None = field(repr=False)
    mimetype: str = 'image/png'


@dataclass(frozen=True)
class FileResponse:
    path: Path
    mimetype: str = 'application/zip'
    as_attachment: bool = True


@dataclass(frozen=True)
class TextResponse:
    content: str
    mimetype: str = 'text/plain'
