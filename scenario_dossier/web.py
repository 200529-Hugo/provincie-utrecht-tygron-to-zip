from __future__ import annotations

import json
import mimetypes
import os
import tempfile
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from .exporter import build_archive, load_demo
from .tygron import TygronClient, TygronError, TygronRootClient
from .validation import validate_archive

ROOT = Path(__file__).parent.parent
STATIC = ROOT / "static"
EXPORTS = ROOT / "exports"
COMPONENTS = ("overlays", "indicators", "measures", "alerts")


def _properties(item):
    if item.get("type") == "Feature":
        return item.get("properties") or {}
    return item


def _item_key(item, index):
    item_id = _properties(item).get("id")
    return f"id:{item_id}" if item_id is not None else f"index:{index}"


def _item_inventory(data):
    inventory = []
    for component in COMPONENTS:
        for index, item in enumerate(data.get(component, [])):
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
                "component": component,
                "name": str(props.get("name", props.get("shortName", f"{component} {index + 1}"))),
                "detail": detail[:240],
                "spatial": bool(geometry),
                "geometry_type": geometry.get("type", "") if isinstance(geometry, dict) else "",
            })
    return inventory


def _select_data(data, selected_components=None, selected_items=None):
    components = selected_components if isinstance(selected_components, list) else list(COMPONENTS)
    item_selection = selected_items if isinstance(selected_items, dict) else None
    result = {}
    for component in COMPONENTS:
        items = data.get(component, []) if component in components else []
        if item_selection is not None and component in item_selection:
            wanted = {str(key) for key in item_selection[component]}
            items = [
                item for index, item in enumerate(items)
                if _item_key(item, index) in wanted
            ]
        result[component] = items
    return result


def _demo_scenario(project_id: str, scenario_id: str):
    for project in load_demo()["projects"]:
        if project["id"] == project_id:
            for scenario in project["scenarios"]:
                if scenario["id"] == scenario_id:
                    return project, scenario
    raise ValueError("Project of scenario niet gevonden.")


def _resolve(p):
    source = p.get("source", "demo")
    if source == "demo":
        project, scenario = _demo_scenario(p.get("project_id", ""), p.get("scenario_id", ""))
        return project["name"], scenario["name"], scenario["data"], [], None, None
    if source not in ("tygron", "tygron_project"):
        raise ValueError("Onbekende gegevensbron.")

    session = None
    if source == "tygron_project":
        root = TygronRootClient(
            p.get("base_url", ""),
            p.get("username", ""),
            p.get("login_key", ""),
        )
        session = root.open_project(p.get("project_file", ""))
        client = session.client
    else:
        client = TygronClient(p.get("base_url", ""), p.get("token", ""))
    try:
        data, warnings = client.fetch_all()
    except Exception:
        if session:
            session.close()
        raise
    project = p.get("project_name", "").strip()
    scenario = p.get("scenario_name", "").strip()
    if not project or not scenario:
        if session:
            session.close()
        raise ValueError("Selecteer een project en scenario.")
    return project, scenario, data, warnings, client, session


