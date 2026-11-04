"""Behoud het oude importpad voor scripts die dossiers exporteren.

De implementatie staat per bestandssoort in exporting/.
"""

from .exporting.archive import build_archive
from .exporting.data import COMPONENTS, DOSSIER_FIELDS, feature, geometry, properties, slug
from .exporting.data import _simple, _write_csv, _write_json, _dossier_fields
from .exporting.geopackage import create_geopackage, _wkb, _gpkg_geometry
from .exporting.report import _report_html, _report_table


def load_demo():
    from .services.demo_service import DemoService
    return DemoService().read_data()


__all__ = ['build_archive', 'create_geopackage', 'load_demo', 'slug']
