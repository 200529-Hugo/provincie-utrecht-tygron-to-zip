from dataclasses import dataclass, field
from math import isfinite
from struct import unpack
from xml.etree import ElementTree

from .....integrations.tygron.errors import TygronError


@dataclass(frozen=True)
class WmsCapabilitiesResponse:
    bounds: tuple[float, float, float, float]

    @classmethod
    def from_bytes(cls, value):
        try:
            root = ElementTree.fromstring(value)
            for element in root.iter():
                if element.tag.rsplit('}', 1)[-1] != 'BoundingBox':
                    continue
                if (element.get('CRS') or element.get('SRS') or '').upper() != 'EPSG:3857':
                    continue
                bounds = tuple(float(element.attrib[name]) for name in ('minx', 'miny', 'maxx', 'maxy'))
                west, south, east, north = bounds
                if all(isfinite(number) for number in bounds) and west < east and south < north:
                    return cls(bounds)
        except (ElementTree.ParseError, ValueError, KeyError) as error:
            raise TygronError('Geen bruikbare kaartbegrenzing beschikbaar.') from error
        raise TygronError('Geen bruikbare kaartbegrenzing beschikbaar.')


@dataclass(frozen=True)
class WmsMapResponse:
    data: bytes = field(repr=False)

    @classmethod
    def from_bytes(cls, value, width, height):
        if len(value) < 33 or not value.startswith(b'\x89PNG\r\n\x1a\n') or value[12:16] != b'IHDR':
            raise TygronError('Tygron gaf geen geldige kaartafbeelding terug.')
        if unpack('>II', value[16:24]) != (width, height):
            raise TygronError('De kaartafbeelding heeft onverwachte afmetingen.')
        return cls(value)
