from dataclasses import dataclass, field

from ...dossier import DossierDetails
from ..base import JsonModel, boolean, object_value, string_list, text


@dataclass(frozen=True)
class InspectRequest(JsonModel):
    """De bron bepaalt welke velden nodig zijn om het scenario te openen."""

    source: str = 'demo'
    project_id: str = ''
    scenario_id: str = ''
    base_url: str = ''
    token: str = field(default='', repr=False)
    username: str = ''
    login_key: str = field(default='', repr=False)
    domain: str = ''
    project_file: str = ''
    project_name: str = ''
    scenario_name: str = ''
    authenticated: bool = False

    @classmethod
    def from_dict(cls, value: dict) -> 'InspectRequest':
        data = object_value(value)
        source = text(data, 'source', 'demo')
        if source not in ('demo', 'tygron', 'tygron_project'):
            raise ValueError('Onbekende gegevensbron.')
        names = ('project_id', 'scenario_id', 'base_url', 'token', 'username',
                 'login_key', 'domain', 'project_file', 'project_name', 'scenario_name')
        return cls(source=source, authenticated=boolean(data, 'authenticated'),
                   **{name: text(data, name) for name in names})


@dataclass(frozen=True)
class ExportRequest(InspectRequest):
    notes: str = ''
    dossier: DossierDetails = field(default_factory=DossierDetails)
    components: list[str] | None = None
    selected_items: dict[str, list[str]] | None = None
    rasters: bool = True

    @classmethod
    def from_dict(cls, value: dict) -> 'ExportRequest':
        data = object_value(value)
        source = InspectRequest.from_dict(data)
        components = data.get('components')
        if components is not None:
            components = string_list(components, 'components')
        selected = data.get('selected_items')
        if selected is not None:
            selected = {name: string_list(keys, 'selected_items')
                        for name, keys in object_value(selected).items()}
        dossier = data.get('dossier')
        if dossier is None:
            dossier = {}
        return cls(**source.to_dict(), notes=text(data, 'notes')[:4000],
                   dossier=DossierDetails.from_dict(object_value(dossier)),
                   components=components, selected_items=selected,
                   rasters=boolean(data, 'rasters', True))
