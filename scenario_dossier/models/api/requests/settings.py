from dataclasses import dataclass

from ..base import EmptyRequest, JsonModel, object_value, text


@dataclass(frozen=True)
class MapConfigRequest(EmptyRequest):
    pass


@dataclass(frozen=True)
class ManualRequest(EmptyRequest):
    pass


@dataclass(frozen=True)
class TranslationsRequest(JsonModel):
    language: str

    @classmethod
    def from_dict(cls, value: dict) -> 'TranslationsRequest':
        language = text(object_value(value), 'language')
        if language not in ('nl', 'en'):
            raise ValueError('Het verzoek kon niet worden verwerkt.')
        return cls(language=language)
