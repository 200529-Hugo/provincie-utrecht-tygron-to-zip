"""Reproduceerbare lokale deep-dive, onafhankelijk van een Tygron-account.

Gebruik: python3 docs/hugo/onderzoek_deepdive.py
Dit onderzoek wijzigt de applicatiecode niet. A en B gebruiken een bestaande
GeoPackage-structuur als proefopstelling om de huidige exportregressie te isoleren.
De timings beschrijven deze proefopstelling, niet de productiesnelheid.
"""
from __future__ import annotations

import csv
import hashlib
import json
import platform
import shutil
import sqlite3
import statistics
import subprocess
import sys
import tempfile
import time
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scenario_dossier.exporter import COMPONENTS, _gpkg_geometry, _write_csv, feature, geometry, load_demo, properties
from scenario_dossier.validation import _manifest_status, validate_archive

OUT = ROOT / 'output' / 'onderzoek' / 'deepdive'
BASELINE = ROOT / 'exports' / 'test_hallo_20260905T230247Z.zip'


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def manifest(folder):
    file = folder / 'metadata' / 'manifest-sha256.txt'
    file.parent.mkdir(exist_ok=True)
    lines = [f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(folder).as_posix()}'
             for p in sorted(folder.rglob('*')) if p.is_file() and p != file]
    file.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def mutation_tests():
    outcomes = []
    with tempfile.TemporaryDirectory(prefix='deepdive-integriteit-') as tmp:
        root = Path(tmp)
        for variant in ['origineel', 'waarde_gewijzigd', 'bestand_verwijderd', 'bestand_toegevoegd', 'bestand_en_manifest_gewijzigd', 'verkeerde_waarde_met_nieuw_manifest']:
            folder = root / variant
            with zipfile.ZipFile(BASELINE) as z:
                z.extractall(folder)
            jsonfile = folder / 'bron' / 'indicators.json'
            if variant in ['waarde_gewijzigd', 'bestand_en_manifest_gewijzigd', 'verkeerde_waarde_met_nieuw_manifest']:
                values = json.loads(jsonfile.read_text())
                values[0]['deepdive_marker'] = 'bewust toegevoegd'
                if variant == 'verkeerde_waarde_met_nieuw_manifest':
                    values[0]['value'] = -999999
                write_json(jsonfile, values)
            if variant == 'bestand_verwijderd':
                (folder / 'README.txt').unlink()
            if variant == 'bestand_toegevoegd':
                (folder / 'extra.txt').write_text('proefbestand', encoding='utf-8')
            if variant in ['bestand_en_manifest_gewijzigd', 'verkeerde_waarde_met_nieuw_manifest']:
                manifest(folder)
            archive = root / f'{variant}.zip'
            with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
                for p in sorted(folder.rglob('*')):
                    if p.is_file():
                        z.write(p, p.relative_to(folder))
            report = validate_archive(archive)
            write_json(OUT / 'validatie' / f'{variant}.json', report)
            outcomes.append({'proef': variant, 'status': report['status'], 'checks_ok': report['checks_ok'],
                             'checks_failed': report['checks_failed'], 'manifest': _manifest_status(folder)})
    return outcomes


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    project = load_demo()['projects'][0]
    scenario = project['scenarios'][0]
    selected = {c: [] for c in COMPONENTS}
    for c in ['measures', 'indicators', 'alerts']:
        selected[c] = scenario['data'][c][:1]
    context = {'project': project['id'], 'scenario': scenario['id'], 'crs': 'EPSG:4326',
               'bron': 'synthetische projectdemodata, geen echt Tygron-project'}
    write_json(OUT / 'fixture.json', {'context': context, 'data': selected})
    with zipfile.ZipFile(BASELINE) as z:
        template = z.read('gis/scenario.gpkg')

    def build(kind, folder):
        folder.mkdir(parents=True)
        if kind in ['A', 'B']:
            gpkg = folder / 'scenario.gpkg'
            gpkg.write_bytes(template)
            with sqlite3.connect(gpkg) as con:
                for c in COMPONENTS:
                    con.execute(f'DELETE FROM "{c}"')
                    for item in selected[c]:
                        p = properties(item)
                        vals = [str(p.get('id', '')), str(p.get('name', '')), str(p.get('status', p.get('severity', ''))),
                                str(p.get('value', p.get('currentValue', ''))), str(p.get('unit', '')),
                                str(p.get('description', '')), json.dumps(p, ensure_ascii=False)]
                        # De bestaande referentie heeft alleen measures als ruimtelijke tabel.
                        # De alert wordt voor deze proef expliciet eveneens ruimtelijk geregistreerd.
                        cols = [r[1] for r in con.execute(f'PRAGMA table_info("{c}")')]
                        if geometry(item) and 'geom' not in cols:
                            con.execute(f'ALTER TABLE "{c}" ADD COLUMN geom BLOB')
                            con.execute('UPDATE gpkg_contents SET data_type="features",srs_id=4326 WHERE table_name=?', (c,))
                            con.execute('INSERT OR REPLACE INTO gpkg_geometry_columns VALUES (?,?,?,?,?,?)', (c, 'geom', 'GEOMETRY', 4326, 0, 0))
                            cols.append('geom')
                        fields = 'item_id,name,status,value,unit,description,source_json'
                        if 'geom' in cols:
                            fields += ',geom'
                            vals.append(_gpkg_geometry(geometry(item)) if geometry(item) else None)
                        con.execute(f'INSERT INTO "{c}"({fields}) VALUES ({",".join("?" for _ in vals)})', vals)
                con.execute('CREATE TABLE IF NOT EXISTS deepdive_context (context_json TEXT)')
                con.execute('DELETE FROM deepdive_context')
                con.execute('INSERT INTO deepdive_context VALUES (?)', (json.dumps(context),))
        if kind in ['B', 'C']:
            for c in COMPONENTS:
                write_json(folder / 'bron' / f'{c}.json', selected[c])
            write_json(folder / 'metadata' / 'context.json', context)
        if kind == 'C':
            (folder / 'tabellen').mkdir()
            (folder / 'gis').mkdir()
            for c in COMPONENTS:
                _write_csv(folder / 'tabellen' / f'{c}.csv', selected[c])
                spatial = [feature(i) for i in selected[c] if geometry(i)]
                if spatial:
                    write_json(folder / 'gis' / f'{c}.geojson', {'type': 'FeatureCollection', 'features': spatial})
        if kind in ['B', 'C']:
            manifest(folder)

    outcomes, raw = [], []
    for kind in ['A', 'B', 'C']:
        measured = []
        for run in range(35):
            with tempfile.TemporaryDirectory(prefix='deepdive-meting-') as tmp:
                folder = Path(tmp) / kind
                start = time.perf_counter_ns()
                build(kind, folder)
                archive = Path(tmp) / f'{kind}.zip'
                with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
                    for p in sorted(folder.rglob('*')):
                        if p.is_file():
                            z.write(p, p.relative_to(folder))
                elapsed = (time.perf_counter_ns() - start) / 1e6
                sizes = sum(p.stat().st_size for p in folder.rglob('*') if p.is_file())
                raw.append({'alternatief': kind, 'run': run + 1, 'opwarmrun': run < 5, 'tijd_ms': elapsed,
                            'bytes_uitgepakt': sizes, 'bytes_zip': archive.stat().st_size})
                if run >= 5:
                    measured.append(elapsed)
                if run == 34:
                    shutil.copytree(folder, OUT / 'pakketten' / kind, dirs_exist_ok=True)
                    shutil.copy2(archive, OUT / 'pakketten' / f'{kind}.zip')
                    if kind in ['A', 'B']:
                        checks = []
                        with sqlite3.connect(folder / 'scenario.gpkg') as con:
                            for c in ['measures', 'indicators', 'alerts']:
                                source = selected[c][0]
                                stored = json.loads(con.execute(f'SELECT source_json FROM {c}').fetchone()[0])
                                checks.append(stored == properties(source))
                                if geometry(source):
                                    checks.append(con.execute(f'SELECT geom FROM {c}').fetchone()[0] == _gpkg_geometry(geometry(source)))
                            checks.append(json.loads(con.execute('SELECT context_json FROM deepdive_context').fetchone()[0]) == context)
                        meaning = {'attributen': '3/3 property-dictionaries gelijk',
                                   'geometrie': '2/2 gelijk aan encoding bron', 'context': 'gelijk', 'alle_controles': all(checks)}
                    else:
                        checks = [json.loads((folder / 'bron' / f'{c}.json').read_text()) == selected[c] for c in COMPONENTS]
                        meaning = {'bronobjecten': '3/3 volledig gelijk', 'alle_controles': all(checks)}
                    quantiles = statistics.quantiles(measured, n=4)
                    outcomes.append({'alternatief': kind, 'mediaan_ms': round(statistics.median(measured), 3),
                                     'iqr_ms': round(quantiles[2] - quantiles[0], 3), 'bytes_uitgepakt': sizes,
                                     'bytes_zip': archive.stat().st_size, 'betekenis': meaning})
    with (OUT / 'metingen.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(raw[0]))
        writer.writeheader()
        writer.writerows(raw)

    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'))
    with (OUT / 'projecttests.txt').open('w', encoding='utf-8') as log:
        run = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    mutation = mutation_tests()
    # Een proef op de encoder, geen onderdeel van de 2D-demofixture.
    z_equal = _gpkg_geometry({'type': 'Point', 'coordinates': [5, 52, 10]}) == _gpkg_geometry({'type': 'Point', 'coordinates': [5, 52, 99]})
    ogr = Path('/Applications/QGIS.app/Contents/MacOS/ogrinfo')
    reader = {}
    if ogr.exists():
        r = subprocess.run([str(ogr), '-ro', '-al', '-so', str(OUT / 'pakketten' / 'A' / 'scenario.gpkg')], capture_output=True, text=True)
        (OUT / 'ogrinfo.txt').write_text(r.stdout + r.stderr, encoding='utf-8')
        reader = {'exit_code': r.returncode, 'tool': str(ogr), 'claim': 'GDAL-leesproef, geen QGIS-UI of ArcGIS Pro-test'}
    result = {'datum': '2026-10-28', 'python': sys.version, 'platform': platform.platform(),
              'fixture': context, 'method': 'Bestaande structuur als isolerende proefopstelling, inclusief gedeelde dossiercontext. A behoudt de al aanwezige source_json-kolom. Geen reparatie van applicatiecode.',
              'projecttests': {'methods': run.testsRun, 'errors': len(run.errors), 'failures': len(run.failures), 'successful': run.wasSuccessful()},
              'alternatieven': outcomes, 'integriteitsproeven': mutation, 'encoder_hoogteverlies': z_equal, 'gdal_leesproef': reader,
              'beperkingen': ['Synthetische demodata, drie objecten en één computer', 'Geen QGIS-gebruikersinterfacetest of ArcGIS Pro-test', 'Geen volledige OGC-conformiteitscontrole', 'Timings gelden voor de geïsoleerde proefopstelling, niet de huidige defecte productie-export', 'Gelijke encoding is geen onafhankelijke semantische geometrievalidatie']}
    write_json(OUT / 'resultaten.json', result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
