# Onderzoeksverslag deep-dive

**Student:** Hugo de Heus  
**Project:** Dossiervorming Digitale Scenario's vanuit Digital Twin  
**Datum:** 28 oktober 2026  
**Status:** Afgerond onderzoek met afgebakende conclusies

## 5.1 Hoofdvraag en antwoord

> Van Tygron-object naar duurzaam GIS-dossier: hoe combineer je open formaten, validatie en integriteitscontrole zonder betekenis te verliezen?

Het antwoord is een combinatie van een open gegevenscontainer, behoud van broninformatie en dossiercontext, inhoudelijke
controles en wijzigingsdetectie met een vertrouwde referentie. GeoPackage met bron-JSON en een SHA-256-manifest is mijn
advies voor overdracht in dit project. Het manifest beschermt daarbij de vastgelegde bestandsinhoud. Voor inhoudelijke
juistheid, overeenstemming tussen representaties en herkomst zijn aanvullende waarborgen nodig.

Dat advies heeft een belangrijke nuance. In de onderzochte 2D-demodata behield GeoPackage alleen al alle geteste
attributen doordat de bestaande implementatie een `source_json`-kolom bevat. Extra bron-JSON leverde hier geen gemeten
verbetering in betekenisbehoud op. De reden om bron-JSON daarnaast te bewaren is onafhankelijke inspectie en herstel,
zonder eerst het databaseformaat te hoeven lezen. Dat is een ontwerpoverweging, geen bewezen herstelproef.

De deep-dive is afgerond. Beperkingen en productievoorwaarden zijn onderdeel van het eindadvies en geen beloofd vervolg
van dit onderzoek. De applicatie is op grond van de aangetroffen exportregressie niet gereed voor productie.

## 5.2 Context, afbakening en bewijs

De Provincie Utrecht wil scenario-informatie ook buiten de actieve Tygron-omgeving kunnen raadplegen. Een object bevat
naast geometrie ook eigenschappen, eenheden, relaties en scenario-context. De centrale risico's zijn verlies bij
omzetting, onderlinge afwijking tussen exportbestanden en onterecht vertrouwen in een geldig formaat of manifest.

Het onderzoek combineert brononderzoek, code-inspectie en uitgevoerde lokale experimenten. De deelvragen zijn:

1. Welke informatie blijft bij de exportalternatieven behouden, verandert of gaat verloren?
2. Welke controles tonen bestandsintegriteit en bruikbaarheid aan, en welke claims kunnen zij niet onderbouwen?

Voor de formaatvergelijking zijn drie bestaande synthetische demo-objecten geselecteerd uit Merwedekanaalzone,
scenario Groen & Gezond 2040:

| Type | Object | Geteste kenmerken |
|------|--------|--------------------|
| Measure | 31, Parklint langs kanaal | Polygon, naam, status, beschrijving en kosten |
| Indicator | 21, Inwoners binnen 300 m van groen | Waarde 84,2, eenheid %, doelwaarde 75 en beschrijving |
| Alert | 41, Hittestress bij schoolplein | Punt, naam, ernst, status en beschrijving |

Dit zijn demo-objecten, geen export uit een actueel Tygron-project. Het oudere dossier `test_hallo_20260905T230247Z.zip`
diende afzonderlijk als referentie voor de proeven op de bestaande validator. Het bevat vier overlays, twee indicatoren,
één measure en nul alerts. Deze referentie wordt niet verward met de objectset van de formaatvergelijking.

De lokale onderzoekscode, testfixture, ruwe meetgegevens, JSON-rapporten en proefpakketten zijn bewaard voor
reproduceerbaarheid. Dit document bevat de relevante methode en uitkomsten zelf, zodat het zelfstandig leesbaar blijft.

## 5.3 Methode en meetlat

De drie vergeleken proefpakketten zijn:

