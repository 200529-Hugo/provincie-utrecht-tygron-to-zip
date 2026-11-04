import json
import re
from pathlib import Path

TRANSLATIONS = Path(__file__).parents[1] / 'translations'
CATALOGS = {language: json.loads((TRANSLATIONS / f'{language}.json').read_text()) for language in ('nl', 'en')}


def translate(message, language='nl', **values):
    text = CATALOGS.get(language, {}).get(message, CATALOGS['nl'].get(message, message))
    return text.format(**values) if values else text


def translate_message(message, language='nl'):
    if language == 'nl' or not isinstance(message, str):
        return message
    direct = CATALOGS['en'].get(message)
    if direct:
        return direct
    for template, translation in CATALOGS['en'].items():
        fields = re.findall(r'\{(\w+)\}', template)
        if not fields:
            continue
        pattern = re.escape(template)
        for name in fields:
            pattern = pattern.replace(re.escape('{' + name + '}'), f'(?P<{name}>.+?)')
        match = re.fullmatch(pattern, message)
        if match:
            return translation.format(**match.groupdict())
    return message
