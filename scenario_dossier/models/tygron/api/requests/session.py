from dataclasses import dataclass
from urllib.parse import quote, urlencode


@dataclass(frozen=True)
class ComponentRequest:
    name: str
    output_format: str = 'JSON'
    crs: int | None = None

    @property
    def path(self) -> str:
        query = {'f': self.output_format}
        if self.crs:
            query['crs'] = self.crs
        return f'/api/session/items/{quote(self.name, safe="")}/?{urlencode(query)}'


@dataclass(frozen=True)
class OverlayGeoTiffRequest:
    overlay_id: int

    @property
    def path(self) -> str:
        return '/api/session/overlay.geotiff?' + urlencode({'id': self.overlay_id})
