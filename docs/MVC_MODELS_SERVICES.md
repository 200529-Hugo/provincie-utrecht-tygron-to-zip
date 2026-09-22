# Overdracht modellen en services

## Doel

De backend wordt geschikt gemaakt voor een Flask-applicatie met een MVC-indeling. De modellen en services bevatten
geen Flask-routes, requestobjecten, templates of HTML. Daardoor kan de controllerlaag deze code gebruiken zonder dat de
domeinlogica afhankelijk wordt van Flask.

## Mappenstructuur

```text
scenario_dossier/
├── models/
│   ├── auth/
│   │   ├── active_session_credentials.py
│   │   └── project_credentials.py
│   ├── dossier/
│   │   ├── archive_result.py
│   │   ├── dossier_details.py
│   │   └── validation_result.py
│   ├── project/
│   │   ├── project.py
│   │   └── tygron_project.py
│   ├── scenario/
│   │   ├── component_type.py
│   │   ├── scenario.py
│   │   ├── scenario_data.py
│   │   └── scenario_item.py
│   └── tygron/
│       ├── tygron_connection.py
│       └── tygron_fetch_result.py
└── services/
    ├── demo_service.py
    ├── dossier_service.py
    ├── scenario_service.py
    ├── tygron_service.py
    └── validation_service.py
```

Ieder model staat in een eigen bestand en in een map die bij het domein hoort. De bestanden `__init__.py` bieden korte
imports aan voor controllers en tests.

## Verantwoordelijkheden

### Modellen

- `Project` bevat een project met scenario's.
- `Scenario` bevat de naam, omschrijving en `ScenarioData`.
- `ScenarioData` bevat overlays, indicatoren, measures en alerts.
- `ScenarioItem` is een leesbaar inventarisitem voor selectie in een controller.
- `DossierDetails` bevat de overdrachts- en besluitmetadata.
- `ArchiveResult` bevat het pad en de metadata van een export.
- `ValidationResult` bevat de uitslag en controles van een dossier.
- De Tygron-modellen bevatten invoergegevens en resultaten zonder tokens te serialiseren.

### Services

- `DemoService` leest de demonstratieprojecten en zoekt projecten en scenario's.
- `ScenarioService` maakt een inventaris en filtert geselecteerde onderdelen.
- `TygronService` leest projecten, actieve sessies en tijdelijk geopende projecten.
- `DossierService` maakt een ZIP-dossier.
- `ValidationService` controleert een ZIP-dossier of uitgepakte dossiermap.

## Voorbeeld voor een controller

```python
from pathlib import Path

from scenario_dossier.models import DossierDetails
from scenario_dossier.services import DemoService, DossierService, ScenarioService

demo_service = DemoService()
scenario_service = ScenarioService()
dossier_service = DossierService(Path("exports"))

scenario = demo_service.get_scenario(project_id, scenario_id)
selected_data = scenario_service.select(
    scenario.data,
    selected_components,
    selected_items,
)
result = dossier_service.create(
    project_name,
    scenario.name,
    selected_data,
    notes=notes,
    details=DossierDetails.from_dict(form_data),
)
```

De controller vertaalt een request naar modelwaarden en vertaalt het resultaat daarna naar JSON, een redirect of een
downloadresponse. De service kent het request en de response niet.

## Tijdelijk Tygron-project

Gebruik de contextmanager van `TygronService` om te garanderen dat een tijdelijk geopend Tygron-project weer wordt
gesloten.

```python
with tygron_service.project_connection(credentials, file_name) as connection:
    result = dossier_service.create(
        project_name,
        scenario_name,
        connection.data,
        source="tygron_project",
        warnings=connection.warnings,
        raster_fetcher=connection.raster_fetcher,
    )
```

De controller mag een login key of API-token nooit in een sessiecookie, logregel, database of export opslaan.

## Foutafhandeling

De services geven `ValueError`, `LookupError` of `TygronError` door. De controller bepaalt welke HTTP-status en welke
gebruikersmelding daarbij horen. Een aanbevolen vertaling is:

| Fout | HTTP-status |
|------|-------------|
| `ValueError` | 400 |
| `LookupError` | 404 |
| `TygronError` | 502 |
| Onverwachte fout | 500 |

## Testen

```bash
python3 -m unittest discover -s tests -v
```

De servicetests gebruiken geen Flask testclient. De controllerstudent kan daar later afzonderlijke routetests naast
plaatsen.
