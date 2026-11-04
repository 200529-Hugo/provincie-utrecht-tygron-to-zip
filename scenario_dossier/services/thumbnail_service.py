"""Begrensde afbeeldingscache en offline previews zonder opgeslagen credentials."""
from collections import OrderedDict
from concurrent.futures import Future
from dataclasses import dataclass
from hashlib import sha256
import json
from math import cos, isfinite, radians
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import BoundedSemaphore, RLock
from time import monotonic, time

from ..tygron import TygronError


@dataclass(frozen=True)
class Thumbnail:
    data: bytes
    mimetype: str


class ThumbnailService:
    def __init__(self, lifetime=86400, failure_lifetime=120, capacity=128,
                 max_parallel=3, cache_dir=None):
        self.lifetime = lifetime
        self.failure_lifetime = failure_lifetime
        self.capacity = capacity
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self._cache = OrderedDict()
        self._pending = {}
        self._lock = RLock()
        self._disk_lock = RLock()
        self._slots = BoundedSemaphore(max(1, min(6, int(max_parallel))))

    def get(self, key, loader):
        # Laat andere cacheverzoeken door tijdens een trage Tygron-aanroep.
        with self._lock:
            now = monotonic()
            for expired in [k for k, (deadline, _) in self._cache.items() if deadline <= now]:
                del self._cache[expired]
            if key in self._cache:
                self._cache.move_to_end(key)
                return self._cache[key][1]
            future = self._pending.get(key)
            owner = future is None
            if owner:
                future = Future()
                self._pending[key] = future
        if not owner:
            return future.result()
        try:
            cached = self._read_disk(key)
            if cached is not None:
                thumbnail, duration = cached
            else:
                with self._slots:
                    try:
                        thumbnail = loader()
                    except (TygronError, ValueError):
                        thumbnail = None
                duration = self.lifetime if thumbnail else self.failure_lifetime
                if thumbnail:
                    self._write_disk(key, thumbnail)
            with self._lock:
                self._cache[key] = (monotonic() + duration, thumbnail)
                while len(self._cache) > self.capacity:
                    self._cache.popitem(last=False)
            future.set_result(thumbnail)
            return thumbnail
        except BaseException as error:
            # Geef ook wachtende verzoeken dezelfde fout terug.
            future.set_exception(error)
            raise
        finally:
            with self._lock:
                self._pending.pop(key, None)

    def _path(self, key):
        encoded = json.dumps(key, ensure_ascii=True, separators=(',', ':')).encode()
        return self.cache_dir / (sha256(encoded).hexdigest() + '.thumbnail')

    def _read_disk(self, key):
        if self.cache_dir is None:
            return None
        try:
            path = self._path(key)
            remaining = self.lifetime - (time() - path.stat().st_mtime)
            if remaining <= 0:
                return None
            with path.open('rb') as cached:
                record = cached.read(2_000_065)
            if len(record) > 2_000_064:
                return None
            mimetype, data = record.split(b'\n', 1)
            if (mimetype == b'image/png' and data.startswith(b'\x89PNG\r\n\x1a\n')
                    or mimetype == b'image/svg+xml' and data.startswith(b'<svg ')):
                return Thumbnail(data, mimetype.decode('ascii')), remaining
        except (OSError, ValueError):
            pass
        return None

    def _write_disk(self, key, thumbnail):
        if self.cache_dir is None:
            return
        temporary = None
        try:
            with self._disk_lock:
                self.cache_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
                with NamedTemporaryFile(dir=self.cache_dir, prefix='.thumbnail-', delete=False) as cached:
                    temporary = Path(cached.name)
                    cached.write(thumbnail.mimetype.encode('ascii') + b'\n' + thumbnail.data)
                os.replace(temporary, self._path(key))
                temporary = None
                files = [p for p in self.cache_dir.glob('*.thumbnail')
                         if len(p.stem) == 64 and all(c in '0123456789abcdef' for c in p.stem)]
                files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                now = time()
                for index, path in enumerate(files):
                    if index >= self.capacity or now - path.stat().st_mtime >= self.lifetime:
                        path.unlink(missing_ok=True)
        except OSError:
            # Een volle of niet-schrijfbare cache mag een geldige preview niet blokkeren.
            pass
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass

    @staticmethod
    def demo(project):
        """Draw real demo geometry as a compact SVG, usable entirely offline."""
        geometries = []
        for scenario in project.scenarios[:1]:
            for component in ('measures', 'alerts'):
                for record in scenario.data.items(component):
                    if isinstance(record.get('geometry'), dict):
                        geometries.append((component, record['geometry']))
        points = []

        def collect(value):
            if isinstance(value, (list, tuple)) and len(value) >= 2 and all(isinstance(v, (int, float)) and isfinite(v) for v in value[:2]):
                points.append(value[:2])
            elif isinstance(value, (list, tuple)):
                for part in value:
                    collect(part)

        def visit(geometry):
            if geometry.get('type') == 'GeometryCollection':
                for child in geometry.get('geometries', []):
                    visit(child)
            else:
                collect(geometry.get('coordinates', []))

        for _, geometry in geometries:
            visit(geometry)
        if not points:
            raise ValueError('Geen kaartgeometrie beschikbaar.')
        xscale = cos(radians(sum(p[1] for p in points) / len(points)))
        west, east = min(p[0] for p in points) * xscale, max(p[0] for p in points) * xscale
        south, north = min(p[1] for p in points), max(p[1] for p in points)
        scale = min(280 / max(east - west, 0.00001), 160 / max(north - south, 0.00001))
        center_x, center_y = (west + east) / 2, (south + north) / 2

        def xy(point):
            return 160 + (point[0] * xscale - center_x) * scale, 100 - (point[1] - center_y) * scale

        def path(coordinates, close=False):
            return ' '.join(('M' if i == 0 else 'L') + f'{xy(p)[0]:.2f},{xy(p)[1]:.2f}' for i, p in enumerate(coordinates)) + (' Z' if close else '')

        shapes = []
        def draw(geometry, alert=False):
            kind, coordinates = geometry.get('type'), geometry.get('coordinates', [])
            color = '#c52d26' if alert else '#467c68'
            if kind == 'GeometryCollection':
                for child in geometry.get('geometries', []):
                    draw(child, alert)
            elif kind == 'Point':
                x, y = xy(coordinates)
                shapes.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="5" fill="{color}" stroke="white" stroke-width="2"/>')
            elif kind == 'MultiPoint':
                for point in coordinates:
                    draw({'type': 'Point', 'coordinates': point}, alert)
            elif kind in ('LineString', 'MultiLineString'):
                for line in ([coordinates] if kind == 'LineString' else coordinates):
                    shapes.append(f'<path d="{path(line)}" fill="none" stroke="white" stroke-width="7" stroke-linecap="round"/>')
                    shapes.append(f'<path d="{path(line)}" fill="none" stroke="{color}" stroke-width="3" stroke-linecap="round"/>')
            elif kind in ('Polygon', 'MultiPolygon'):
                for polygon in ([coordinates] if kind == 'Polygon' else coordinates):
                    commands = ' '.join(path(ring, True) for ring in polygon)
                    shapes.append(f'<path d="{commands}" fill="{color}" fill-opacity=".22" fill-rule="evenodd" stroke="{color}" stroke-width="2"/>')

        for component, geometry in geometries:
            draw(geometry, component == 'alerts')
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="320" height="200" viewBox="0 0 320 200">'
               '<defs><pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">'
               '<path d="M32 0H0V32" fill="none" stroke="#d8e1d8" stroke-width="1"/></pattern></defs>'
               '<rect width="320" height="200" fill="#edf1e9"/><rect width="320" height="200" fill="url(#grid)"/>'
               + ''.join(shapes) + '</svg>')
        return Thumbnail(svg.encode(), 'image/svg+xml')
