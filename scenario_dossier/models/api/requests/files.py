from dataclasses import dataclass, field

from ..base import JsonModel, object_value, text


@dataclass(frozen=True)
class DownloadRequest(JsonModel):
    name: str

    @classmethod
    def from_dict(cls, value: dict) -> 'DownloadRequest':
        name = text(object_value(value), 'name')
        if not name.endswith('.zip') or '/' in name or '\\' in name:
            raise ValueError('Het verzoek kon niet worden verwerkt.')
        return cls(name=name)


@dataclass(frozen=True)
class ValidateArchiveRequest:
    """De payload is een ZIP-bestand en geen JSON-object."""

    data: bytes = field(repr=False)

    @classmethod
    def from_bytes(cls, value: bytes) -> 'ValidateArchiveRequest':
        if not value:
            raise ValueError('Selecteer een ZIP-dossier om te controleren.')
        return cls(data=value)
