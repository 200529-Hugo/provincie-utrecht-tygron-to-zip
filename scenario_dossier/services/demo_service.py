from __future__ import annotations

import json
from pathlib import Path

from ..models import Project, Scenario


class DemoService:
    def __init__(self, data_path: Path | None = None) -> None:
        self.data_path = data_path or Path(__file__).parents[2] / "data" / "demo.json"

    def list_projects(self) -> list[Project]:
        payload = json.loads(self.data_path.read_text(encoding="utf-8"))
        return [Project.from_dict(item) for item in payload.get("projects") or []]

    def get_project(self, project_id: str) -> Project:
        for project in self.list_projects():
            if project.id == project_id:
                return project
        raise LookupError("Project niet gevonden.")

    def get_scenario(self, project_id: str, scenario_id: str) -> Scenario:
        return self.get_project(project_id).get_scenario(scenario_id)

    def public_catalog(self) -> dict[str, list[dict]]:
        return {"projects": [project.to_public_dict() for project in self.list_projects()]}
