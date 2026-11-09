# ScenarioDossier

Werkend prototype voor duurzame dossiervorming van scenario's uit een Tygron Digital Twin. De browserinterface kan een project uit het Tygron-domein selecteren, tijdelijk starten, exporteren en weer sluiten. Ook een al actieve sessie en volledig offline demonstratiedata worden ondersteund. Overlays, alerts, indicatoren en measures worden verpakt in één controleerbaar GIS-dossier.

## Zelf de code aanpassen

Begin bij [Zelf wijzigingen maken](docs/CODE_WIJZIGEN.md). Die handleiding legt de mappen en de werkwijze uit met voorbeelden voor teksten, instellingen, dossiergegevens en API-aanpassingen. Alle eigen API-routes staan met hun payload- en antwoordmodellen in [API_MODELLEN.md](docs/API_MODELLEN.md). De externe Tygron-aanroepen staan in [TYGRON_API_MODELLEN.md](docs/TYGRON_API_MODELLEN.md).

De code gebruikt MVC met services. Routes, controllers, services, modellen en bestandsproductie hebben aparte mappen. In de browser staan de API-aanroepen onder `static/api/` en de onderdelen van de exportworkflow onder `static/workflow/`. Python-modellen zijn de bron voor de gegenereerde browsertypes en API-documentatie:

**macOS/Linux:**

```bash
.venv/bin/python scripts/generate_api_models.py
.venv/bin/python scripts/generate_api_models.py --check
```

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\python.exe scripts/generate_api_models.py
.\.venv\Scripts\python.exe scripts/generate_api_models.py --check
```

## Snel starten

Python 3.11+ en Flask zijn nodig. Beide startbestanden gebruiken dezelfde Flask-app met MVC en services. Maak een virtuele omgeving en installeer de afhankelijkheden vanuit de projectmap.

**macOS/Linux (terminal):**

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 app.py
```

**Windows (PowerShell):**

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Met de Windows-commando's hierboven hoeft de virtuele omgeving niet te worden geactiveerd; ze werken ook wanneer PowerShell het uitvoeren van activatiescripts blokkeert. Als Python 3.11 niet is geïnstalleerd maar een andere ondersteunde versie (3.12+) wel, gebruik dan bijvoorbeeld `py -3.12` in de eerste opdracht. Controleer met `py --list` welke versies beschikbaar zijn. Installeer Python inclusief de Python Launcher als het commando `py` ontbreekt.

Open daarna <http://127.0.0.1:8080>. Log in met je Tygron-account of kies **Demonstratie openen**, selecteer een project en scenario, controleer de samenvatting en maak het dossier. Een bestaand ZIP-dossier kan onafhankelijk worden gecontroleerd via <http://127.0.0.1:8080/controle>.

Tests uitvoeren:

**macOS/Linux:**

```bash
.venv/bin/python -m unittest discover -s tests -v
```

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Interactieve kaart en OpenMapTiles

Stap 3 toont een ruime onderdelenlijst naast een kaartpreview. Zoek op naam, type of status en filter op categorie, selectie of onderdelen op de kaart. **Resultaten selecteren/wissen** en de groepsvakjes werken alleen op de zichtbare zoek- en filterresultaten. Een hele rij is aanklikbaar; de aparte kaartknop bekijkt een object zonder de selectie te veranderen. **Dossiergegevens** bevat de optionele metadata en toelichting in een eigen tab. De exportknop en selectietelling blijven onderaan bereikbaar. Op kleine schermen is de kaart standaard ingeklapt en gebruikt de lijst gewone paginascroll.

De kaart en ZIP-export volgen dezelfde selectie. De kaart biedt afzonderlijke laagknoppen en toont broninformatie in een popup. MapLibre en alle bijbehorende browserbestanden staan lokaal in `static`; de scenario-objecten blijven daarom ook zonder internet of actieve basiskaart zichtbaar.

