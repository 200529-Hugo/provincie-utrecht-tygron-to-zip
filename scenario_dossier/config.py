"""Instellingen staan hier zodat de opdrachtgever ze eenvoudig kan terugvinden."""

import os
import secrets
from pathlib import Path

ROOT = Path(__file__).parents[1]


def default_config():
    return {
        'SECRET_KEY': os.environ.get('SCENARIO_SECRET_KEY') or secrets.token_hex(32),
        'MAX_CONTENT_LENGTH': 200_000_000,
        'SESSION_COOKIE_HTTPONLY': True,
        'SESSION_COOKIE_SAMESITE': 'Lax',
        'SESSION_COOKIE_SECURE': os.environ.get('SCENARIO_HTTPS') == '1',
        'EXPORT_DIR': ROOT / 'exports',
        'AUTH_SESSION_LIFETIME': 30 * 60,
        'THUMBNAIL_CONCURRENCY': 3,
        'THUMBNAIL_LIFETIME': 24 * 60 * 60,
        'THUMBNAIL_FAILURE_LIFETIME': 120,
        'THUMBNAIL_CAPACITY': 128,
        'THUMBNAIL_CACHE_DIR': ROOT / '.cache' / 'thumbnails',
        'MAP_STYLE_URL': os.environ.get('OPENMAPTILES_STYLE_URL', 'http://127.0.0.1:8081/styles/OSM%20OpenMapTiles/style.json'),
    }
