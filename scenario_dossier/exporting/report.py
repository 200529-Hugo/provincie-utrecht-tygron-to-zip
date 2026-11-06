"""Bereid rapportgegevens voor en render de los aanpasbare HTML-template."""

from functools import lru_cache
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from ..config import ROOT
from .data import properties


@lru_cache(maxsize=1)
def _environment():
    environment = Environment(
        loader=FileSystemLoader(ROOT / 'templates' / 'reports'),
        autoescape=True,
        undefined=StrictUndefined,
    )
    environment.filters['display_value'] = lambda item: str(item or '').strip() or 'Niet vastgelegd'
    return environment


def _table_rows(items):
    rows = []
    for item in items:
        values = properties(item)
        rows.append({
            'name': str(values.get('name', values.get('shortName', values.get('id', 'Onbenoemd')))),
            'value': str(values.get('value', values.get('currentValue', values.get('status', '')))),
            'unit': str(values.get('unit', '')),
            'description': str(values.get('description', values.get('warnings', ''))),
        })
    return rows


def _report_table(items, empty):
    table = _environment().get_template('components/table.html').module.report_table
    return str(table(_table_rows(items), empty))


def _report_html(metadata, data, warnings):
    return _environment().get_template('dossier.html').render(
        metadata=metadata,
        record=metadata['record'],
        decision=metadata['decision'],
        components=metadata['components'],
        component_labels={'overlays': 'overlays', 'indicators': 'indicatoren',
                          'measures': 'maatregelen', 'alerts': 'alerts'},
        tables={name: _table_rows(items) for name, items in data.items()},
        warnings=warnings,
    )
