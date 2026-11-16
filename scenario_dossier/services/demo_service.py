from __future__ import annotations

import json
from pathlib import Path

from ..coordinates import RD_NEW, WGS84, reproject_geometry
from ..models import ComponentType, Project, Scenario


class DemoService:
    """Lees de offline demonstratie zonder live API-aanroepen of exportlogica."""

    def __init__(self, data_path: Path | None = None) -> None:
        self.data_path = data_path or Path(__file__).parents[2] / 'data' / 'demo.json'
        self._additional_catalog = self.data_path.with_name('demo-rd-new.json') if data_path is None else None

    def revision(self) -> tuple[int, ...]:
        paths = (self.data_path, self._additional_catalog) if self._additional_catalog else (self.data_path,)
        return tuple(path.stat().st_mtime_ns for path in paths)

    def read_data(self) -> dict:
        payload = json.loads(self.data_path.read_text(encoding='utf-8'))
        if self._additional_catalog:
            additional = json.loads(self._additional_catalog.read_text(encoding='utf-8'))
            payload['projects'].extend(additional['projects'])
        for project in payload.get('projects') or []:
            source_crs = project.get('source_crs', WGS84)
            if source_crs == WGS84:
                continue
            if source_crs != RD_NEW:
                raise ValueError(f'Onbekend coördinatenstelsel voor demoproject: {source_crs}')
            for scenario in project.get('scenarios') or []:
                data = scenario.get('data') or {}
                for component in ComponentType.values():
                    for item in data.get(component) or []:
                        if geometry := item.get('geometry'):
                            item.pop('bbox', None)
                            item.pop('crs', None)
                            item['geometry'] = reproject_geometry(geometry, source_crs, WGS84)
        return payload

    def list_projects(self) -> list[Project]:
        payload = self.read_data()
        return [Project.from_dict(item) for item in payload.get('projects') or []]

    def get_project(self, project_id: str) -> Project:
        for project in self.list_projects():
            if project.id == project_id:
                return project
        raise LookupError('Project niet gevonden.')

    def get_scenario(self, project_id: str, scenario_id: str) -> Scenario:
        return self.get_project(project_id).get_scenario(scenario_id)

    def get_scenarios(self, project_id: str) -> list[Scenario]:
        return self.get_project(project_id).scenarios

    def public_catalog(self) -> dict:
        return {'projects': [project.to_public_dict() for project in self.list_projects()]}
