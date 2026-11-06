# API-modellen

Dit overzicht wordt opgebouwd uit de modellen die de routes werkelijk gebruiken.
Werk het bij met `.venv/bin/python scripts/generate_api_models.py`.

GET-verzoeken hebben geen JSON-body. Hun requestmodel beschrijft pad- en querywaarden.
Uploads en downloads gebruiken bytes. Afbeeldingen kunnen leeg zijn met HTTP 204.

Alle fouten gebruiken `ErrorResponse` met het veld `error`.

| Methode | URL                                | Payloadmodel                                                                   | Antwoordmodel                                                                    |
|---------|------------------------------------|--------------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| POST    | `/api/auth/login`                  | [LoginRequest](../scenario_dossier/models/api/requests/auth.py)                | [LoginResponse](../scenario_dossier/models/api/responses/auth.py)                |
| POST    | `/api/auth/logout`                 | [LogoutRequest](../scenario_dossier/models/api/requests/auth.py)               | [LogoutResponse](../scenario_dossier/models/api/responses/auth.py)               |
| GET     | `/api/auth/session`                | [SessionStatusRequest](../scenario_dossier/models/api/requests/auth.py)        | [SessionStatusResponse](../scenario_dossier/models/api/responses/auth.py)        |
| GET     | `/api/demo`                        | [DemoCatalogRequest](../scenario_dossier/models/api/requests/projects.py)      | [DemoCatalogResponse](../scenario_dossier/models/api/responses/projects.py)      |
| GET     | `/api/demo/projects`               | [DemoProjectsRequest](../scenario_dossier/models/api/requests/projects.py)     | [DemoProjectsResponse](../scenario_dossier/models/api/responses/projects.py)     |
| GET     | `/api/demo/scenarios/<project_id>` | [DemoScenariosRequest](../scenario_dossier/models/api/requests/projects.py)    | [DemoScenariosResponse](../scenario_dossier/models/api/responses/projects.py)    |
| GET     | `/api/demo/thumbnail/<project_id>` | [DemoThumbnailRequest](../scenario_dossier/models/api/requests/projects.py)    | [DemoThumbnailResponse](../scenario_dossier/models/api/responses/projects.py)    |
| GET     | `/api/download/<name>`             | [DownloadRequest](../scenario_dossier/models/api/requests/files.py)            | [DownloadResponse](../scenario_dossier/models/api/responses/files.py)            |
| POST    | `/api/export`                      | [ExportRequest](../scenario_dossier/models/api/requests/workflow.py)           | [ExportResponse](../scenario_dossier/models/api/responses/workflow.py)           |
| POST    | `/api/inspect`                     | [InspectRequest](../scenario_dossier/models/api/requests/workflow.py)          | [InspectResponse](../scenario_dossier/models/api/responses/workflow.py)          |
| GET     | `/api/map-config`                  | [MapConfigRequest](../scenario_dossier/models/api/requests/settings.py)        | [MapConfigResponse](../scenario_dossier/models/api/responses/settings.py)        |
| GET     | `/api/translations/<language>`     | [TranslationsRequest](../scenario_dossier/models/api/requests/settings.py)     | [TranslationsResponse](../scenario_dossier/models/api/responses/settings.py)     |
| GET     | `/api/tygron/projects`             | [AccountProjectsRequest](../scenario_dossier/models/api/requests/projects.py)  | [ProjectsResponse](../scenario_dossier/models/api/responses/projects.py)         |
| POST    | `/api/tygron/projects`             | [LegacyProjectsRequest](../scenario_dossier/models/api/requests/projects.py)   | [ProjectsResponse](../scenario_dossier/models/api/responses/projects.py)         |
| POST    | `/api/tygron/thumbnail`            | [ProjectThumbnailRequest](../scenario_dossier/models/api/requests/projects.py) | [ProjectThumbnailResponse](../scenario_dossier/models/api/responses/projects.py) |
| POST    | `/api/validate`                    | [ValidateArchiveRequest](../scenario_dossier/models/api/requests/files.py)     | [ValidateArchiveResponse](../scenario_dossier/models/api/responses/files.py)     |
| GET     | `/api/werkinstructie`              | [ManualRequest](../scenario_dossier/models/api/requests/settings.py)           | [ManualResponse](../scenario_dossier/models/api/responses/settings.py)           |

