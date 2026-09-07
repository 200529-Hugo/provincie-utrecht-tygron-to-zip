# Acceptatietest ScenarioDossier

Gebruik deze checklist voor de formele opleverproef met een representatief Tygron-project. Noteer tester, datum, applicatieversies en afwijkingen in het projectdossier.

## Functionele proef

- [ ] De offline demonstratie kan worden geselecteerd, gecontroleerd en geëxporteerd.
- [ ] De root-API toont de startbare projecten van het bedoelde domein.
- [ ] Het gekozen project wordt gestart, gejoint en na controle of export gesloten.
- [ ] Een bestaande sessie kan met een tijdelijk API-token worden geëxporteerd.
- [ ] Overlays, indicatoren, measures en alerts hebben plausibele aantallen.
- [ ] Besluittoelichting staat ongewijzigd in `metadata/dossier.json`.
- [ ] Dossierpaspoort en besluitgegevens staan gestructureerd in `metadata/dossier.json`.
- [ ] `rapport/dossierrapport.html` opent zonder externe afhankelijkheden en toont de juiste gegevens.
- [ ] Een mislukte optionele rasterdownload staat als waarschuwing in `metadata/exportlog.json`.

## GIS-proef

- [ ] `gis/scenario.gpkg` opent zonder herstelmelding in de beheerde QGIS-versie.
- [ ] De vier tabellen/lagen zijn zichtbaar en aantallen komen overeen met het validatierapport.
- [ ] Ruimtelijke measures en alerts liggen op de verwachte locatie in EPSG:4326.
- [ ] GeoJSON-fallbackbestanden openen in QGIS.
- [ ] Het GeoPackage opent zonder herstelmelding in de beheerde ArcGIS Pro-versie.
- [ ] Eventuele GeoTIFF-bestanden openen en sluiten ruimtelijk aan.

## Archief- en beveiligingsproef

- [ ] `metadata/validatierapport.json` heeft status `goedgekeurd`.
- [ ] Alle hashes uit `metadata/manifest-sha256.txt` valideren.
- [ ] De pagina **Dossier controleren** keurt het originele ZIP-dossier goed.
- [ ] De pagina **Dossier controleren** keurt een bewust gewijzigd testdossier af.
- [ ] Login key en API-tokens komen niet voor in het ZIP-bestand of serverlog.
- [ ] Eigenaar, classificatie, bewaartermijn, toegangsrechten en definitieve dossierlocatie zijn vastgelegd.
- [ ] Het oorspronkelijke ZIP-bestand blijft ongewijzigd; analyse vindt plaats op een werkkopie.

## Acceptatie

Resultaat: `geaccepteerd / geaccepteerd met bevindingen / afgewezen`

Openstaande bevindingen:

1. 
2. 
