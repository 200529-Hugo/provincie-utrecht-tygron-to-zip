# Spiekbrief afgeronde deep-dive

Hugo de Heus | 28 oktober 2026

Bij de presentatie `deepdive_gis_dossier_afgerond.pptx`. Steekwoorden om vrij te vertellen, met context bij lastige begrippen. Richttijd: 28 minuten inhoud, maximaal 5 minuten vragen.

## Slide 1. Van Tygron-object naar duurzaam GIS-dossier

- Provincie Utrecht, gebiedsontwikkeling
- Tygron-project eindigt, gemaakte keuzes blijven relevant
- Niet alleen bewaren, ook later begrijpen
- Onderzoek afgerond, resultaten en eindadvies

**Context:** een Digital Twin is een digitale weergave van een gebied waarmee je scenario’s onderzoekt. GIS betekent geografisch informatiesysteem, software voor gegevens met een locatie.

## Slide 2. De centrale onderzoeksvraag

> Van Tygron-object naar duurzaam GIS-dossier: hoe combineer je open formaten, validatie en integriteitscontrole zonder betekenis te verliezen?

- Open formaat: publiek beschreven structuur
- Validatie: controleren tegen afgesproken eisen
- Integriteit: wijzigingen tegenover een vertrouwde referentie herkennen
- Betekenis: locatie, waarde, eenheid en context
- Twee deelvragen: wat blijft behouden, welke controles leveren bewijs?

**Voorbeeld:** getal 12 bewaren is niet genoeg als de eenheid verdwijnt.

## Slide 3. Waarom is dit onderzoek nodig?

- Tygron: afhankelijk van licentie en actief project
- Een kaartvorm vertelt niet het hele verhaal
- Attributen, relaties, scenario en bron
- Bestand opent betekent niet dat inhoud klopt
- Duurzame toegankelijkheid vraagt begrijpelijkheid

**Context:** een attribuut is een eigenschap, zoals naam of kosten. Geometrie is de vorm en locatie, zoals punt of vlak.

## Slide 4. Afbakening: één scenario, drie objecttypen

- Synthetische demo, geen actuele Tygron-projectmeting
- Measure 31: Parklint langs kanaal, vlak, kosten 3.200.000
- Indicator 21: groen binnen 300 meter, 84,2 procent, doel 75
- Alert 41: hittestress schoolplein, punt, ernst hoog
- Zelfde selectie voor alle alternatieven
- Bestaand ZIP-dossier apart gebruikt voor validatorproeven

**Context:** een measure is een ingreep, een indicator een meetwaarde, een alert een waarschuwing. Kleine selectie maakt vergelijking controleerbaar, maar niet representatief voor alle Tygron-objecten.

## Slide 5. Drie alternatieven, dezelfde brondata

- A: alleen GeoPackage, inclusief `source_json` en onderzoekcontext
- B: hetzelfde GeoPackage plus losse bron-JSON, context en manifest
- C: JSON, CSV, ruimtelijke GeoJSON, context en manifest
- Belangrijke ontdekking: A bewaart de geteste extra attributen al
- B dus geen aangetoonde extra betekeniswinst op deze selectie
- B wel makkelijker broninspectie buiten de database

**Begrippen:** GeoPackage is een SQLite-databasebestand voor kaartlagen en gewone tabellen. JSON betekent JavaScript Object Notation en kan geneste gegevens bewaren. CSV betekent Comma-Separated Values, een eenvoudige tabel. GeoJSON is JSON met geografische objecten. Een manifest is hier een bestandenlijst met hashes.

**Afweging:** extra bestanden helpen inspectie, maar vragen opslag en controle op onderlinge afwijkingen.

## Slide 6. Werkwijze: productiepad en geïsoleerde proef

- Eerst bestaande export en projecttests controleren
- Productie-export loopt vast op niet-ruimtelijke tabellen
- Geen geslaagde productie-export claimen
- Geïsoleerde proef met bestaande GeoPackage-structuur
- Huidige omzettingsfuncties, productiecode ongewijzigd
- Selectie, representaties, context, validatie, SHA-256 en ZIP

**Context:** ETL betekent Extract, Transform, Load, oftewel ophalen, omzetten en opslaan. Een geïsoleerde proef helpt het afgebakende vraagstuk beantwoorden, maar bewijst niet dat de hele applicatie werkt.

## Slide 7. Resultaten: betekenisbehoud en verlies

- A en B: attributen 3 van 3 gelijk
- Twee ruimtelijke geometrieën als gecodeerde gegevens gelijk
- C: drie volledige bronobjecten gelijk
- Context expliciet meegegeven
- Extra proef: hoogte 10 en hoogte 99 geven dezelfde geometrieblob
- Dus hoogteverlies bij omzetting naar twee dimensies
- Geen algemene uitspraak over alle relaties en objecttypen

**Begrippen:** CRS betekent Coordinate Reference System, het coördinatenreferentiesysteem. Z is de hoogtecomponent naast X en Y. Een blob is een reeks binaire gegevens.

**Kritisch punt:** dezelfde encoder aan beide kanten maakt de geometrievergelijking niet onafhankelijk. De hoogteproef toont juist een grens die zo’n vergelijking kan missen.

## Slide 8. Uitkomsten: validatie en technische grenzen