## Payloads

### AccountProjectsRequest

Bron: [AccountProjectsRequest](../scenario_dossier/models/api/requests/projects.py).

| Veld        | Type         | Standaardwaarde |
|-------------|--------------|-----------------|
| Geen velden | Leeg verzoek | `{}`            |

### DemoCatalogRequest

Bron: [DemoCatalogRequest](../scenario_dossier/models/api/requests/projects.py).

| Veld        | Type         | Standaardwaarde |
|-------------|--------------|-----------------|
| Geen velden | Leeg verzoek | `{}`            |

### DemoProjectsRequest

Bron: [DemoProjectsRequest](../scenario_dossier/models/api/requests/projects.py).

| Veld        | Type         | Standaardwaarde |
|-------------|--------------|-----------------|
| Geen velden | Leeg verzoek | `{}`            |

### DemoScenariosRequest

Bron: [DemoScenariosRequest](../scenario_dossier/models/api/requests/projects.py).

| Veld         | Type     | Standaardwaarde |
|--------------|----------|-----------------|
| `project_id` | `string` | `verplicht`     |

### DemoThumbnailRequest

Bron: [DemoThumbnailRequest](../scenario_dossier/models/api/requests/projects.py).

| Veld         | Type     | Standaardwaarde |
|--------------|----------|-----------------|
| `project_id` | `string` | `verplicht`     |

### DossierDetails

Bron: [DossierDetails](../scenario_dossier/models/dossier/dossier_details.py).

| Veld               | Type     | Standaardwaarde |
|--------------------|----------|-----------------|
| `reference`        | `string` | `''`            |
| `owner`            | `string` | `''`            |
| `author`           | `string` | `''`            |
| `decision_date`    | `string` | `''`            |
| `decision_status`  | `string` | `''`            |
| `alternatives`     | `string` | `''`            |
| `classification`   | `string` | `''`            |
| `retention_period` | `string` | `''`            |

### DownloadRequest

Bron: [DownloadRequest](../scenario_dossier/models/api/requests/files.py).

| Veld   | Type     | Standaardwaarde |
|--------|----------|-----------------|
| `name` | `string` | `verplicht`     |

### ExportRequest

Bron: [ExportRequest](../scenario_dossier/models/api/requests/workflow.py).

| Veld             | Type                            | Standaardwaarde    |
|------------------|---------------------------------|--------------------|
| `source`         | `string`                        | `'demo'`           |
| `project_id`     | `string`                        | `''`               |
| `scenario_id`    | `string`                        | `''`               |
| `base_url`       | `string`                        | `''`               |
| `token`          | `string`                        | `''`               |
| `username`       | `string`                        | `''`               |
| `login_key`      | `string`                        | `''`               |
| `domain`         | `string`                        | `''`               |
| `project_file`   | `string`                        | `''`               |
| `project_name`   | `string`                        | `''`               |
| `scenario_name`  | `string`                        | `''`               |
| `authenticated`  | `boolean`                       | `False`            |
| `notes`          | `string`                        | `''`               |
| `dossier`        | `DossierDetails`                | `DossierDetails()` |
| `components`     | `(Array<string>                 | null)`             | `None` |
| `selected_items` | `(Object<string, Array<string>> | null)`             | `None` |
| `rasters`        | `boolean`                       | `True`             |

### InspectRequest

Bron: [InspectRequest](../scenario_dossier/models/api/requests/workflow.py).

| Veld            | Type      | Standaardwaarde |
|-----------------|-----------|-----------------|
| `source`        | `string`  | `'demo'`        |
| `project_id`    | `string`  | `''`            |
| `scenario_id`   | `string`  | `''`            |
| `base_url`      | `string`  | `''`            |
| `token`         | `string`  | `''`            |
| `username`      | `string`  | `''`            |
| `login_key`     | `string`  | `''`            |
| `domain`        | `string`  | `''`            |
| `project_file`  | `string`  | `''`            |
| `project_name`  | `string`  | `''`            |
| `scenario_name` | `string`  | `''`            |
| `authenticated` | `boolean` | `False`         |

### LegacyProjectsRequest

Bron: [LegacyProjectsRequest](../scenario_dossier/models/api/requests/projects.py).

