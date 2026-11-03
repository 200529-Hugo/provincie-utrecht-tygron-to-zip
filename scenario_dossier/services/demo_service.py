from __future__ import annotations

import json
from http import HTTPStatus
from pathlib import Path
from typing import Any

from scenario_dossier.models import ScenarioData, TygronFetchResult
from scenario_dossier.tygron import TygronClient, TygronRootSession

from ..models import Project, Scenario, ActiveSessionCredentials, ProjectCredentials
from .tygron_service import TygronService
from ..exporter import build_archive

ROOT = Path(__file__).parent.parent
STATIC = ROOT / "static"
EXPORTS = ROOT / "exports"
COMPONENTS = ("overlays", "indicators", "measures", "alerts")

def _item_inventory(data):
    inventory = []
    if isinstance(data, ScenarioData):
        components = {"overlays": data.overlays, "indicators": data.indicators, "measures": data.measures, "alerts": data.alerts}
    else:
        components = data
    for component_name, items in components.items():
        for index, item in enumerate(items):
            props = _properties(item)
            value = props.get("value", props.get("currentValue"))
            unit = props.get("unit", "")
            status = props.get("status", props.get("severity", ""))
            item_type = props.get("type", props.get("overlayType", ""))
            detail = " ".join(
                str(part) for part in (item_type, status, value, unit)
                if part not in (None, "")
            )
            geometry = item.get("geometry")
            inventory.append({
                "key": _item_key(item, index),
                "component": component_name,
                "name": str(props.get("name", props.get("shortName", f"{component_name} {index + 1}"))),
                "detail": detail[:240],
                "spatial": bool(geometry),
                "geometry_type": geometry.get("type", "") if isinstance(geometry, dict) else "",
            })
    return inventory


# Gets the properties of an item, handling both Feature and non-Feature types.
def _properties(item):
    if item.get("type") == "Feature":
        return item.get("properties") or {}
    return item


# Generates a unique key for an item based on its ID or index.
def _item_key(item, index):
    item_id = _properties(item).get("id")
    return f"id:{item_id}" if item_id is not None else f"index:{index}"

# Filters the data based on selected components and items, returning only the relevant parts.
def _select_data(data, selected_components=None, selected_items=None):
    all_components = {
        "overlays": data.overlays,
        "indicators": data.indicators,
        "measures": data.measures,
        "alerts": data.alerts
    }
    components = {}
    if not selected_components is None:
        components = all_components
    else:
        for key, value in all_components.items():
            if key in selected_components:
                components[key] = value

    item_selection = selected_items if isinstance(selected_items, dict) else None
    result = {}
    for component_name, items in components.items():
        if item_selection is not None and component_name in item_selection:
            wanted = {str(key) for key in item_selection[component_name]}
            items = [
                item for index, item in enumerate(items)
                if _item_key(item, index) in wanted
            ]
        result[component_name] = items
    return result

