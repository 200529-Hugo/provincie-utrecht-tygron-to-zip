from __future__ import annotations

import json
from pathlib import Path

from ..models import Project, Scenario


class DemoService:
    """Lees de offline demonstratie zonder live API-aanroepen of exportlogica."""

    def __init__(self, data_path: Path | None = None) -> None:
        self.data_path = data_path or Path(__file__).parents[2] / 'data' / 'demo.json'

    def read_data(self) -> dict:
        return json.loads(self.data_path.read_text(encoding='utf-8'))

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