class Handler(BaseHTTPRequestHandler):
    server_version = "ScenarioDossier/1.0"

    def log_message(self, fmt, *args):
        # Bewust geen request bodies of tokens loggen.
        print(f"{self.address_string()} - {fmt % args}")

    def _json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length > 1_000_000:
            raise ValueError("Verzoek is te groot.")
        return json.loads(self.rfile.read(length) or b"{}")

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/werkinstructie":
            file = ROOT / "docs" / "WERKINSTRUCTIE.md"
            body = file.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/markdown; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            return self.wfile.write(body)
        if path in ("/werkinstructie", "/werkinstructie/"):
            path = "/werkinstructie.html"
        if path in ("/controle", "/controle/"):
            path = "/controle.html"
        if path == "/api/demo":
            demo = load_demo()
            public = {"projects": [
                {
                    "id": p["id"],
                    "name": p["name"],
                    "scenarios": [
                        {
                            k: s[k] for k in ("id", "name", "description")
                        } for s in p["scenarios"]
                    ]
                } for p in demo["projects"]
            ]}
            return self._json(public)
        if path == "/api/map-config":
            return self._json({
                "style_url": os.environ.get(
                    "OPENMAPTILES_STYLE_URL",
                    "http://127.0.0.1:8081/styles/OSM%20OpenMapTiles/style.json",
                )
            })
        if path.startswith("/api/download/"):
            name = Path(unquote(path.split("/api/download/", 1)[1])).name
            file = EXPORTS / name
            if not file.is_file() or file.suffix != ".zip":
                return self._json({"error": "Export niet gevonden."}, 404)
            body = file.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/zip")
            self.send_header("Content-Disposition", f'attachment; filename="{file.name}"')
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            return self.wfile.write(body)
        if path == "/":
            path = "/index.html"
        file = (STATIC / path.lstrip("/")).resolve()
        if STATIC.resolve() not in file.parents or not file.is_file():
            return self._json({"error": "Niet gevonden."}, 404)
        body = file.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(file.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        return None

    def do_POST(self):
        try:
            path = urlparse(self.path).path
            if path == "/api/validate":
                return self._validate_archive()
            payload = self._body()
            if path == "/api/inspect":
                return self._inspect(payload)
            if path == "/api/export":
                return self._export(payload)
            if path == "/api/tygron/projects":
                return self._tygron_projects(payload)
            return self._json({"error": "Niet gevonden."}, 404)
        except (ValueError, TygronError) as exc:
            return self._json({"error": str(exc)}, 400)
        except Exception as exc:
            print(f"Interne fout: {type(exc).__name__}: {exc}")
            return self._json({"error": "De bewerking is onverwacht mislukt."}, 500)

    def _validate_archive(self):
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0:
            raise ValueError("Selecteer een ZIP-dossier om te controleren.")
        if length > 200_000_000:
            raise ValueError("Het ZIP-dossier is groter dan 200 MB.")
        body = self.rfile.read(length)
        if len(body) != length:
            raise ValueError("Het ZIP-dossier is niet volledig ontvangen.")
        with tempfile.TemporaryDirectory(prefix="scenario-dossier-upload-") as temp:
            archive = Path(temp) / "dossier.zip"
            archive.write_bytes(body)
            return self._json(validate_archive(archive))

    def _tygron_projects(self, p):
        root = TygronRootClient(
            p.get("base_url", ""),
            p.get("username", ""),
            p.get("login_key", ""),
        )
        projects = root.list_projects(p.get("domain", ""))
        public = []
        for project in projects:
            file_name = project.get("fileName") or project.get("filename") or project.get("name")
            name = project.get("name") or project.get("displayName") or file_name
            versions = project.get("versions") or ["Actieve versie"]
            try:
                active_version = int(project.get("activeVersion", 0))
            except (TypeError, ValueError):
                active_version = 0
            active_name = versions[active_version] if 0 <= active_version < len(versions) else "Actieve versie"
            public.append({
                "file_name": file_name,
                "name": name,
                # De root-API start de actieve projectversie; toon daarom geen
                # historische versie alsof die met deze route te openen is.
                "versions": [active_name],
                "active_version": 0,
            })
        return self._json({"projects": public})

    def _inspect(self, p):
        project, scenario, data, warnings, _, session = _resolve(p)
        try:
            spatial = sum(1 for group in data.values() for item in group if item.get("geometry"))
            preview = []
            for name in ("measures", "alerts"):
                for index, item in enumerate(data.get(name, [])):
                    if item.get("geometry"):
                        preview.append({
                            "component": name,
                            "key": _item_key(item, index),
                            "feature": item,
                        })
            return self._json({
                "project": project,
                "scenario": scenario,
                "counts": {
                    key: len(data.get(key, []))
                    for key in COMPONENTS
                },
                "spatial": spatial,
                "warnings": warnings,
                "preview": preview,
                "items": _item_inventory(data),
            })
        finally:
            if session:
                session.close()

    def _export(self, p):
        project, scenario, data, warnings, client, session = _resolve(p)
        try:
            data = _select_data(data, p.get("components"), p.get("selected_items"))
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
            return self._json(
                {
                    "ok": True,
                    "filename": archive.name,
                    "download": f"/api/download/{archive.name}",
                    "summary": summary,
                },
                HTTPStatus.CREATED,
            )
        finally:
            if session:
                session.close()


def serve(host="127.0.0.1", port=8080):
    print(f"ScenarioDossier draait op http://{host}:{port}")
    print("Stoppen: Ctrl+C")
    ThreadingHTTPServer((host, port), Handler).serve_forever()
