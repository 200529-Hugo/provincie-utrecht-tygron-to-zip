from dataclasses import dataclass
from typing import ClassVar

from ..base import JsonModel
from .common import TextResponse


@dataclass(frozen=True)
class MapConfigResponse(JsonModel):
    style_url: str


@dataclass(frozen=True)
class ManualResponse(TextResponse):
    mimetype: str = 'text/markdown'


@dataclass(frozen=True)
class TranslationsResponse(JsonModel):
    catalog: dict[str, str]
    root_field: ClassVar[str] = 'catalog'
