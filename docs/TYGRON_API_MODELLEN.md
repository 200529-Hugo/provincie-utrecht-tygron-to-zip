# Modellen voor de externe API’s

Deze modellen beschrijven de aanroepen die de applicatie zelf doet. De eigen browser-API staat
in [API_MODELLEN.md](API_MODELLEN.md). Beide gebruiken aparte modellen, zodat gegevens van Tygron nooit automatisch als
openbaar browserantwoord worden teruggestuurd.

## Tygron root-API

De implementatie staat in `scenario_dossier/tygron.py`. Payloads staan
in [requests/root.py](../scenario_dossier/models/tygron/api/requests/root.py) en antwoorden
in [responses/root.py](../scenario_dossier/models/tygron/api/responses/root.py).

| Methode en pad                                             | Payloadmodel               | Antwoordmodel               | Inhoud van de payload                                     |
|------------------------------------------------------------|----------------------------|-----------------------------|-----------------------------------------------------------|
| POST `/api/event/user/get_my_login_key/?f=JSON`            | `LoginKeyRequest`          | `LoginKeyResponse`          | Lege body                                                 |
| POST `/api/event/user/get_my_user/?f=JSON`                 | `UserRequest`              | `UserResponse`              | Lege body                                                 |
| POST `/api/event/io/get_domain_startable_projects/?f=JSON` | `StartableProjectsRequest` | `StartableProjectsResponse` | Domeinnaam als JSON-tekst                                 |
| POST `/api/event/io/start/?f=JSON`                         | `StartProjectRequest`      | `StartProjectResponse`      | Rol en bestandsnaam als JSON-lijst                        |
| POST `/api/event/io/join/?f=JSON`                          | `JoinSessionRequest`       | `JoinSessionResponse`       | Sessie-ID, rol en clientnaam als JSON-lijst               |
| POST `/api/event/io/close/?f=JSON`                         | `CloseSessionRequest`      | `CloseSessionResponse`      | Sessie-ID, clienttoken en keep-alive-keuze als JSON-lijst |

De modellen bewaren de bestaande wireformaten. Het ene Tygron-event verwacht tekst en een ander event een lijst.
`to_payload()` legt dat verschil vast. Deze waarden zijn geen dictionaries zoals bij de eigen API.

De Authorization-header wordt door de client toegevoegd. Credentials staan niet in de URL. De HTTP-laag weigert
redirects met credentials. Een antwoord met een login key of sessietoken verbergt die waarde in zijn normale
tekstweergave.

`UserResponse` bewaart de uitbreidbare gebruikersinformatie intern en biedt een `domain`-eigenschap.
`StartableProjectsResponse` controleert de lijststructuur. Daarna normaliseert het domeinmodel `TygronProject` de naam,
beschrijving, versies en domeininformatie. De controller kiest expliciet welke metadata openbaar wordt.

## Tygron sessie-API

Payloads staan in [requests/session.py](../scenario_dossier/models/tygron/api/requests/session.py). Antwoorden staan
in [responses/session.py](../scenario_dossier/models/tygron/api/responses/session.py).

| Methode en pad                     | Payloadmodel            | Antwoordmodel            |
|------------------------------------|-------------------------|--------------------------|
| GET `/api/session/items/{name}/`   | `ComponentRequest`      | `ComponentResponse`      |
| GET `/api/session/overlay.geotiff` | `OverlayGeoTiffRequest` | `OverlayGeoTiffResponse` |

`ComponentRequest` bevat de componentnaam, het uitvoerformaat en optioneel het coördinatenstelsel. Het antwoordmodel
accepteert de bestaande lijst- en GeoJSON-vormen en zet beide om naar een lijst van records. Records en
GeoJSON-eigenschappen blijven uitbreidbare brongegevens.

De vier aanroepen voor overlays, indicatoren, maatregelen en panels gebruiken hetzelfde componentmodel. Alleen de
veldwaarden verschillen. De omzetting van waarschuwingen en panels naar dossieralerts staat in
`integrations/tygron/alerts.py`.

## WMS-previews

Payloads staan in [requests/wms.py](../scenario_dossier/models/tygron/api/requests/wms.py). Antwoorden staan
in [responses/wms.py](../scenario_dossier/models/tygron/api/responses/wms.py).

| Methode en verzoek        | Payloadmodel             | Antwoordmodel             |
|---------------------------|--------------------------|---------------------------|
| GET WMS `GetCapabilities` | `WmsCapabilitiesRequest` | `WmsCapabilitiesResponse` |
| GET WMS `GetMap`          | `WmsMapRequest`          | `WmsMapResponse`          |

Het capabilities-antwoordmodel leest een bruikbare projectbegrenzing uit XML. `WmsMapRequest.from_project_bounds()` past
de begrenzing aan de verhouding van de thumbnail aan. Het antwoordmodel controleert de PNG-header en afmetingen. De
bestaande limieten op antwoordgrootte blijven in de requestmodellen staan.

## Kaartserver in de browser

De browser haalt daarnaast een MapLibre-stijl en TileJSON-metadata op. Die aanroepen staan in
`static/api/map-assets.js`. Hun payload- en antwoordtypen staan in `static/api/models/map-assets.js`.

De modellen beschrijven de bron-URL, kaartbronnen en de optionele projectbegrenzing. Dit zijn uitbreidbare bestanden van
de kaartserver. De eigen applicatie controleert of de gebruikte velden aanwezig zijn en houdt de bestaande lege
basiskaart als terugval. Het ophalen van de kaarttegels zelf wordt door de bestaande MapLibre-bibliotheek uitgevoerd.
