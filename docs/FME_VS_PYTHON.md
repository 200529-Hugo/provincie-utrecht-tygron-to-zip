# Keuze tussen FME en Python voor ScenarioDossier

**Advies voor Sprint Review 4.** Houd Python aan voor het prototype. De bestaande Python-keten levert een controleerbaar
ZIP-dossier op en draait lokaal zonder FME-runtime. Toets vóór de productiekeuze wie de keten gaat beheren, welke
runtime en licentie zijn toegestaan en of FME met dezelfde invoer hetzelfde bruikbare dossier kan
opleveren. [Trello #92](https://trello.com/c/3Pr764HR/92-keuze-tussen-fme-en-python-onderbouwen)

## Wat de keuze moet oplossen

De [projectopdracht](OPDRACHT.md) vraagt om Tygron-scenario’s buiten Tygron te kunnen bewaren en hergebruiken. De
ETL-keten haalt overlays, indicatoren, measures en alerts op, verwerkt de selectie en levert een GIS-dossier dat een
collega zelfstandig kan openen en controleren. Beoordeel de hele keten, inclusief Tygron-sessies, foutafhandeling en
overdracht.

| Aanpak           | Sterke kant                                                                                                                                                    | Werk en afhankelijkheden                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
|------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Python**       | De huidige werkstroom voor selectie, export en controle werkt al. De code staat in Git en het team kan de export automatisch testen.                           | Het team onderhoudt zelf het Tygron-contract, de dataconversies en de GeoPackage-schrijver. Productiebeheer vraagt ondersteunde Python-runtime, beheerafspraken en GIS-kennis. [Exportcode](../scenario_dossier/exporting/archive.py) · [Python Software Foundation](https://www.python.org/psf/about/)                                                                                                                                                                                                                                                                                                                                                                                 |
| **FME**          | Workbench modelleert datatransformaties visueel. Safe documenteert HTTP-aanroepen en lezen en schrijven van GeoPackage en GeoJSON.                             | Bouw en toets de Tygron-sessieafhandeling en het volledige dossiercontract in een workspace. Controleer welke FME-licentie, versie en beheeromgeving de provincie beschikbaar heeft. Serveruitvoering via FME Flow vraagt een ingerichte omgeving. [HTTPCaller](https://docs.safe.com/fme/2026.1/html/FME-Form-Documentation/FME-Transformers/Transformers/httpcaller.htm) · [GeoPackage](https://docs.safe.com/fme/2026.2/html/FME-Form-Documentation/FME-ReadersWriters/ogcgeopackage/ogcgeopackage.htm) · [FME Flow](https://docs.safe.com/fme/2026.2/html/FME-Form-Documentation/FME-Form/Workbench/Working-with-FME-Flow.htm) · [Licentievoorwaarden](https://www.safe.com/legal/) |
| **Python + FME** | Python houdt de webflow, selectie en pakketcontrole in één applicatie. FME kan een afgebakende GIS-transformatie overnemen als beheer daar voordeel aan heeft. | Definieer het invoer- en uitvoercontract, eigenaarschap, retries en foutmeldingen tussen de twee onderdelen. Een export waarin FME meedraait vraagt beide runtimes en een geldige FME-licentie.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |

## Beslismatrix en gevoeligheid

De scores komen uit
het [verantwoordingsdocument, §3.3](hugo/verantwoordingsdocument.md#33-mcda-1---extract-transform-load-technologie). Een
5 betekent een sterkere aansluiting op de criteria voor dit prototype. Het gewogen totaal is de som van
`gewicht × score / 5`. Beheerbaarheid en snelheid voor FME en hybride blijven inschattingen totdat er een proef en
beoordeling door provinciaal beheer zijn.

| Aanpak       | GIS 25% | Onafhankelijkheid 20% | Ontwikkelsnelheid 15% | Beheer 20% | Testbaarheid 15% | Secretbeheer 5% |     Totaal |
|--------------|--------:|----------------------:|----------------------:|-----------:|-----------------:|----------------:|-----------:|
| Python       |       4 |                     5 |                     5 |          3 |                5 |               4 | **86/100** |
| FME          |       5 |                     2 |                     4 |          5 |                4 |               4 | **81/100** |
| Python + FME |       5 |                     3 |                     2 |          4 |                5 |               4 | **78/100** |

Bij dezelfde scores en een verschuiving van 10 procentpunt van onafhankelijkheid naar beheer stijgt FME naar **87/100**,
terwijl Python **82/100** en hybride **80/100** scoren. Een beheerbesluit kan de volgorde dus veranderen. De scores zijn
geen prestatiemetingen.

## Proef met dezelfde invoer en uitvoereisen

Gebruik **Merwedekanaalzone -> Groen & Gezond 2040** uit de [demodata](../data/demo.json). De vier bronbestanden staan
ook in de [geteste demo-export](ScenarioDossier-demoproef-92-94.zip).

| Controle             | Verwachte uitkomst voor elk alternatief                                                                                                                                                                                         |
|----------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Inhoud en selectie   | 5 overlays, 6 indicatoren, 6 measures en 4 alerts bij de volledige selectie. Vergelijk de bron-ID’s en test daarnaast een beperkte selectie.                                                                                    |
| GIS                  | Het GeoPackage bevat de vier tabellen. De 6 measures en 2 ruimtelijke alerts behouden geometrie en bron-ID. Leg CRS en transformatie expliciet vast.                                                                            |
| Dossier              | Het ZIP-bestand bevat brondata, GeoPackage, bijbehorende GeoJSON en CSV, de metadata, het HTML-rapport en een geldig SHA-256-manifest. Het bestaande controlescherm keurt het dossier goed.                                     |
| Foutafhandeling      | Test ook een ontbrekend brononderdeel en een beschadigd ZIP-bestand. Leg vast welke fout gemeld wordt en hoe de beheerder die kan terugvinden. Controleer dat credentials geen onderdeel zijn van het dossier of de uitvoerlog. |
| Beheer en inspanning | Noteer per alternatief de benodigde licentie en runtime, overdrachtsstappen, opbouwtijd en doorlooptijd op dezelfde testomgeving.                                                                                               |

**Gemeten.** De volledige Python-export is op 16 november 2026 via de normale export- en validatieroutes uitgevoerd. De
validator gaf **20 geslaagde controles en 0 fouten**. De bron-ID’s en aantallen zijn apart vergeleken met de tabellen in
het GeoPackage. Zie [het ERD en de uitkomst per tabel](ERD_SCENARIODOSSIER.md#toets-met-een-demo-export). De reguliere
Python-exporttests omvatten ook de beperkte selectie en manifestcontrole. Voor FME en hybride was lokaal geen
FME-installatie beschikbaar. Hun uitvoer, doorlooptijd en licentie bij de provincie zijn nog onbevestigd. De proef
gebruikte offline demodata en liet rasterdownload en live Tygron-toegang buiten beschouwing.

## Besluitvraag voor de opdrachtgever

**Welke keten kan provinciaal GIS- en IT-beheer na overdracht daadwerkelijk beheren?** Vraag wie eigenaar is van de
jobs, wie meldingen onderzoekt, welke licentie en runtime beschikbaar zijn en waar credentials en exportbestanden worden
beheerd. Heropen het advies zodra beheer bevestigt dat FME de standaard is én een FME- of hybride proef dezelfde
dossiercontroles haalt. Kies een hybride opzet alleen als de extra integratie een aantoonbaar probleem in
GIS-transformatie of beheer oplost.

De tweede teamreview en toets bij provinciaal GIS- of IT-beheer staan open.
