"""Werk browsertypes en API-documentatie bij vanuit de Python-modellen.

Uitvoeren vanaf de projectmap: .venv/bin/python scripts/generate_api_models.py
"""

import sys
import types
from dataclasses import MISSING, fields, is_dataclass
from pathlib import Path
from typing import Any, Union, get_args, get_origin, get_type_hints

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scenario_dossier.http.contracts import API_CONTRACTS
from scenario_dossier.models.api.responses.common import ErrorResponse, FileResponse, ImageResponse, TextResponse
from scenario_dossier.routes import api


def js_type(value):
    origin, arguments = get_origin(value), get_args(value)
    if value is Any:
        return '*'
    if value is type(None):
        return 'null'
    if origin in (Union, types.UnionType):
        return '(' + '|'.join(js_type(item) for item in arguments) + ')'
    if origin is list:
        return f'Array<{js_type(arguments[0])}>'
    if origin is dict:
        return f'Object<{js_type(arguments[0])}, {js_type(arguments[1])}>'
    if origin is tuple:
        return 'Array<number>'
    return {str: 'string', int: 'number', float: 'number', bool: 'boolean', bytes: 'Blob'}.get(value, getattr(value, '__name__', '*'))


def wire_type(model):
    if issubclass(model, ImageResponse):
        return '(Blob|null)'
    if issubclass(model, FileResponse) or hasattr(model, 'from_bytes'):
        return 'Blob'
    if issubclass(model, TextResponse):
        return 'string'
    root = getattr(model, 'root_field', None)
    return js_type(get_type_hints(model)[root]) if root else None


def collect_models(model, found):
    if model in found or not is_dataclass(model):
        return
    found.add(model)
    if wire_type(model) in ('Blob', '(Blob|null)', 'string'):
        return
    for value in get_type_hints(model).values():
        pending = [value]
        while pending:
            item = pending.pop()
            if is_dataclass(item):
                collect_models(item, found)
            pending.extend(get_args(item))


def render_types(models, *, requests=False):
    lines = ['// Gegenereerd vanuit Python-modellen, pas de bronmodellen aan.', '// Opnieuw opbouwen met scripts/generate_api_models.py', '']
    for model in sorted(models, key=lambda value: value.__name__):
        root = wire_type(model)
        if root:
            lines.extend(['/**', f' * @typedef {{{root}}} {model.__name__}', ' */', ''])
            continue
        lines.extend(['/**', f' * @typedef {{Object}} {model.__name__}'])
        hints = get_type_hints(model)
        for item in fields(model):
            optional = requests and (item.default is not MISSING or item.default_factory is not MISSING)
            name = f'[{item.name}]' if optional else item.name
            note = ' Vertrouwelijk, niet loggen.' if not item.repr else ''
            lines.append(f' * @property {{{js_type(hints[item.name])}}} {name}{note}')
        lines.extend([' */', ''])
    lines.append('export {};')
    return '\n'.join(lines) + '\n'


def source_link(model):
    path = model.__module__.replace('.', '/') + '.py'
    return f'[{model.__name__}](../{path})'


def render_docs(requests, responses):
    lines = ['# API-modellen', '',
             'Dit overzicht wordt opgebouwd uit de modellen die de routes werkelijk gebruiken.',
             'Werk het bij met `.venv/bin/python scripts/generate_api_models.py`.', '',
             'GET-verzoeken hebben geen JSON-body. Hun requestmodel beschrijft pad- en querywaarden.',
             'Uploads en downloads gebruiken bytes. Afbeeldingen kunnen leeg zijn met HTTP 204.', '',
             'Alle fouten gebruiken `ErrorResponse` met het veld `error`.', '',
             '| Methode | URL | Payloadmodel | Antwoordmodel |', '| --- | --- | --- | --- |']
    for contract in sorted(API_CONTRACTS, key=lambda item: (item.path, item.method)):
        lines.append(f'| {contract.method} | `{contract.path}` | {source_link(contract.request_model)} | {source_link(contract.response_model)} |')
    for title, models in [('Payloads', requests), ('Antwoorden', responses)]:
        lines.extend(['', f'## {title}', ''])
        for model in sorted(models, key=lambda value: value.__name__):
            lines.extend([f'### {model.__name__}', '', f'Bron: {source_link(model)}.', ''])
            root = wire_type(model)
            if root:
                lines.extend([f'HTTP-inhoud: `{root}`.', ''])
                continue
            lines.extend(['| Veld | Type | Standaardwaarde |', '| --- | --- | --- |'])
            hints = get_type_hints(model)
            for item in fields(model):
                default = 'verplicht'
                if item.default is not MISSING:
                    default = repr(item.default)
                elif item.default_factory is not MISSING:
                    default = item.default_factory.__name__ + '()'
                lines.append(f'| `{item.name}` | `{js_type(hints[item.name])}` | `{default}` |')
            if not fields(model):
                lines.append('| Geen velden | Leeg verzoek | `{}` |')
            lines.append('')
    return '\n'.join(lines)


def generated_files():
    requests, responses = set(), {ErrorResponse}
    for contract in API_CONTRACTS:
        collect_models(contract.request_model, requests)
        collect_models(contract.response_model, responses)
    directory = ROOT / 'static' / 'api' / 'models'
    return {
        directory / 'requests.js': render_types(requests, requests=True),
        directory / 'responses.js': render_types(responses),
        ROOT / 'docs' / 'API_MODELLEN.md': render_docs(requests, responses),
    }


def main():
    files = generated_files()
    if '--check' in sys.argv:
        outdated = [str(path.relative_to(ROOT)) for path, content in files.items()
                    if not path.exists() or path.read_text() != content]
        if outdated:
            raise SystemExit('Werk de API-modellen bij: ' + ', '.join(outdated))
        print('API-documentatie en browsertypes zijn actueel.')
        return
    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
    print(f'{len(API_CONTRACTS)} API-contracten verwerkt.')


if __name__ == '__main__':
    main()
