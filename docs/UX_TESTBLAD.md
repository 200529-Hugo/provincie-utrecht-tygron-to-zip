# Testblad gebruikerstests ScenarioDossier

Trello [#97](https://trello.com/c/kD9mYBP5/97-use-cases-voor-externe-gebruikerstests-uitwerken). Dit blad gebruiken we
voor de interne proefronde en de externe sessies
van [#82](https://trello.com/c/6FQt3ZI5/82-met-gebruikers-testen-of-de-applicatie-goed-werkt-en-begrijpelijk-is). De
bevindingen gaan naar de analyse van #93.

## Opzet van een sessie

| Onderdeel     | Afspraak                                                                                                                |
|---------------|-------------------------------------------------------------------------------------------------------------------------|
| Duur          | 30 tot 35 minuten per deelnemer                                                                                         |
| Rollen        | Eén begeleider leest de opdrachten voor. Eén observator vult het formulier in en zegt niets.                            |
| Deelnemer     | Krijgt een code (P1, P2, …). We noteren geen naam. Wel de rol: GIS-gebruiker, beleidsmedewerker of anders.              |
| Omgeving      | ScenarioDossier draait lokaal op `http://127.0.0.1:8080` in de demonstratiemodus. Voor use case 4 staat QGIS 3.x klaar. |
| Hulp          | De begeleider helpt pas als de deelnemer er zelf om vraagt of twee minuten vastzit. Elke hulp wordt genoteerd.          |
| Hardop denken | Vraag de deelnemer te vertellen wat die zoekt en verwacht.                                                              |

Zeg vooraf: "We testen de applicatie, niet jou. Als iets niet lukt, ligt dat aan ons ontwerp."

### Klaarzetten

1. Start de app volgens de [README](../README.md) en open `http://127.0.0.1:8080`.
2. Controleer dat **Demonstratie openen** het projectenoverzicht toont met Merwedekanaalzone, Stationsgebied Utrecht,
   Kromme Rijngebied en Merwedekanaalzone · RD New.
3. Leeg de downloadmap of noteer welke ZIP-bestanden er al staan.
4. Zet de app terug op de loginpagina en de taal op Nederlands voordat de deelnemer begint.

## Use cases

De opdrachten staan in gebruikerstaal. Lees alleen de tekst onder **Opdracht** voor. Het verwachte resultaat is voor de
observator.

### Use case 1: het juiste scenario vinden

- **Rol:** medewerker van de provincie die een scenario wil vastleggen.
- **Beginsituatie:** de loginpagina van ScenarioDossier.
- **Opdracht:** "Je collega heeft voor de Merwedekanaalzone een scenario gemaakt met de naam Groen & Gezond 2040. Je
  hebt geen Tygron-account bij de hand. Zoek dit scenario op in de demonstratie."
- **Verwacht resultaat:** de deelnemer kiest **Demonstratie openen**, selecteert het project **Merwedekanaalzone** en
  ziet in stap 3 het scenario **Groen & Gezond 2040** met de kaart en de onderdelen.
- **Let op:** vindt de deelnemer de demonstratieknop, en is duidelijk dat een projectrij aanklikbaar is?

### Use case 2: alleen de gevraagde onderdelen selecteren

- **Rol:** dezelfde medewerker.
- **Beginsituatie:** stap 3, Kaart en selectie, van Merwedekanaalzone met scenario Groen & Gezond 2040.
- **Opdracht:** "Voor dit dossier zijn alleen hitte en groen van belang. Zorg dat het dossier alleen deze onderdelen
  bevat: de overlays Hittestress gevoelstemperatuur en Groen op loopafstand, de indicator Boomkroonbedekking en de alert
  Capaciteit buurtzorgpunt onzeker. Klik daarna op de naam van de alert en vertel wat je op de kaart ziet."
- **Verwacht resultaat:** in **Onderdelen in dossier** staan precies deze vier onderdelen aangevinkt en de teller toont
  vier records. De deelnemer heeft op de naam van de alert geklikt en benoemt wat de kaart toont.
- **Let op:** gebruikt de deelnemer **Geen** en daarna losse vinkjes, het zoekveld, of vinkt die alles één voor één uit?
  Is de teller begrijpelijk?

### Use case 3: het dossier maken en controleren

- **Rol:** dezelfde medewerker.
- **Beginsituatie:** de selectie uit use case 2.
- **Opdracht:** "Maak nu het dossier en bewaar het op deze computer. Laat daarna zien dat het bestand compleet en
  ongewijzigd is."
- **Verwacht resultaat:** de deelnemer kiest **Dossier maken**, downloadt het ZIP-bestand en vindt het terug in de
  downloadmap. Via **Dossier controleren** in de header uploadt de deelnemer het ZIP-bestand en ziet de uitkomst *
  *Goedgekeurd**, met een geslaagde controle van het SHA-256-manifest.
- **Let op:** is duidelijk welke velden verplicht zijn? Vindt de deelnemer **Dossier controleren** zonder hulp? Begrijpt
  de deelnemer wat Goedgekeurd betekent?

### Use case 4: het dossier openen in GIS

Alleen voor deelnemers die met GIS werken. Nodig: QGIS 3.x. Het dossier bevat een GeoPackage, `gis/scenario.gpkg`.

- **Rol:** GIS-gebruiker die het dossier van een collega krijgt.
- **Beginsituatie:** QGIS staat open met een leeg project in Amersfoort / RD New (EPSG:28992). Het ZIP-dossier uit de
  demo **Merwedekanaalzone · RD New**, geëxporteerd met RD New als GeoPackage-CRS, staat op het bureaublad.
- **Opdracht:** "Je hebt dit dossier van een collega gekregen. Open de kaartgegevens in QGIS en zoek het Buurtzorgpunt
  op de kaart."
- **Verwacht resultaat:** de deelnemer pakt het ZIP-bestand uit, voegt `gis/scenario.gpkg` toe als vectorlaag, opent de
  laag `measures` en vindt het object **Buurtzorgpunt** op de kaart of in de attributentabel. De laag heeft EPSG:28992
  als CRS.
- **Let op:** vindt de deelnemer het GeoPackage in de mappenstructuur? Gebruikt de deelnemer het HTML-rapport of de
  README in het dossier om de weg te vinden?

## Scoring

Per use case kiest de observator één uitkomst.

| Uitkomst      | Wanneer                                                           |
|---------------|-------------------------------------------------------------------|
| Zelfstandig   | Het verwachte resultaat is bereikt zonder hulp van de begeleider. |
| Met hulp      | Het verwachte resultaat is bereikt na een of meer aanwijzingen.   |
| Niet afgerond | Het verwachte resultaat is niet bereikt, of de deelnemer stopt.   |

Stop een use case na acht minuten en noteer Niet afgerond. Zet de app daarna zelf in de beginsituatie van de volgende
use case.

## Observatieformulier

Eén formulier per deelnemer.

| Veld                     | Invullen                                    |
|--------------------------|---------------------------------------------|
| Deelnemercode            |                                             |
| Rol                      | GIS-gebruiker / beleidsmedewerker / anders: |
| Intern of extern         |                                             |
| Datum                    |                                             |
| Begeleider en observator |                                             |

| Use case                       | Uitkomst | Tijd (min) | Aantal keer hulp | Fouten of omwegen | Opmerkingen en uitspraken van de deelnemer |
|--------------------------------|----------|------------|------------------|-------------------|--------------------------------------------|
| 1 Scenario vinden              |          |            |                  |                   |                                            |
| 2 Onderdelen selecteren        |          |            |                  |                   |                                            |
| 3 Dossier maken en controleren |          |            |                  |                   |                                            |
| 4 Openen in GIS                |          |            |                  |                   |                                            |

Afsluitende vragen:

1. Wat ging het makkelijkst?
2. Waar twijfelde je het meest?
3. Wat zou je als eerste veranderen?

## Controle van dit testblad

- [ ] Een teamlid heeft het blad zonder extra uitleg doorgelopen in de demo (Definition of Done van #97).
- [ ] De vier use cases zijn in de demo uitvoerbaar met de genoemde namen.
- [ ] De link naar dit blad staat op kaart #97.