| Veld        | Type     | Standaardwaarde |
|-------------|----------|-----------------|
| `base_url`  | `string` | `verplicht`     |
| `username`  | `string` | `verplicht`     |
| `login_key` | `string` | `verplicht`     |
| `domain`    | `string` | `''`            |

### LoginRequest

Bron: [LoginRequest](../scenario_dossier/models/api/requests/auth.py).

| Veld       | Type     | Standaardwaarde               |
|------------|----------|-------------------------------|
| `username` | `string` | `verplicht`                   |
| `password` | `string` | `verplicht`                   |
| `base_url` | `string` | `'https://engine.tygron.com'` |
| `domain`   | `string` | `''`                          |

### LogoutRequest

Bron: [LogoutRequest](../scenario_dossier/models/api/requests/auth.py).

| Veld        | Type         | Standaardwaarde |
|-------------|--------------|-----------------|
| Geen velden | Leeg verzoek | `{}`            |

### ManualRequest

Bron: [ManualRequest](../scenario_dossier/models/api/requests/settings.py).

| Veld        | Type         | Standaardwaarde |
|-------------|--------------|-----------------|
| Geen velden | Leeg verzoek | `{}`            |

### MapConfigRequest

Bron: [MapConfigRequest](../scenario_dossier/models/api/requests/settings.py).

| Veld        | Type         | Standaardwaarde |
|-------------|--------------|-----------------|
| Geen velden | Leeg verzoek | `{}`            |

### ProjectThumbnailRequest

Bron: [ProjectThumbnailRequest](../scenario_dossier/models/api/requests/projects.py).

| Veld           | Type     | Standaardwaarde |
|----------------|----------|-----------------|
| `project_file` | `string` | `verplicht`     |

### SessionStatusRequest

Bron: [SessionStatusRequest](../scenario_dossier/models/api/requests/auth.py).

| Veld        | Type         | Standaardwaarde |
|-------------|--------------|-----------------|
| Geen velden | Leeg verzoek | `{}`            |

### TranslationsRequest

Bron: [TranslationsRequest](../scenario_dossier/models/api/requests/settings.py).

| Veld       | Type     | Standaardwaarde |
|------------|----------|-----------------|
| `language` | `string` | `verplicht`     |

### ValidateArchiveRequest

Bron: [ValidateArchiveRequest](../scenario_dossier/models/api/requests/files.py).

HTTP-inhoud: `Blob`.

## Antwoorden

### ArchiveSummaryResponse

Bron: [ArchiveSummaryResponse](../scenario_dossier/models/api/responses/workflow.py).

| Veld             | Type                       | Standaardwaarde |
|------------------|----------------------------|-----------------|
| `schema`         | `string`                   | `verplicht`     |
| `project`        | `string`                   | `verplicht`     |
| `scenario`       | `string`                   | `verplicht`     |
| `exported_at`    | `string`                   | `verplicht`     |
| `source`         | `string`                   | `verplicht`     |
| `crs`            | `string`                   | `verplicht`     |
| `components`     | `ComponentCountsResponse`  | `verplicht`     |
| `notes`          | `string`                   | `verplicht`     |
| `record`         | `RecordMetadataResponse`   | `verplicht`     |
| `decision`       | `DecisionMetadataResponse` | `verplicht`     |
| `software`       | `string`                   | `verplicht`     |
| `token_archived` | `boolean`                  | `verplicht`     |
| `warnings`       | `Array<string>`            | `verplicht`     |
| `validation`     | `string`                   | `verplicht`     |
| `size`           | `number`                   | `verplicht`     |

### ComponentCountsResponse

Bron: [ComponentCountsResponse](../scenario_dossier/models/api/responses/workflow.py).

| Veld         | Type     | Standaardwaarde |
|--------------|----------|-----------------|
| `overlays`   | `number` | `verplicht`     |
| `indicators` | `number` | `verplicht`     |
| `measures`   | `number` | `verplicht`     |
| `alerts`     | `number` | `verplicht`     |

### DecisionMetadataResponse

Bron: [DecisionMetadataResponse](../scenario_dossier/models/api/responses/workflow.py).