class DemoService:
    def __init__(self, data_path: Path | None = None) -> None:
        self.data_path = data_path or Path(__file__).parents[2] / "data" / "demo.json"
        self.tygron_service = TygronService()

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

    def get_scenarios(self, project_id: str) -> list[Scenario]:
        try:
            project = self.get_project(project_id)
            return project.get_scenarios()
        except:
            raise LookupError("Project niet gevonden.")

    def get_project_and_scenario_by_ids(self, project_id: str, scenario_id: str) -> tuple[Project, Scenario]:
        project = self.get_project(project_id)
        for scenario in project.scenarios:
            if scenario.id == scenario_id:
                return project, scenario
        raise ValueError("Scenario niet gevonden.")

    def public_catalog(self) -> dict[str, list[dict]]:
        return {"projects": [project.to_public_dict() for project in self.list_projects()]}

    # Inspects the project and scenario data, returning counts, spatial information, warnings, and a preview of items as JSON.
    def inspect(self, payload) -> dict[str, dict[Any, int] | int | list[Any] | Any]:
        project, scenario, data, warnings, _, session = self._resolve(payload)
        try:
            # Count the number of spatial items in the data by checking for the presence of geometry in each item across all components.
            print(data)
            # spatial = sum(1 for group in data.values() for item in group if item.get("geometry"))
            spatial = data.get_spatial()

            preview = []
            for index, item in enumerate(data.measures):
                if item.get("geometry"):
                    preview.append({
                        "component": "measures",
                        "key": _item_key(item, index),
                        "feature": item,
                    })

            for index, item in enumerate(data.alerts):
                if item.get("geometry"):
                    preview.append({
                        "component": "alerts",
                        "key": _item_key(item, index),
                        "feature": item,
                    })

            # Return the inspection results as a JSON response, including project and scenario names, counts of items per component, spatial item count, warnings, preview of spatial items, and an inventory of all items.
            return {
                "project": project,
                "scenario": scenario,
                "counts": {
                    "overlays": len(data.overlays),
                    "indicators": len(data.indicators),
                    "measures": len(data.measures),
                    "alerts": len(data.alerts)
                    # key: len(data)
                    # for key in COMPONENTS
                },
                "spatial": spatial,
                "warnings": warnings,
                "preview": preview,
                "items": _item_inventory(data),
            }
        # Ensure that the session is closed after the inspection is complete, regardless of whether an exception occurred or not.
        finally:
            if session:
                session.close()

    # Exports the selected project and scenario data, creating a ZIP archive and returning the filename, download link, and summary as JSON.
    def export(self, p):
        project, scenario, data, warnings, client, session = self._resolve(p)
        try:
            # Filter the data based on the selected components and items specified in the request parameters, returning only the relevant parts for export.
            data = _select_data(data, p.get("components"), p.get("selected_items"))
            # Build the export archive using the filtered data, project and scenario names, notes, source, warnings, and optional raster fetching function if applicable.
            archive, summary = build_archive(
                EXPORTS,
                project,
                scenario,
                data,
                str(p.get("notes", ""))[:4000],
                p.get("source", "demo"),
                warnings,
                client.fetch_overlay_geotiff if client and p.get("rasters", True) else None,
                p.get("dossier", {}),
            )
            # Return the export result as a JSON response, including the filename of the created archive, a download link, and a summary of the export process.
            return {
                "ok": True,
                "filename": archive.name,
                "download": f"/api/download/{archive.name}",
                "summary": summary,
            }
        # Ensure that the session is closed after the export is complete, regardless of whether an exception occurred or not.
        finally:
            if session:
                session.close()

    # Resolves the project and scenario information based on the provided parameters, handling different data sources.
    def _resolve(self, payload) -> tuple[str, str, ScenarioData, list[Any], None, None] | tuple[
        Any, Any, dict[str, list[dict[str, Any]]], list[
            str], TygronClient | TygronFetchResult, TygronRootSession | None]:
        source = payload.get("source", "demo")
        if source == "demo":
            project, scenario = self.get_project_and_scenario_by_ids(
                payload.get("project_id", ""),
                payload.get("scenario_id", "")
            )
            return project.name, scenario.name, scenario.data, [], None, None
        if source not in ("tygron", "tygron_project"):
            raise ValueError("Onbekende gegevensbron.")

        session = None
        if source == "tygron_project":
            # root = TygronRootClient(
            #     payload.get("base_url", ""),
            #     payload.get("username", ""),
            #     payload.get("login_key", ""),
            # )
            # session = root.open_project(payload.get("project_file", ""))

            session = self.tygron_service.open_project_from_root(
                ProjectCredentials(
                    payload.get("base_url", ""),
                    payload.get("username", ""),
                    payload.get("login_key", ""),
                ),
                payload.get("project_file", ""),
            )
            client = session.client
        else:
            # client = TygronClient(payload.get("base_url", ""), payload.get("token", ""))
            client = self.tygron_service.fetch_active_session(
                ActiveSessionCredentials(payload.get("base_url", ""), payload.get("token", ""))
            )
        try:
            data, warnings = client.fetch_all()
        except Exception:
            if session:
                session.close()
            raise
        project = payload.get("project_name", "").strip()
        scenario = payload.get("scenario_name", "").strip()
        if not project or not scenario:
            if session:
                session.close()
            raise ValueError("Selecteer een project en scenario.")
        return project, scenario, data, warnings, client, session

