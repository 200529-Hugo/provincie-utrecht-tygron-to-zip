from dataclasses import dataclass
from typing import ClassVar
from urllib.parse import urlencode


@dataclass(frozen=True)
class WmsCapabilitiesRequest:
    path: ClassVar[str] = '/web/wms?REQUEST=GetCapabilities'
    max_bytes: ClassVar[int] = 512_000


@dataclass(frozen=True)
class WmsMapRequest:
    bounds: tuple[float, float, float, float]
    width: int = 320
    height: int = 200
    max_bytes: ClassVar[int] = 2_000_000

    @classmethod
    def from_project_bounds(cls, bounds):
        """Pas het hele project in de thumbnail zonder de kaart uit te rekken."""
        west, south, east, north = bounds
        width, height = east - west, north - south
        ratio = cls.width / cls.height
        width, height = max(width, height * ratio) * 1.04, max(height, width / ratio) * 1.04
        center_x, center_y = (west + east) / 2, (south + north) / 2
        return cls((center_x - width / 2, center_y - height / 2,
                    center_x + width / 2, center_y + height / 2))

    @property
    def path(self) -> str:
        query = {
            'SERVICE': 'WMS', 'REQUEST': 'GetMap', 'VERSION': '1.3.0',
            'LAYERS': 'TOPOGRAPHIC', 'STYLES': '', 'CRS': 'EPSG:3857',
            'BBOX': ','.join(str(value) for value in self.bounds),
            'WIDTH': self.width, 'HEIGHT': self.height, 'FORMAT': 'image/png',
            'TRANSPARENT': 'false', 'maptype': 'CURRENT', 'forcexy': 'true',
        }
        return '/web/wms?' + urlencode(query)