| Veld                | Type     | Standaardwaarde |
|---------------------|----------|-----------------|
| `date`              | `string` | `verplicht`     |
| `status`            | `string` | `verplicht`     |
| `selected_scenario` | `string` | `verplicht`     |
| `alternatives`      | `string` | `verplicht`     |
| `rationale`         | `string` | `verplicht`     |

### DemoCatalogResponse

Bron: [DemoCatalogResponse](../scenario_dossier/models/api/responses/projects.py).

| Veld       | Type                         | Standaardwaarde |
|------------|------------------------------|-----------------|
| `projects` | `Array<DemoProjectResponse>` | `verplicht`     |

### DemoProjectResponse

Bron: [DemoProjectResponse](../scenario_dossier/models/api/responses/projects.py).

| Veld        | Type                          | Standaardwaarde |
|-------------|-------------------------------|-----------------|
| `id`        | `string`                      | `verplicht`     |
| `name`      | `string`                      | `verplicht`     |
| `scenarios` | `Array<DemoScenarioResponse>` | `verplicht`     |

### DemoProjectsResponse

Bron: [DemoProjectsResponse](../scenario_dossier/models/api/responses/projects.py).

HTTP-inhoud: `Array<DemoProjectResponse>`.

### DemoScenarioResponse

Bron: [DemoScenarioResponse](../scenario_dossier/models/api/responses/projects.py).

| Veld          | Type     | Standaardwaarde |
|---------------|----------|-----------------|
| `id`          | `string` | `verplicht`     |
| `name`        | `string` | `verplicht`     |
| `description` | `string` | `verplicht`     |

### DemoScenariosResponse

Bron: [DemoScenariosResponse](../scenario_dossier/models/api/responses/projects.py).

HTTP-inhoud: `Array<DemoScenarioResponse>`.

### DemoThumbnailResponse

Bron: [DemoThumbnailResponse](../scenario_dossier/models/api/responses/projects.py).

HTTP-inhoud: `(Blob|null)`.

### DownloadResponse

Bron: [DownloadResponse](../scenario_dossier/models/api/responses/files.py).

HTTP-inhoud: `Blob`.

### ErrorResponse

Bron: [ErrorResponse](../scenario_dossier/models/api/responses/common.py).

| Veld    | Type     | Standaardwaarde |
|---------|----------|-----------------|
| `error` | `string` | `verplicht`     |

### ExportResponse

Bron: [ExportResponse](../scenario_dossier/models/api/responses/workflow.py).

| Veld       | Type                     | Standaardwaarde |
|------------|--------------------------|-----------------|
| `filename` | `string`                 | `verplicht`     |
| `download` | `string`                 | `verplicht`     |
| `summary`  | `ArchiveSummaryResponse` | `verplicht`     |
| `ok`       | `boolean`                | `True`          |

### InspectResponse

Bron: [InspectResponse](../scenario_dossier/models/api/responses/workflow.py).

| Veld       | Type                            | Standaardwaarde |
|------------|---------------------------------|-----------------|
| `project`  | `string`                        | `verplicht`     |
| `scenario` | `string`                        | `verplicht`     |
| `counts`   | `ComponentCountsResponse`       | `verplicht`     |
| `spatial`  | `number`                        | `verplicht`     |
| `warnings` | `Array<string>`                 | `verplicht`     |
| `preview`  | `Array<PreviewFeatureResponse>` | `verplicht`     |
| `items`    | `Array<ScenarioItemResponse>`   | `verplicht`     |

### LoginResponse

Bron: [LoginResponse](../scenario_dossier/models/api/responses/auth.py).

| Veld | Type      | Standaardwaarde |
|------|-----------|-----------------|
| `ok` | `boolean` | `True`          |

### LogoutResponse

Bron: [LogoutResponse](../scenario_dossier/models/api/responses/auth.py).

| Veld | Type      | Standaardwaarde |
|------|-----------|-----------------|
| `ok` | `boolean` | `True`          |

### ManualResponse

Bron: [ManualResponse](../scenario_dossier/models/api/responses/settings.py).

HTTP-inhoud: `string`.

### MapConfigResponse

Bron: [MapConfigResponse](../scenario_dossier/models/api/responses/settings.py).

| Veld        | Type     | Standaardwaarde |
|-------------|----------|-----------------|
| `style_url` | `string` | `verplicht`     |