| Alternatief | Inhoud |
|-------------|--------|
| A | GeoPackage met genormaliseerde velden, bestaande `source_json`-kolommen en dossiercontext |
| B | Hetzelfde GeoPackage, aparte bron-JSON, contextbestand en SHA-256-manifest |
| C | Bron-JSON, CSV, ruimtelijke GeoJSON, contextbestand en SHA-256-manifest |

Nieuwe exports uit de applicatie liepen vast. Daarom zijn A en B opgebouwd in een geïsoleerde proefopstelling op basis
van de tabelstructuur uit het bestaande referentiedossier. De geselecteerde records zijn hierin opnieuw ingevoerd met
de bestaande normalisatie- en geometriefuncties. Voor de alert is de geometriekolom geregistreerd en voor de gedeelde
context is een onderzoekstabel toegevoegd. De applicatiecode is niet gerepareerd of stilzwijgend vervangen.

Deze opzet maakt een vergelijking van representaties mogelijk, maar bewijst niet dat de huidige applicatie deze
pakketten zelf succesvol kan exporteren. Ook is de toegevoegde contexttabel geen getoetste OGC-metadatastandaard.

De oorspronkelijke veldchecklist is gebruikt om de betekenis van de controles te bepalen. De uitgevoerde vergelijking
bestond uit exacte vergelijking van de drie property-dictionaries, vergelijking van de twee geometrieblobs met de
bronencoding en controle van de scenario-context. Bij C zijn de volledige bronobjecten teruggelezen en vergeleken.

| Onderdeel | Controle en interpretatie |
|-----------|----------------------------|
| Identificatie, type, naam en beschrijving | Vergelijken van bronattributen en teruggelezen `source_json` of bron-JSON |
| Waarde en eenheid | Indicatorwaarde, eenheid en overige attributen behouden in de bronrepresentatie |
| Geometrie en CRS | Vergelijking met bronencoding en afzonderlijke GDAL-leesproef. Dit is geen volledige onafhankelijke geometrievalidatie |
| Relaties | Alleen aanwezige bronattributen vergelijken. De fixture bevat geen uitgebreide relatiestructuur, dus geen algemene conclusie over relationele volledigheid |
| Scenario-context | Dezelfde project-, scenario- en CRS-context meegeven en teruglezen |

Er is geen kunstmatige totaalscore van 20 punten toegekend. Daarvoor zou een onafhankelijk ingevuld formulier per veld
nodig zijn. Een geslaagde dictionaryvergelijking bewijst behoud van de geteste bronattributen, maar niet hun
domeininhoudelijke juistheid of gelijkwaardige zichtbaarheid in iedere GIS-gebruikersinterface.

## 5.4 Resultaten van de formaatvergelijking

Per alternatief zijn vijf opwarmruns en dertig meetruns uitgevoerd. De tijd omvat het opbouwen en ZIP-verpakken van het
proefpakket. De mediaan en interkwartielafstand zijn berekend uit de dertig meetruns. De volgorde was A, B, C. De
testomgeving was macOS op ARM64 met Python 3.13.3. Cache-effecten en achtergrondbelasting zijn niet volledig uitgesloten.

| Alternatief | Teruggelezen informatie | Mediaan | Interkwartielafstand | Uitgepakt | ZIP |
|-------------|--------------------------|--------:|---------------------:|---------:|----:|
| A | 3/3 property-dictionaries, 2/2 geometrie-encodings en context gelijk | 1,305 ms | 0,325 ms | 53.248 bytes | 3.535 bytes |
| B | 3/3 property-dictionaries, 2/2 geometrie-encodings en context gelijk | 2,675 ms | 0,239 ms | 55.170 bytes | 5.295 bytes |
| C | 3/3 volledige bronobjecten gelijk | 2,771 ms | 0,203 ms | 4.044 bytes | 3.589 bytes |

