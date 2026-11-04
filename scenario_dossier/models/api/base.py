"""Gedeelde invoercontroles en omzetting van modellen naar JSON."""

from dataclasses import asdict, dataclass
from typing import Any, ClassVar


class JsonModel:
    root_field: ClassVar[str | None] = None

    def to_dict(self) -> Any:
        values = asdict(self)
        return values[self.root_field] if self.root_field else values


def object_value(value: Any) -> dict:
    if not isinstance(value, dict):
        raise ValueError('Het verzoek kon niet worden verwerkt.')
    return value


def text(data: dict, name: str, default: str = '', *, strip: bool = True) -> str:
    value = data.get(name, default)
    if not isinstance(value, str):
        raise ValueError(f'Ongeldig veld: {name}.')
    return value.strip() if strip else value


def boolean(data: dict, name: str, default: bool = False) -> bool:
    value = data.get(name, default)
    if not isinstance(value, bool):
        raise ValueError(f'Ongeldig veld: {name}.')
    return value


def string_list(value: Any, name: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f'Ongeldig veld: {name}.')
    return list(value)


@dataclass(frozen=True)
class EmptyRequest(JsonModel):
    """Een GET-verzoek of een actie zonder inhoud heeft ook een expliciet model."""

    @classmethod
    def from_dict(cls, value: dict):
        object_value(value)
        return cls()
