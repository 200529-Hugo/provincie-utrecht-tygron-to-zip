# ScenarioDossier

Werkend prototype voor duurzame dossiervorming van scenario's uit een Tygron Digital Twin. De browserinterface kan een project uit het Tygron-domein selecteren, tijdelijk starten, exporteren en weer sluiten. Ook een al actieve sessie en volledig offline demonstratiedata worden ondersteund. Overlays, alerts, indicatoren en measures worden verpakt in één controleerbaar GIS-dossier.

## Snel starten

Alleen Python 3.11+ is nodig; er zijn geen externe packages.

```bash
python3 app.py
```

Open daarna <http://127.0.0.1:8080>. Kies **Demonstratie**, selecteer een project en scenario, controleer de samenvatting en maak het dossier. Een bestaand ZIP-dossier kan onafhankelijk worden gecontroleerd via <http://127.0.0.1:8080/controle>.

Tests uitvoeren:

```bash
python3 -m unittest discover -s tests -v
```

## Interactieve kaart en OpenMapTiles

Stap 2 toont ruimtelijke measures en alerts op een interactieve kaart. De kaart zoomt naar de geselecteerde objecten, biedt afzonderlijke laagknoppen en toont broninformatie in een popup. Een doorzoekbare lijst laat ieder overlay-, indicator-, measure- en alertrecord afzonderlijk opnemen of uitsluiten; de kaart en ZIP-export volgen dezelfde selectie. MapLibre en alle bijbehorende browserbestanden staan lokaal in `static/vendor`; de scenario-objecten blijven daarom ook zonder internet of actieve basiskaart zichtbaar.