Alle drie de proefpakketten behouden de gecontroleerde broninformatie. Bij A en B staan aanvullende attributen zoals
kosten en doelwaarde al in `source_json`. De hypothese dat alleen een genormaliseerd GeoPackage deze eigenschappen
noodzakelijk verliest, wordt voor de bestaande implementatie en deze fixture niet ondersteund.

B gebruikt in deze proef 1.760 bytes meer ZIP-opslag dan A. C is uitgepakt het kleinst. Dat laatste hangt mede samen met
de kleine fixture en de overgenomen SQLite-bestandsstructuur, inclusief gereserveerde pagina's. Het verschil is geen
algemene uitspraak over de ruimte-efficiëntie van deze formaten.

A had in deze proef de laagste mediane opbouwtijd. De verschillen zijn milliseconden en betreffen de onderzoeksharness,
inclusief het kopiëren van een bestaand GeoPackage. Ze rechtvaardigen geen conclusie dat de echte applicatie of
GeoPackage in het algemeen sneller is. Snelheid is daarom niet doorslaggevend in het eindadvies.

## 5.5 Resultaten van validatie en integriteitsproeven

De bestaande validator is op zes gecontroleerde varianten van het referentiedossier uitgevoerd:

| Proef | Uitkomst | Betekenis |
|-------|----------|-----------|
| Ongewijzigd dossier | Goedgekeurd, 19/19 controles | Positieve controle voor deze interne validator |
| Bron-JSON gewijzigd, manifest gelijk | Afgekeurd, 18 goed en 1 fout | Afwijkende hash herkend |
| README verwijderd | Afgekeurd, 18 goed en 1 fout | Ontbrekend bestand herkend |
| Extra bestand toegevoegd | Afgekeurd, 18 goed en 1 fout | Niet-geregistreerd bestand herkend |
| Bron-JSON en manifest opnieuw gemaakt | Goedgekeurd, 19/19 controles | Een intern consistent manifest bewijst geen authenticiteit |
| Indicatorwaarde -999999 in bron-JSON, nieuw manifest | Goedgekeurd, 19/19 controles | De validator controleert geen inhoudelijke domeingeldigheid of exacte overeenkomst met het GeoPackage |

De laatste proef houdt de aantallen gelijk, maar verandert een inhoudelijke waarde. Het bestaande GeoPackage blijft
ongewijzigd. Toch keurt de validator het dossier goed. Dat toont aan dat de huidige controles vooral bestaan,
recordaantallen en hashes beoordelen. De eerdere aanname dat daarmee alle representaties inhoudelijk synchroon blijven,
is te sterk en wordt door dit experiment weerlegd.

Een SHA-256-manifest werkt dus als wijzigingsdetectie ten opzichte van de vastgelegde referentie. Wanneer iemand ook
die referentie kan aanpassen, bewijst de interne controle de oorspronkelijke herkomst niet. Een vertrouwd extern
vastgelegde hash of een controleerbare digitale handtekening is nodig voor een sterkere authenticiteitsclaim.

Daarnaast zijn de bestaande projecttests opnieuw uitgevoerd. De runner voerde 11 testmethoden uit en registreerde
9 errors, inclusief fouten in subtests. Dat is niet hetzelfde als negen afzonderlijke testmethoden. De belangrijkste
oorzaak is dat niet-ruimtelijke tabellen alleen binnen de ruimtelijke codevertakking worden aangemaakt. Een insert in
bijvoorbeeld `overlays` veroorzaakt daardoor `sqlite3.OperationalError: no such table: overlays`. Tests voor lege
componenten lopen op de dossiercontrole vast.

Een aparte encoderproef gaf voor punten `[5, 52, 10]` en `[5, 52, 99]` dezelfde geometrieblob. De derde coördinaat wordt
in deze route dus niet behouden. Deze proef staat los van de 2D-fixture en begrenst de claim over betekenisbehoud:
de onderzochte encoder is niet geschikt om hoogte-informatie stilzwijgend te archiveren.

## 5.6 Onafhankelijke leesproef, bronnen en betrouwbaarheid

