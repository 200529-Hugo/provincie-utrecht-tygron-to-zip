# Technische overdracht: MVC en services

De applicatie gebruikt Flask voor HTTP en templates. De modellen en services zijn gewone Python-code. Ze gebruiken geen Flask-request, cookie of templateobjecten. Voor praktische wijzigingen is [CODE_WIJZIGEN.md](CODE_WIJZIGEN.md) het startpunt.

## Mappen en verantwoordelijkheden

```text
scenario_dossier/
├── web.py                 Verbindt de onderdelen bij het starten
├── config.py              Instellingen met standaardwaarden
├── routes/                URL’s per onderwerp
├── http/                  Gedeeld lezen, versturen en afhandelen van HTTP
├── controllers/           Toegang controleren en antwoorden samenstellen
├── services/              Projecten openen, selecteren, exporteren en controleren
├── models/
│   ├── api/requests/       Payloads voor de eigen API
│   ├── api/responses/      Publieke antwoorden van de eigen API
│   ├── tygron/api/        Externe Tygron-payloads en antwoorden
│   ├── auth/              Credentials en accountsessie
│   ├── scenario/          Inhoud, inventaris en broncontext
│   ├── project/           Projectmetadata
│   └── dossier/           Dossiergegevens en bestandsresultaten
├── integrations/tygron/   HTTP-transport en omzetting van Tygron-alerts
├── exporting/             JSON/CSV, GeoPackage, rapport en ZIP-opbouw
└── validation.py          Controle van een dossier of ZIP
```

| Onderdeel | Doet wel | Doet niet |
| --- | --- | --- |
| Route | Verbindt URL, payloadmodel, antwoordmodel en controller | Domeinregels of Tygron-aanroepen implementeren |
| HTTP-adapter | Leest JSON of bytes en verstuurt het model | Een project kiezen of een dossier samenstellen |
| Controller | Regelt toegang en vertaalt resultaten naar publieke API-modellen | Eigen HTTP-aanroepen naar Tygron doen |
| Service | Voert domeinhandelingen uit met benoemde modellen | Flask-request of browsercookies uitlezen |
| Model | Beschrijft gegevens en controleert invoervormen | Templates renderen of een sessie openen |
| Integratie | Verstuurt HTTP naar Tygron en leest externe antwoorden | Browserantwoorden bepalen |
| Bestandsproductie | Schrijft één of meer bestandsformaten | Inloggegevens of browserstatus beheren |

`WorkflowService` ontvangt een getypeerd payloadmodel en levert `ScenarioInspection` of `ArchiveResult`. `WorkflowController` maakt daarvan `InspectResponse` of `ExportResponse`. De API-vormgeving blijft zo buiten de bestandsproductie.

## API-contracten

Iedere eigen route gebruikt `api_endpoint` met een request- en responseklasse. De adapter valideert de invoervorm en controleert het type van het teruggegeven model. JSON-antwoorden, bestanden, afbeeldingen en tekst hebben ieder een expliciete representatie.

De volledige lijst staat in [API_MODELLEN.md](API_MODELLEN.md). Dit document en de JavaScript-typebeschrijvingen worden uit de geregistreerde Python-modellen gegenereerd. De bronmodellen staan per onderwerp in `models/api/requests/` en `models/api/responses/`.

De Tygron root-, sessie- en WMS-aanroepen hebben eigen modellen in `models/tygron/api/`. Zie [TYGRON_API_MODELLEN.md](TYGRON_API_MODELLEN.md). Publieke projectantwoorden worden expliciet samengesteld en bevatten geen credentials.

## Gedeelde onderdelen

- De drie bronnen gebruiken dezelfde `WorkflowService`, `ScenarioService` en `DossierService`.
- Projecttoegang wordt gecontroleerd door `ProjectService`.
- `ProjectPreviewService` gebruikt de bestaande begrensde thumbnailcache.
- De twee Tygron-clients delen de HTTP-foutafhandeling in `integrations/tygron/transport.py`.
- Browserverzoeken gebruiken uitsluitend `static/api/client.js`.
- De onderdelenlijst, bronkeuze, dossiergegevens en resultaatweergave staan apart onder `static/workflow/`.
- Export en validatie gebruiken de componentnamen uit `ComponentType`.

## Tijdelijke sessies

Behoud de contextmanager rond een tijdelijk geopend Tygron-project:

```python
with tygron_service.project_connection(credentials, file_name) as connection:
    result = dossier_service.create(
        project_name,
        scenario_name,
        connection.data,
        source='tygron_project',
        warnings=connection.warnings,
        raster_fetcher=connection.raster_fetcher,
    )
```

Een fout bij inspectie, WMS of export verlaat het `with`-blok en sluit de tijdelijke sessie. Een al actieve sessie blijft van de gebruiker en wordt door deze workflow niet gesloten.

## Foutafhandeling

`http/errors.py` geeft alle API-fouten dezelfde JSON-vorm: `ErrorResponse(error=...)`.

| Situatie | HTTP-status |
| --- | --- |
| Verkeerde invoer of niet-bestaande demokeuze | 400 |
| Ongeldige of verlopen toegang | 401 |
| Onbekende URL, download of afgeschermd project | 404 |
| Verkeerd HTTP-inhoudstype | 415 |
| Onverwacht antwoord of netwerkfout van Tygron | 502 |
| Onverwachte interne fout | 500 |

Een ongeldig token van een actieve sessie meldt de fout bij die sessie. Het beëindigt geen los ingelogd account. Foutteksten van Tygron worden niet rechtstreeks naar de browser teruggestuurd.

## Controles

```bash
.venv/bin/python scripts/generate_api_models.py --check
.venv/bin/python -m unittest discover -s tests
```

De tests omvatten domeinmodellen, services, routes, API-contracten, archiefinhoud, tokenafscherming, thumbnails, vertalingen en browserlogica. `tests/test_api_contracts.py` controleert ook dat iedere eigen API-route modellen heeft, gegenereerde bestanden actueel zijn en de eigen comments de afgesproken stijl volgen.

De oude importpaden `http_routes.py` en `exporter.py` blijven als kleine doorverwijzing bestaan. Nieuwe implementatie hoort in de betreffende onderwerpmap.
