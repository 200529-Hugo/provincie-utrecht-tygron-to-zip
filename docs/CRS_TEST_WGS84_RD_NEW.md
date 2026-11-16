# ScenarioDossier testen met WGS 84 en RD New

**Voor Sprint Review 4 · 16 november 2026.** De bestaande WGS 84-export ligt correct in een QGIS-project met RD New. Een
in QGIS omgerekende RD-kopie ligt op dezelfde plek. De browser toont de drie objecten na omzetting naar WGS 84. Bij
onbewerkte RD-coördinaten valt de browserkaart weg, terwijl de export en pakketvalidator de ongeldige ligging
accepteren. [Trello #81](https://trello.com/c/okmZSKIp/81) · [Testbestanden](CRS81-testbestanden.zip)

## Opzet

De test gebruikt drie fictieve maatregelen uit **Merwedekanaalzone -> Groen & Gezond 2040**. De bron is GeoJSON met WGS
84 in lengtegraad, breedtegraad. Het QGIS-project gebruikt Amersfoort / RD New, EPSG:28992, met oost- en
noordcoördinaten in meters. De vooraf gekozen tolerantie voor afwijkingen tussen de proefbestanden is **1,00 m per
overeenkomstig hoekpunt**. De WGS 84-broncoördinaten vormen de referentie. Het zijn geen ingemeten
controlepunten. [Demodata](../data/demo.json) · [GeoJSON RFC 7946 §4](https://www.rfc-editor.org/rfc/rfc7946#section-4) · [NSGI overzicht coördinatenstelsels](https://www.nsgi.nl/coordinatenstelsels-en-transformaties/overzicht-coordinatenstelsels)

| Geometrie                                        | Referentie uit WGS 84 (lon, lat) | Berekende referentie in RD New (x, y) | Vergeleken coördinaten |
|--------------------------------------------------|----------------------------------|---------------------------------------|-----------------------:|
| Punt 33 · Buurtzorgpunt                          | 5,1072° · 52,0853°               | 135.808,245 m · 455.263,000 m         |                      1 |
| Lijn 32 · Doorfietsroute, eerste vertex          | 5,0998° · 52,0818°               | 135.299,502 m · 454.875,576 m         |                      3 |
| Vlak 31 · Parklint langs kanaal, eerste ringpunt | 5,1028° · 52,0830°               | 135.505,663 m · 455.008,277 m         |  5 inclusief sluitpunt |

De proef draaide in QGIS 3.44.14 met PROJ 9.8.1. QGIS koos voor `Inverse of Amersfoort to WGS 84 (4) + RD New`. Voor de
browserproef is de RD-geometrie weer naar WGS 84 omgerekend. `referenties.json` bevat de gebruikte pijplijnen en alle
coördinaten. De kleine gemeten verschillen beschrijven de consistentie tussen bestanden bij deze transformatie. Voor
absolute nauwkeurigheid is een aparte veldreferentie
nodig. [QGIS-handleiding over CRS en reproprojectie](https://docs.qgis.org/3.44/en/docs/training_manual/vector_analysis/reproject_transform.html)

## Uitkomsten

| Proef                                               | Uitkomst                                                                                                                                                                                                                                                                                                                                                                               |
|-----------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| WGS 84-nulmeting in Chrome                          | De kaartbediening vond het punt, de lijn en het vlak onder hun eigen naam. Na het deselecteren van de overige onderdelen ging een selectie van drie objecten via **Dossier maken** naar de export. De validator gaf 19/19 geslaagde controles. De GeoJSON-positie van het punt is `[5.1072, 52.0853]`. De GeoPackage-laag en de dossiermetadata vermelden EPSG:4326.                   |
| Hetzelfde GeoPackage in een RD-project              | QGIS opende de WGS 84-laag in een project met EPSG:28992. QGIS projecteerde de objecten tijdens het weergeven. De bronlaag behield EPSG:4326. De grootste afwijking ten opzichte van de berekende RD-referentie bij dezelfde transformatie was 0,000 m.                                                                                                                                |
| GeoPackage met echte RD-coördinaten                 | De QGIS-export schreef het punt, de lijn en het vlak als drie lagen met EPSG:28992 en waarden in meters. De oorspronkelijke `item_id`-waarden en geometrietypes bleven behouden. De grootste afwijking ten opzichte van de RD-referentie was 0,000 m. De zes lagen openden opnieuw vanuit `Utrecht-RD-New.qgz`.                                                                        |
| Browser na omzetting RD -> WGS 84                    | De testkopie van de demo bevatte de drie vooraf omgerekende objecten. In Chrome opende **Kaart** voor elk object de juiste kaartpop-up. De grootste gemeten afwijking in de coördinaten was minder dan 0,00046 m, binnen 1,00 m. Het geëxporteerde dossier bevatte dezelfde drie objecten en haalde 19/19 controles. Beide browsertests liepen met de lokale basiskaart uitgeschakeld. |
| Onbewerkte RD-invoer, drie varianten                | Bij een correct RD-label, een fout WGS 84-label en een ontbrekend label liep de browserkaart vast op `Invalid LngLat latitude value: must be between -90 and 90`. Er is geen openbare invoerroute voor een RD-bestand. De proef bood de varianten aan via een lokale kopie van de demobron.                                                                                            |
| Export en validatie van de drie negatieve varianten | De export accepteerde elk geval. Het dossier kreeg EPSG:4326 terwijl het punt de RD-waarden `[135808.2453308353, 455262.9998146437]` hield. De validator keurde alle drie de archieven goed met 19/19 controles. QGIS las de foutieve GeoPackage-laag als EPSG:4326 met dezelfde waarden in meters.                                                                                    |

## Proef herhalen

1. Pak [het ZIP-bestand met testbestanden](CRS81-testbestanden.zip) uit. Houd `Utrecht-RD-New.qgz` en de twee correcte
   GeoPackages in dezelfde map. Open het QGIS-project. Oranje toont de WGS 84-uitvoer in de projectprojectie. Blauw
   toont de in RD New opgeslagen kopie. Zet de groepen om beurten aan. Bekijk het laag-CRS via **Eigenschappen ->
   Informatie** en vergelijk de referenties met `referenties.json`.
2. Open de reguliere demo en selecteer Parklint langs kanaal, Doorfietsroute en Buurtzorgpunt. Open voor elk object de
   kaart en maak het dossier. Vergelijk `gis/measures.geojson` en `gis/scenario.gpkg` met
   `ScenarioDossier-CRS81-WGS84.zip` uit de testbestanden.
3. Gebruik `demo-crs81.json` met een lokale testinstantie via `start-crs81-demo.py` uit het testpakket. Start vanuit de
   repo met `.venv/bin/python /pad/naar/uitgepakte/testbestanden/start-crs81-demo.py`. Ga naar
   `http://127.0.0.1:54881/projecten?mode=demo` en open Merwedekanaalzone. Kies achtereenvolgens **RD New vooraf omgezet
   naar WGS 84**, **RD New met expliciet EPSG:28992**, **RD New foutief gelabeld als EPSG:4326** en **RD New zonder CRS
   **. Klik steeds op **Kaart** bij Buurtzorgpunt.
4. Klik bij een negatieve variant op **Resultaten deselecteren**, vink alleen de drie testmaatregelen aan en exporteer.
   Open het ZIP-bestand in **Dossier controleren**. Vergelijk het oordeel met de waarden van het punt in
   `gis/measures.geojson` en EPSG:4326 in `metadata/dossier.json`. `scenario-rd-zonder-crs.gpkg` in de testbestanden is
   een eerder gemeten voorbeeld.

## Vervolg voor het bord

**Ongeldige coördinaten vóór export afvangen.** Reproduceer via stap 3 en 4 met de variant **RD New zonder CRS**. De
verwachte uitkomst is een melding met de oorzaak en een geblokkeerde export zodra de coördinaten buiten de geldige WGS
84-grenzen vallen. De pakketvalidator moet bestaande archieven met dezelfde ongeldige waarden afkeuren. Voeg aan beide
controles ook de positieve WGS 84-proef toe. Beslis apart of een expliciete RD-invoerroute onderdeel van het product
moet worden. Die route zou een bekend bron-CRS moeten gebruiken en vóór kaart en export naar WGS 84 moeten
transformeren.

De proef betreft vectorgeometrie en de offline demostroom. Live Tygron-data, rasters en nauwkeurigheid ten opzichte van
ingemeten referentiepunten vielen buiten de gekozen proef.