OpenMapTiles is optioneel en wordt niet samen met ScenarioDossier geïnstalleerd. Voor een nieuwe installatie zijn Docker, Docker Compose, Git, Make en voldoende schijfruimte nodig. De volledige installatie vanaf een schone computer, inclusief een compacte Utrecht-extract, staat in [docs/WERKINSTRUCTIE.md](docs/WERKINSTRUCTIE.md#lokale-openmaptiles-basiskaart-installeren).

Als OpenMapTiles al is ingericht, zoekt ScenarioDossier standaard naar deze stijl:

```text
http://127.0.0.1:8081/styles/OSM%20OpenMapTiles/style.json
```

De afwijkende poort voorkomt een conflict met ScenarioDossier op poort 8080. Vanuit een installatie naast de projectmap start je de tileserver in een tweede terminal:

```bash
cd ../openmaptiles
TPORT=8081 make start-tileserver
```

De tileserver leest `../openmaptiles/data/tiles.mbtiles`. Voor Nederlandse projecten zijn tegels nodig waarvan de begrenzing het projectgebied omvat. De kaart vergelijkt de scenario-geometrie met de `bounds` uit TileJSON en meldt **Basiskaart dekt gebied niet** als die niet overeenkomen. Genereer in dat geval een nieuwe tegelset voor het benodigde gebied. Een andere style-URL kan zonder codewijziging worden ingesteld:

```bash
OPENMAPTILES_STYLE_URL="http://kaartserver:8081/styles/eigen-stijl/style.json" python3 app.py
```

Wanneer de server niet bereikbaar is, meldt de interface **Basiskaart niet actief** en gebruikt zij automatisch een neutrale achtergrond. Measures en alerts blijven dan raadpleegbaar.

## Tygron-project selecteren

1. Kies **Tygron-project**.
2. Vul Tygron-URL, gebruikersnaam en login key in. Vul het domein in of laat dit leeg om het uit het account te lezen.
3. Kies **Projecten laden** en selecteer het project en de actieve projectversie.
4. Kies **Verbinding controleren**, controleer de inhoud en maak het dossier.

De toepassing gebruikt de root-API om startbare projecten te lezen. Voor controle en export wordt het gekozen project tijdelijk in editormodus gestart en gejoint. De tijdelijke sessie wordt daarna gesloten. Gebruikersnaam, login key en sessietokens worden niet opgeslagen of gearchiveerd.

## Al actieve Tygron-sessie

1. Open het project in de Tygron Editor.
2. Ga naar **Tools > API Overview** en kopieer het API-token.
3. Kies in ScenarioDossier **Tygron-sessie**, vul de sessie-URL (standaard `https://engine.tygron.com`) en het token in.
4. Geef project- en scenarionaam op. Deze namen worden als dossiercontext vastgelegd; het token zelf wordt nooit opgeslagen.
5. Klik op **Verbinding controleren** en daarna op **Dossier maken**.

Een API-token geeft vergaande toegang tot de actieve sessie. Deel het niet en sluit de sessie na gebruik. Live-export vraagt overlays en indicatoren als JSON en measures als GeoJSON in EPSG:4326 op. Alerts worden samengesteld uit waarschuwingvelden en Tygron-panels met een `ATTENTION`-attribuut. Waar beschikbaar worden GeoTIFF-overlays opgehaald. Een mislukte optionele rasterdownload blokkeert het dossier niet, maar wordt in de exportlog vermeld.

## Inhoud van een dossier

```text
project_scenario_YYYYMMDDTHHMMSSZ.zip
├── README.txt
├── metadata/
│   ├── dossier.json
│   ├── exportlog.json
│   ├── validatierapport.json
│   └── manifest-sha256.txt
├── rapport/
│   └── dossierrapport.html
├── bron/
│   ├── overlays.json
│   ├── indicators.json
│   ├── measures.json
│   └── alerts.json
├── gis/
│   ├── scenario.gpkg
│   ├── measures.geojson
│   └── alerts.geojson
├── tabellen/
│   ├── overlays.csv
│   ├── indicators.csv
│   ├── measures.csv
│   └── alerts.csv
└── rasters/                 # indien beschikbaar in Tygron
```

Het GeoPackage bevat de tabellen `overlays`, `indicators`, `measures` en `alerts`. Ruimtelijke records krijgen geometrie in EPSG:4326; niet-ruimtelijke records blijven als gewone tabellen beschikbaar. GeoJSON is toegevoegd voor brede uitwisselbaarheid en CSV voor snelle inspectie. Het zelfstandige HTML-rapport toont het dossierpaspoort, de besluitvorming en de belangrijkste inhoud zonder GIS-software. Het validatierapport controleert structuur en aantallen vóór oplevering; het SHA-256-manifest maakt latere integriteitscontrole mogelijk.

## Dossierpaspoort en controle

In stap 2 kan onder **Dossierpaspoort** gestructureerde overdrachtsmetadata worden vastgelegd: referentie, eigenaar, opsteller, besluitdatum en -status, alternatieven, classificatie en bewaartermijn. Deze gegevens komen zowel in `metadata/dossier.json` als in `rapport/dossierrapport.html`.

De pagina **Dossier controleren** accepteert een eerder geëxporteerd ZIP-bestand van maximaal 200 MB. De server pakt dit tijdelijk en padveilig uit, controleert de dossierstructuur, het GeoPackage, recordaantallen, rapport en iedere SHA-256-hash en verwijdert de tijdelijke inhoud daarna. Het oorspronkelijke ZIP-bestand wordt niet gewijzigd of opgeslagen.

Zie [docs/WERKINSTRUCTIE.md](docs/WERKINSTRUCTIE.md) voor QGIS/ArcGIS-gebruik, [docs/ZIP_PROCES.md](docs/ZIP_PROCES.md) voor de technische opbouw van het ZIP-dossier, [docs/BPMN.md](docs/BPMN.md) voor het BPMN-procesmodel, [docs/ONTWERP.md](docs/ONTWERP.md) voor ontwerpkeuzes en [docs/ACCEPTATIETEST.md](docs/ACCEPTATIETEST.md) voor de formele opleverproef met een echt Tygron-project.

## Privacy en beheer

- API-tokens worden alleen in het geheugen gebruikt en niet gelogd of gearchiveerd.
- Exports staan lokaal in `exports/`; regel bewaartermijnen en toegangsrechten organisatorisch in.
- De demo is fictief en bevat geen persoonsgegevens.
- Voor productie: plaats authenticatie vóór de webapp, gebruik HTTPS, schrijf naar een beheerd DMS/object store en sluit aan op provinciale selectielijsten en metadatastandaarden.

## Bronnen

- [Tygron API tutorial](https://support.tygron.com/wiki/API_tutorial)
- [Tygron API Overview](https://support.tygron.com/wiki/API_Overview)
- [Tygron overlays endpoint](https://support.tygron.com/wiki/Api_session_items_overlays)
- [Tygron indicators endpoint](https://support.tygron.com/wiki/Api_session_items_indicators)
- [Tygron measures endpoint](https://support.tygron.com/wiki/Api_session_items_measures)