### PreviewFeatureResponse

Bron: [PreviewFeatureResponse](../scenario_dossier/models/api/responses/workflow.py).

| Veld        | Type                | Standaardwaarde |
|-------------|---------------------|-----------------|
| `component` | `string`            | `verplicht`     |
| `key`       | `string`            | `verplicht`     |
| `feature`   | `Object<string, *>` | `verplicht`     |

### ProjectResponse

Bron: [ProjectResponse](../scenario_dossier/models/api/responses/projects.py).

| Veld             | Type            | Standaardwaarde |
|------------------|-----------------|-----------------|
| `file_name`      | `string`        | `verplicht`     |
| `name`           | `string`        | `verplicht`     |
| `active_version` | `number`        | `verplicht`     |
| `versions`       | `Array<string>` | `verplicht`     |
| `description`    | `string`        | `verplicht`     |
| `domain`         | `string`        | `verplicht`     |
| `revision`       | `string`        | `verplicht`     |

### ProjectThumbnailResponse

Bron: [ProjectThumbnailResponse](../scenario_dossier/models/api/responses/projects.py).

HTTP-inhoud: `(Blob|null)`.

### ProjectsResponse

Bron: [ProjectsResponse](../scenario_dossier/models/api/responses/projects.py).

| Veld       | Type                     | Standaardwaarde |
|------------|--------------------------|-----------------|
| `projects` | `Array<ProjectResponse>` | `verplicht`     |

### RecordMetadataResponse

Bron: [RecordMetadataResponse](../scenario_dossier/models/api/responses/workflow.py).

| Veld               | Type     | Standaardwaarde |
|--------------------|----------|-----------------|
| `reference`        | `string` | `verplicht`     |
| `owner`            | `string` | `verplicht`     |
| `author`           | `string` | `verplicht`     |
| `classification`   | `string` | `verplicht`     |
| `retention_period` | `string` | `verplicht`     |

### ScenarioItemResponse

Bron: [ScenarioItemResponse](../scenario_dossier/models/api/responses/workflow.py).

| Veld            | Type      | Standaardwaarde |
|-----------------|-----------|-----------------|
| `key`           | `string`  | `verplicht`     |
| `component`     | `string`  | `verplicht`     |
| `name`          | `string`  | `verplicht`     |
| `detail`        | `string`  | `verplicht`     |
| `spatial`       | `boolean` | `verplicht`     |
| `geometry_type` | `string`  | `verplicht`     |

### SessionStatusResponse

Bron: [SessionStatusResponse](../scenario_dossier/models/api/responses/auth.py).

| Veld            | Type      | Standaardwaarde |
|-----------------|-----------|-----------------|
| `authenticated` | `boolean` | `verplicht`     |

### TranslationsResponse

Bron: [TranslationsResponse](../scenario_dossier/models/api/responses/settings.py).

HTTP-inhoud: `Object<string, string>`.

### ValidateArchiveResponse

Bron: [ValidateArchiveResponse](../scenario_dossier/models/api/responses/files.py).

| Veld            | Type                             | Standaardwaarde |
|-----------------|----------------------------------|-----------------|
| `schema`        | `string`                         | `verplicht`     |
| `validated_at`  | `string`                         | `verplicht`     |
| `status`        | `string`                         | `verplicht`     |
| `checks_ok`     | `number`                         | `verplicht`     |
| `checks_failed` | `number`                         | `verplicht`     |
| `checks`        | `Array<ValidationCheckResponse>` | `verplicht`     |
| `filename`      | `string`                         | `verplicht`     |
| `archive_size`  | `number`                         | `verplicht`     |
| `project`       | `string`                         | `verplicht`     |
| `scenario`      | `string`                         | `verplicht`     |
| `exported_at`   | `string`                         | `verplicht`     |
| `components`    | `Object<string, number>`         | `verplicht`     |

### ValidationCheckResponse

Bron: [ValidationCheckResponse](../scenario_dossier/models/api/responses/files.py).

| Veld     | Type     | Standaardwaarde |
|----------|----------|-----------------|
| `check`  | `string` | `verplicht`     |
| `status` | `string` | `verplicht`     |
| `detail` | `string` | `verplicht`     |