- Bestaand dossier: 19 van 19 interne controles goed
- Gewijzigd, ontbrekend en extra bestand afgekeurd
- GDAL 3.13.3 leest de drie geselecteerde objecten
- Projecttests: 11 testmethoden, 9 foutmeldingen inclusief subtests
- Geen actuele Tygron-export als eindbewijs
- Geen QGIS-interface of ArcGIS Pro getest

**Context:** GDAL betekent Geospatial Data Abstraction Library, software voor geografische bestanden. GDAL kan aantonen dat deze lezer de lagen en attributen herkent, niet dat iedere GIS-app hetzelfde toont.

**Niet verwarren:** 9 foutmeldingen is niet hetzelfde als 9 van 11 testmethoden mislukt.

## Slide 9. Zes proeven: wat bewijst het manifest?

1. Origineel: 19 van 19, goedgekeurd
2. JSON-waarde gewijzigd, manifest gelijk: afgekeurd
3. README verwijderd: afgekeurd
4. Extra bestand toegevoegd: afgekeurd
5. JSON gewijzigd én manifest opnieuw berekend: goedgekeurd
6. Indicatorwaarde naar -999999, alleen JSON en manifest aangepast: goedgekeurd

- Proef 6: GeoPackage en JSON spreken elkaar tegen
- Validator vergelijkt die waarden niet inhoudelijk
- Hash correct betekent niet dat de betekenis klopt
- Manifest binnen hetzelfde pakket kan worden vervangen

**Begrippen:** SHA-256 betekent Secure Hash Algorithm met een uitkomst van 256 bits. Een hash is een digitale samenvatting van bestandsbytes. Authenticiteit gaat over herkomst en echtheid, daarvoor is meer nodig dan een intern manifest.

**Kernzin:** integriteitscontrole herkent wijzigingen tegenover een vertrouwde referentie, geen inhoudelijke waarheid.

## Slide 10. Betrouwbaarheid en bronnen

- OGC: afspraken van het formaat
- Nationaal Archief: duurzaam toegankelijk en begrijpelijk
- GDAL: concrete lezer en mogelijkheden
- Eigen resultaten: scripts, ruwe metingen en validatierapporten
- Bronclaim, waarneming en interpretatie uit elkaar houden
- Geen volledige standaardconformiteit aangetoond

**Context:** OGC betekent Open Geospatial Consortium, de organisatie achter geografische standaarden. Standaardconformiteit, bruikbaarheid in software en inhoudelijke juistheid zijn drie verschillende vragen.

## Slide 11. Meetresultaten: tijd en opslag

| Pakket | Mediaan | Spreiding, IQR | Uitgepakt | ZIP |
|---|---:|---:|---:|---:|
| A | 1,305 ms | 0,325 ms | 53.248 bytes | 3.535 bytes |
| B | 2,675 ms | 0,239 ms | 55.170 bytes | 5.295 bytes |
| C | 2,771 ms | 0,203 ms | 4.044 bytes | 3.589 bytes |

- Vijf opwarmruns, dertig metingen per pakket
- B: 1.760 bytes meer in ZIP dan A
- Kleine fixture, één computer, vaste meetvolgorde
- Bestaande SQLite-structuur beïnvloedt de bestandsgrootte
- Geen productie-export of algemene snelheidsranglijst
- Oorspronkelijke 18 uur was een raming, geen bewezen urenregistratie

**Begrippen:** mediaan is de middelste gesorteerde meetwaarde. IQR betekent interkwartielafstand, de spreiding van de middelste helft. Opwarmruns verminderen sommige opstarteffecten, niet alle meetbias.

**Interpretatie:** snelheid is op basis hiervan niet doorslaggevend voor de formaatkeuze.

## Slide 12. Eindantwoord en advies aan het team

- Advies: B als dossierontwerp
- GeoPackage voor GIS, bron-JSON voor inspectie en herstel
- Context expliciet bewaren
- Manifest koppelen aan vertrouwde overdrachtsreferentie
- Geen gemeten betekenisvoordeel van B boven A op deze fixture
- Productievoorwaarden: tabelfout herstellen, waarden tussen formaten vergelijken, hoogteverlies expliciet behandelen
- Onderzoek afgerond, applicatie niet productierijp

**Antwoord op de hoofdvraag:** open formaten bewaren de representaties. Context legt de interpretatie vast. Inhoudelijke validatie controleert betekenis, integriteitscontrole controleert wijzigingen. Geen van die onderdelen kan de andere vervangen.

**Afsluiten:** dit onderzoek is af. De geconstateerde productietekortkomingen zijn onderdeel van het eindadvies, geen belofte van vervolgonderzoek.

## Bij vragen

- Waarom B? Inspecteerbare bron naast GIS, niet omdat meer bestanden automatisch meer betekenis geven.
- Waarom geen live demo? Productie-export heeft een aangetoonde regressie, de uitgevoerde proeven en rapporten zijn het bewijs.
- Waarom geen volledige GIS-garantie? Alleen GDAL-leesproef uitgevoerd, geen interfaceproef in QGIS of ArcGIS Pro.
- Waar staan de resultaten? In `output/onderzoek/deepdive`, met methode en duiding in het verslag.
- Bewijst een goede hash dat de gegevens kloppen? Nee, alleen overeenkomst met de vastgelegde referentie.
