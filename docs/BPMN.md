# Procesdiagram ScenarioDossier

Dit compacte schema toont alleen het hoofdproces. De tekst tussen de vierkante haken
kan direct worden aangepast zonder de verbindingen te wijzigen.

```mermaid
flowchart TD
    start((Start))
    bron[Kies bron: demo of Tygron]
    scenario[Selecteer project en scenario]
    ophalen[Haal scenariodata op]
    controleren[Controleer gegevens en kaart]
    selecteren[Selecteer onderdelen voor het dossier]
    metadata[Vul dossiergegevens en onderbouwing in]
    exporteren[Exporteer naar open bestandsformaten]
    validatie{Dossier geldig?}
    fout[Pas invoer of selectie aan]
    zip[Maak ZIP met rapport en controlesommen]
    bewaren[Download en bewaar het dossier]
    einde((Einde))

    start --> bron
    bron --> scenario
    scenario --> ophalen
    ophalen --> controleren
    controleren --> selecteren
    selecteren --> metadata
    metadata --> exporteren
    exporteren --> validatie
    validatie -->|Nee| fout
    fout --> selecteren
    validatie -->|Ja| zip
    zip --> bewaren
    bewaren --> einde
```

## Betekenis van de vormen

- Cirkel: begin of einde.
- Rechthoek: activiteit.
- Ruit: beslissing.

