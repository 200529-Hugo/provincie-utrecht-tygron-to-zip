# Opbrengst Hackathon 6 toegepast op ScenarioDossier

Trello #96. Hackathon 6, Duurzame digitalisering, 19 november 2026.

## Inzending en bewijs

- Inzending op Canvas: [Hackathon 6](https://canvas.hu.nl/courses/55135/assignments/431577), met het SIIA-verslag van ons project en het reviewrapport uit het kruisverhoor.
- Beoordeling: 3 van de 3 punten, met positieve observaties op LU1 (twee keer) en LU5.
- Beeld voor de review: het Double Diamond-schema op de eerste pagina van het SIIA-verslag.

## De les

Wij hebben ScenarioDossier beoordeeld met het SIIA-kompas (Sustainable, Inclusive, Intelligent, Autonomous). De belangrijkste les komt uit het onderdeel Sustainable.

Het dossier slaat dezelfde gegevens in meerdere formaten op: de bron-JSON, CSV, GeoJSON en GeoPackage. Dat helpt bij hergebruik en maakt het dossier onafhankelijk van één leverancier. Het kost ook opslag en verwerking, en wij hebben nog niet gemeten hoeveel. Tijdens de hackathon zagen we dat we bij het ontwerp niet hebben gevraagd welke formaten een gebruiker echt nodig heeft.

Relatie met de SDG's: dit raakt aan SDG 12, verantwoorde consumptie en productie, omdat het gaat om zuinig omgaan met opslag en rekenkracht. Dit is een voorstel. Leg het naast de SDG-keuze die het team in Sprint 2 heeft gemaakt (#32).

## De ontwerpkeuze

**Voorstel:** maak in het dossier onderscheid tussen archiefbestanden en gebruiksformaten.

| Soort | Bestanden | Altijd in het dossier |
| --- | --- | --- |
| Archief | Bron-JSON, GeoPackage, metadata, validatierapport, SHA-256-manifest, HTML-rapport | Ja |
| Gebruiksgemak | CSV, GeoJSON, GeoTIFF | Naar keuze van de gebruiker |

Onderbouwing:

- De bron-JSON en het GeoPackage bevatten samen alle gegevens. CSV en GeoJSON zijn afgeleiden daarvan.
- De gebruiker kiest nu al welke onderdelen in het dossier komen. Een keuze voor formaten sluit daarop aan.
- Het manifest en de validatie blijven werken, omdat ze de bestanden controleren die in het dossier zitten.

Voordat we dit bouwen, meten we hoe groot een gemiddeld dossier is en welk deel de gebruiksformaten innemen. Zonder die meting weten we niet of de winst de extra keuze in de interface waard is.

Tweede verbeterpunt uit de analyse, onderdeel Inclusive: de interface is nog niet getoetst aan WCAG 2.2. Dat nemen we mee bij de gebruikerstests.

## Voor de review

Vraag aan de opdrachtgever: welke formaten gebruiken jullie collega's echt, en mogen CSV en GeoJSON optioneel worden? Bij een ja komt er een backlogitem voor de meting en een voor de formaatkeuze.