Met GDAL 3.13.3, geleverd bij de lokale QGIS-installatie, is `ogrinfo -ro -al -so` uitgevoerd op proefpakket A. GDAL kon
het GeoPackage openen en rapporteerde één measure, één alert en één indicator. De twee ruimtelijke lagen werden
herkend, inclusief hun geometriekolom en geografisch referentiestelsel.

Dit is een onafhankelijke driverleesproef naast de eigen SQLite-controles. Het is geen test van de QGIS-gebruikersinterface,
geen ArcGIS Pro-test en geen volledige OGC-conformiteitscontrole. Het onderzoek rapporteert deze beperkingen als
afgeronde afbakening. Er wordt geen latere test beloofd om de conclusies alsnog geldig te maken.

| Bron | Rol en kritische weging |
|------|--------------------------|
| [OGC GeoPackage-specificatie](https://docs.ogc.org/is/12-128r19/12-128r19.html) | Normatieve structuur en conventies. Bewijst geen correctheid van mijn implementatie |
| [Nationaal Archief over geodata](https://www.nationaalarchief.nl/archiveren/kennisbank/geo-data) | Voorkeursformaten en preservation-overwegingen. Geen certificaat voor dit dossier |
| [GDAL GeoPackage-driver](https://gdal.org/en/stable/drivers/vector/gpkg.html) | Driverfuncties en technische beperkingen. Ondersteuning blijft versiegebonden |
| [ArcGIS Pro-documentatie](https://pro.arcgis.com/en/pro-app/latest/help/data/databases/work-with-sqlite-databases-in-arcgis-pro.htm) | Documenteerde productondersteuning. Geen vervanging van een zelf uitgevoerde ArcGIS-test |
| [Python hashlib](https://docs.python.org/3/library/hashlib.html) | Werking van hashfuncties op bestandsbytes. Geen inhoudelijke domeincontrole |
| Eigen experimenten | Direct bewijs voor de beschreven fixture en implementatie. Kleine steekproef en één testomgeving |

De schijnbare spanning tussen een interoperabele standaard, beschikbare validatietools en beperkte praktische
validatieondersteuning ontstaat doordat de bronnen verschillende claims behandelen. De meetresultaten bevestigen dat
onderscheid: het bestand is leesbaar en kan intern worden goedgekeurd, terwijl de volledige exportcode faalt en een
inhoudelijk gewijzigde representatie niet wordt herkend.

## 5.7 Eindadvies en antwoord op de deelvragen

**Deelvraag 1.** De drie geïsoleerde pakketten behouden de geteste 2D-broninformatie. Een afzonderlijk bronbestand is
voor deze fixture niet noodzakelijk om extra attributen te behouden, omdat het GeoPackage al `source_json` bevat.
Wel is aantoonbaar verlies van hoogte gevonden in de encoder. Algemene uitspraken over andere Tygron-objecttypen,
complexe relaties of onbekende coördinatenstelsels zijn niet door deze proeven gedekt.

**Deelvraag 2.** De manifestcontrole herkent veranderde, ontbrekende en extra bestanden zolang het oorspronkelijke
manifest vertrouwd blijft. Dezelfde validator detecteert geen onjuiste bronwaarde wanneer het manifest wordt bijgewerkt.
De GDAL-leesproef ondersteunt praktische leesbaarheid van het proefbestand, maar geen volledige interoperabiliteit met
alle GIS-producten.

Mijn definitieve advies aan het projectteam is **GeoPackage met bron-JSON, expliciete context en een SHA-256-manifest
voor overdracht**, met het GeoPackage als primaire GIS-representatie en de bron als inspecteerbare referentie. Dit is
een onderbouwd ontwerpbesluit, geen verklaring dat de huidige applicatie productierijp is.

| Optie | Afweging in het eindadvies |
|-------|----------------------------|
| A | Behoudt de fixture en is compact als pakket. Valt af als volledige overdrachtsroute door het ontbreken van een apart manifest en de afhankelijkheid van databasegereedschap voor broninspectie |
| B | Voorkeur voor overdracht. Combineert GIS-gebruik met los inspecteerbare broninformatie en bestandscontrole. Dubbele representaties vragen aantoonbare inhoudelijke vergelijking |
| C | Geschikt als eenvoudige uitwissel- of fallbackroute. Valt af als primaire dossierstructuur doordat relaties en samenhang over bestanden zijn verdeeld. Geen empirisch bewijs dat C inhoudelijk slechter bewaart in deze kleine fixture |

Voor ingebruikname gelden vier acceptatievoorwaarden voor het projectteam: correcte aanmaak van niet-ruimtelijke tabellen,
vergelijking van waarden en relaties tussen representaties, expliciet ondersteunen of afwijzen van Z-coördinaten en een
vertrouwde manifestreferentie voor de gewenste herkomstclaim. Deze voorwaarden volgen uit de gevonden fouten. Zij zijn
geen extra werkzaamheden die in deze deep-dive als uitgevoerd worden voorgesteld.

Een duurzaam dossier vraagt bovendien eigenaarschap, passende toegang en bewaarbeleid. De techniek helpt keuzes over de
leefomgeving uitlegbaar houden. Open formaten betekenen daarbij geen onbeperkte toegang tot gevoelige gegevens.
Toegangstokens horen buiten het dossier. Extra representaties kosten opslag, maar de gemeten overhead in deze fixture
is klein. Dat rechtvaardigt alleen deze lokale afweging en geen algemene uitspraak over grote projecten.

## 5.8 Afronding, reflectie en presentatie

De belangrijkste leeropbrengst is het onderscheid tussen een norm, een leesbaar bestand, interne consistentie,
inhoudelijke juistheid en authenticiteit. De eerste hypothese over extra bron-JSON moest worden genuanceerd door de
aanwezige `source_json`-kolom. De tweede aanname over inhoudelijke synchronisatie is door de gemanipuleerde waarde
weerlegd. De conclusie volgt daarmee uit zowel positieve als negatieve resultaten.

De oorspronkelijke raming was 18 uur: vraag en scope 2 uur, bronnen 3 uur, testdata 3 uur, tests 5 uur, analyse 2 uur,
slides 2 uur en repetitie 1 uur. Er is geen gecontroleerde urenregistratie, docentgoedkeuring of planbordbewijs
aangeleverd. Daarom worden de 18 uur als raming gerapporteerd en niet als bewezen tijdsbesteding.

De presentatie behandelt het afgeronde onderzoek in dezelfde twaalf slides als de aangeleverde PowerPoint. De
hoofdvraag staat direct na de titel. De bestaande secties zijn bijgewerkt naar methode, uitkomsten, beperkingen en
eindadvies. Spreekpunten ondersteunen improvisatie, met uitleg van afkortingen in de begeleidende spiekbrief.

| Slides | Onderdeel | Richttijd |
|--------|-----------|----------:|
| 1 en 2 | Onderwerp en hoofdvraag | 3 minuten |
| 3 en 4 | Praktijkprobleem en afbakening | 4 minuten |
| 5 en 6 | Alternatieven en geïsoleerde proefopstelling | 6 minuten |
| 7 en 8 | Betekenisbehoud, exportfout en leesproef | 5 minuten |
| 9 en 10 | Integriteitsproeven en bronnen | 6 minuten |
| 11 en 12 | Metingen, beperkingen en eindadvies | 4 minuten |
| Na slide 12 | Vragen | maximaal 5 minuten |

De richttijd is 28 minuten inhoud plus maximaal 5 minuten vragen. Een proefpresentatie is nodig om de werkelijke duur
vast te stellen, maar wordt niet als uitgevoerd geclaimd. Er staan geen ontbrekende resultaten of toekomstige
onderzoeksstappen meer open binnen de gerapporteerde deep-dive.
