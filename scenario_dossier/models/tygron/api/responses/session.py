from dataclasses import dataclass, field
from typing import Any

from .....integrations.tygron.errors import TygronError


@dataclass(frozen=True)
class ComponentResponse:
    items: list[dict[str, Any]]

    @classmethod
    def from_api(cls, value, component):
        if isinstance(value, dict) and value.get('type') == 'FeatureCollection':
            value = value.get('features', [])
        if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
            raise TygronError(f'Component {component} heeft geen verwachte lijststructuur.')
        return cls(value)


@dataclass(frozen=True)
class OverlayGeoTiffResponse:
    data: bytes = field(repr=False)

    @classmethod
    def from_bytes(cls, value):
        if not isinstance(value, bytes):
            raise TygronError('Tygron gaf geen rasterbestand terug.')
        return cls(value)