OpenMapTiles is optioneel en wordt niet samen met ScenarioDossier geïnstalleerd. Voor een nieuwe installatie zijn Docker, Docker Compose, Git, Make en voldoende schijfruimte nodig. De uitgebreide installatie-instructie, inclusief een compacte Utrecht-extract, staat in [docs/WERKINSTRUCTIE.md](docs/WERKINSTRUCTIE.md#lokale-openmaptiles-basiskaart-installeren).

**Windows:** draai ScenarioDossier rechtstreeks in PowerShell met de instructies hierboven. Voor de OpenMapTiles-tooling is **WSL2 (bijvoorbeeld Ubuntu) met Docker Desktop en ingeschakelde WSL-integratie** de aanbevolen route. Installeer Git en Make binnen WSL en voer de Linux-commando's uit in de WSL-terminal. Zorg dat de `openmaptiles`-map naast de ScenarioDossier-projectmap staat, bij voorkeur beide binnen het WSL-bestandssysteem wanneer je OpenMapTiles bouwt. Controleer met `docker compose version` en `make --version` of de benodigde tooling vanuit WSL beschikbaar is. Een kaartserver in Docker Desktop/WSL is doorgaans via `http://127.0.0.1:8081` bereikbaar vanuit de Windows-browser wanneer poort 8081 is gepubliceerd. De basiskaart is niet verplicht: de applicatie werkt ook zonder OpenMapTiles.

Als OpenMapTiles al is ingericht, zoekt ScenarioDossier standaard naar deze stijl:

```text
http://127.0.0.1:8081/styles/OSM%20OpenMapTiles/style.json
```

De afwijkende poort voorkomt een conflict met ScenarioDossier op poort 8080. Vanuit een installatie naast de projectmap start je de tileserver in een tweede terminal (Linux/macOS of Windows via WSL2):

```bash
cd ../openmaptiles
TPORT=8081 make start-tileserver
```

De tileserver leest `../openmaptiles/data/tiles.mbtiles`. Voor Nederlandse projecten zijn tegels nodig waarvan de begrenzing het projectgebied omvat. De kaart vergelijkt de scenario-geometrie met de `bounds` uit TileJSON en meldt **Basiskaart dekt gebied niet** als die niet overeenkomen. Genereer in dat geval een nieuwe tegelset voor het benodigde gebied. Een andere style-URL kan zonder codewijziging worden ingesteld:

**macOS/Linux:**

```bash
OPENMAPTILES_STYLE_URL="http://kaartserver:8081/styles/eigen-stijl/style.json" python3 app.py
```

**Windows (PowerShell):**

```powershell
$env:OPENMAPTILES_STYLE_URL = "http://kaartserver:8081/styles/eigen-stijl/style.json"
.\.venv\Scripts\python.exe app.py
```

De PowerShell-omgevingsvariabele geldt voor de huidige terminalsessie. Vervang `kaartserver` door `127.0.0.1` als de tileserver op dezelfde computer draait en poort 8081 bereikbaar is.

Wanneer de server niet bereikbaar is, meldt de interface **Basiskaart niet actief** en gebruikt zij automatisch een neutrale achtergrond. Measures en alerts blijven dan raadpleegbaar.

## Inloggen, projecten en taal

De startpagina toont een loginformulier met gebruikersnaam, wachtwoord en een knop om het wachtwoord te tonen. **Verbindingsinstellingen** bevat de Tygron-URL en een optioneel domein. De voortgang bestaat uit vier stappen: **1. Inloggen**, **2. Project kiezen**, **3. Kaart en selectie**, **4. Succes**. Na inloggen verschijnt de doorzoekbare projectlijst. Een project selecteren laadt direct de kaart en exportselectie in stap 3. Na het maken van het dossier verschijnt het downloadscherm in stap 4. Alleen de actieve projectversie wordt geopend; de tijdelijke Tygron-sessie sluit na iedere controle of export.

Authenticatie gebruikt de [officiële Tygron-root-API](https://support.tygron.com/wiki/API_tutorial): HTTP Basic Authentication over HTTPS en `POST /api/event/user/get_my_login_key/?f=JSON`. Het wachtwoord wordt uitsluitend gebruikt om de login key op te halen en wordt daarna uit het formulier gewist. Een bestaande login key kan ook als inloggegeven worden gebruikt. Neem bij accounts met tweestapsverificatie contact op met Tygron Support over API-toegang; deze app voegt geen eigen 2FA-procedure toe.

De browser ontvangt alleen een willekeurige sessie-ID in een HttpOnly/SameSite-cookie. De login key blijft in servergeheugen; sessies verlopen na 30 minuten en worden bij uitloggen ingetrokken. Een serverherstart vereist opnieuw inloggen. De sessieopslag is bedoeld voor één serverproces. Voor HTTPS-deployment: stel `SCENARIO_HTTPS=1` en een vaste geheime `SCENARIO_SECRET_KEY` in. Wachtwoorden, keys en tokens komen niet in exports of API-responses.

**NL / EN** in de header wisselt de taal van alle schermen, de gebruikersmeldingen en de handleiding. Nederlands is standaard. Een taalcookie bewaart de voorkeur; vertalingen staan centraal in `translations/nl.json` en `translations/en.json`, met Nederlandse fallback. Namen en inhoud uit Tygron en het ZIP-dossierformaat blijven brongegevens. Wisselen van taal werkt direct en behoudt formulierwaarden, de selectie en een lopende workflow.

Bij normaal inloggen en via **Demonstratie openen** is stap 2 het dashboard **Projecten**. Een projectrij selecteren opent stap 3 met de kaart en inhoudselectie; in de demo blijft het scenario daar wisselbaar. **Dossier maken** gaat voor ingelogde gebruikers naar het projectenoverzicht. De bestaande handmatige login-key-route blijft beschikbaar via **Een login key gebruiken** op het projectenoverzicht (`/workflow?mode=legacy`). De route voor een actieve sessie en de offline demo zijn ook zonder login beschikbaar.

**Een actieve sessie gebruiken** (`/workflow?mode=tygron`) heeft een eigen pagina met alleen sessie-URL, API-token, projectnaam en scenarionaam. Deze pagina laadt geen democatalogus en toont geen bronkeuzetabs. Na controle gebruikt hij dezelfde kaart, selectie en export als de overige routes. Teruggaan naar de sessie behoudt de ingevulde waarden. Een ongeldig sessietoken geeft een fout bij het formulier en meldt een eventueel ingelogd account niet af.

## 2D-projectthumbnails

Projectrijen laden een 2D-kaartafbeelding zodra ze in beeld komen. Tygron-thumbnails gebruiken de officiële [WMS](https://support.tygron.com/wiki/WMS)-achtergrondlaag `TOPOGRAPHIC` en een PNG van 320 × 200 pixels. De server leest de projectbegrenzing uit `GetCapabilities`; sessietokens gaan uitsluitend mee in de Authorization-header en komen niet in de browser of afbeeldings-URL.

De eerste aanvraag opent het project tijdelijk via de bestaande root-client en sluit de gejoinde sessie na afloop, ook bij een WMS-fout. Browser en server laden maximaal **drie thumbnails tegelijk**; een trage afbeelding houdt andere projecten en cachetreffers niet tegen. Dezelfde afbeelding wordt bij gelijktijdige aanvragen maar eenmaal gegenereerd. Bij scrollen of zoeken worden nog niet gestarte aanvragen voor verdwenen rijen verwijderd uit de wachtrij. Preview, inspectie en export delen uitsluitend voor hetzelfde project een slot, zodat verschillende projecten parallel kunnen laden.

De server bewaart maximaal 128 thumbnails gedurende **24 uur**, in het geheugen en in de lokale map `.cache/thumbnails/` (buiten Git en exports). Deze cache overleeft opnieuw inloggen en een serverherstart. Afbeeldingen zijn afgeschermd per Tygron-server, domein en gebruiker; iedere aanvraag controleert eerst de ingelogde sessie en de toegankelijke projectlijst. Een gewijzigde actieve versie of `lastActivity` maakt automatisch een nieuwe cachevermelding. Bestanden hebben gehashte namen en bevatten alleen de afbeelding en het bestandstype, zonder wachtwoorden of tokens. Mislukte previews worden twee minuten in het geheugen onthouden. Thumbnails worden niet in het exportdossier opgenomen.

De eerste thumbnail van een groot, nog niet gecachet project blijft afhankelijk van Tygrons opstart- en WMS-tijd. `THUMBNAIL_CONCURRENCY` (standaard 3, maximaal 6), `THUMBNAIL_LIFETIME` (standaard 86400 seconden) en `THUMBNAIL_CACHE_DIR` zijn configureerbaar via de Flask-appconfiguratie.

De offline demo tekent compacte SVG-kaartafbeeldingen van de aanwezige measures en alerts, zonder externe kaartdienst. Als een thumbnail niet beschikbaar is, blijven de initialen zichtbaar en kan het project gewoon worden geselecteerd. De live WMS-koppeling is met gesimuleerde antwoorden getest; controle met een echt Tygron-account blijft onderdeel van acceptatie.

## Tygron-project selecteren

1. Open **Een login key gebruiken** op het projectenoverzicht (`/workflow?mode=legacy`).
2. Vul Tygron-URL, gebruikersnaam en login key in. Vul het domein in of laat dit leeg om het uit het account te lezen.
3. Kies **Projecten laden** en selecteer het project en de actieve projectversie.
4. Kies **Verbinding controleren**, controleer de inhoud en maak het dossier.

De toepassing gebruikt de root-API om startbare projecten te lezen. Voor controle en export wordt het gekozen project tijdelijk in editormodus gestart en gejoint. De tijdelijke sessie wordt daarna gesloten. Gebruikersnaam, login key en sessietokens worden niet op schijf opgeslagen of gearchiveerd.

## Al actieve Tygron-sessie

1. Open het project in de Tygron Editor.
2. Ga naar **Tools > API Overview** en kopieer het API-token.
3. Kies in ScenarioDossier **Een actieve sessie gebruiken**, vul de sessie-URL (standaard `https://engine.tygron.com`) en het token in.
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

In stap 3 kan onder **Dossierpaspoort** gestructureerde overdrachtsmetadata worden vastgelegd: referentie, eigenaar, opsteller, besluitdatum en -status, alternatieven, classificatie en bewaartermijn. Deze gegevens komen zowel in `metadata/dossier.json` als in `rapport/dossierrapport.html`.

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
