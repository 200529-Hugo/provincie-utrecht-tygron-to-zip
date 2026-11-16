"""Coördinaten omzetten zonder geometrietypes of eigenschappen te wijzigen."""

from functools import cache

from pyproj import Transformer

WGS84 = 'EPSG:4326'
RD_NEW = 'EPSG:28992'
EXPORT_CRS = {WGS84: 4326, RD_NEW: 28992}


@cache
def _transformer(source_crs: str, target_crs: str) -> Transformer:
    return Transformer.from_crs(source_crs, target_crs, always_xy=True)


def reproject_geometry(geometry: dict, source_crs: str, target_crs: str) -> dict:
    """Zet horizontale coördinaten om in GIS-asvolgorde."""
    if source_crs == target_crs:
        return geometry

    transform = _transformer(source_crs, target_crs)

    def project_coordinates(coordinates):
        if not coordinates or isinstance(coordinates[0], (list, tuple)):
            return [project_coordinates(part) for part in coordinates]
        x, y, *other_dimensions = coordinates
        x, y = transform.transform(x, y, errcheck=True)
        return [x, y, *other_dimensions]

    def project_geometry(part):
        result = {key: value for key, value in part.items() if key not in ('bbox', 'crs')}
        if part['type'] == 'GeometryCollection':
            result['geometries'] = [project_geometry(geometry) for geometry in part['geometries']]
        else:
            result['coordinates'] = project_coordinates(part['coordinates'])
        return result

    return project_geometry(geometry)


def _positions(coordinates):
    if coordinates and isinstance(coordinates[0], (list, tuple)):
        for part in coordinates:
            yield from _positions(part)
    elif coordinates:
        yield coordinates


def has_wgs84_coordinates(geometry: dict) -> bool:
    if geometry['type'] == 'GeometryCollection':
        return all(has_wgs84_coordinates(part) for part in geometry['geometries'])
    return all(
        len(position) >= 2
        and all(type(value) in (int, float) for value in position[:2])
        and -180 <= position[0] <= 180
        and -90 <= position[1] <= 90
        for position in _positions(geometry['coordinates'])
    )
