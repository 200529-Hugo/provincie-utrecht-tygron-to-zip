from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


class TygronError(RuntimeError):
    pass


def _validate_base_url(value: str) -> str:
    base_url = value.rstrip("/")
    if not base_url.startswith("https://") and not base_url.startswith("http://localhost"):
        raise TygronError("Gebruik een HTTPS-adres voor Tygron.")
    return base_url


def _item_properties(item: dict[str, Any]) -> dict[str, Any]:
    if item.get("type") == "Feature":
        return item.get("properties", {})
    return item


def _warning_alert(component: str, item: dict[str, Any]) -> dict[str, Any] | None:
    props = _item_properties(item)
    warning = props.get("warnings") or props.get("warning") or props.get("failText")
    if not warning:
        return None
    return {
        "id": f"{component}-{props.get('id', 'onbekend')}",
        "name": f"Waarschuwing bij {props.get('name', component)}",
        "severity": "warning",
        "status": "open",
        "description": str(warning),
        "source": component,
    }


def _panel_alert(panel: dict[str, Any]) -> dict[str, Any] | None:
    props = _item_properties(panel)
    attention = (props.get("attributes") or {}).get("ATTENTION", [0])
    if not attention or float(attention[0]) <= 0:
        return None

    alert: dict[str, Any] = {
        "id": f"panel-{props.get('id', 'onbekend')}",
        "name": props.get("name") or "Tygron-attentie",
        "severity": "attention",
        "status": "open",
        "description": props.get("warnings") or props.get("text") or "Panel vraagt aandacht.",
        "source": "panels",
    }
    geometry = props.get("point") or props.get("polygons")
    if geometry:
        return {"type": "Feature", "geometry": geometry, "properties": alert}
    return alert


@dataclass
class TygronClient:
    base_url: str
    token: str
    timeout: int = 25

    def __post_init__(self) -> None:
        self.base_url = _validate_base_url(self.base_url)
        if not self.token.strip():
            raise TygronError("Een API-token is verplicht.")

    def _get(self, path: str, binary: bool = False) -> Any:
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            headers={"Authorization": f"Bearer {self.token}", "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = response.read()
                if binary:
                    return body
                return json.loads(body.decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise TygronError(f"Tygron antwoordde met HTTP {exc.code} voor {path}.") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            reason = exc.reason if hasattr(exc, "reason") else exc
            raise TygronError(f"Tygron is niet bereikbaar: {reason}") from exc
        except json.JSONDecodeError as exc:
            raise TygronError(f"Onverwacht antwoord van Tygron voor {path}.") from exc

    def fetch_component(
        self,
        name: str,
        output_format: str = "JSON",
        crs: int | None = None,
    ) -> list[dict[str, Any]]:
        query: dict[str, str | int] = {"f": output_format}
        if crs:
            query["crs"] = crs
        encoded = urllib.parse.urlencode(query)
        data = self._get(f"/api/session/items/{name}/?{encoded}")
        if isinstance(data, dict) and data.get("type") == "FeatureCollection":
            return data.get("features", [])
        if not isinstance(data, list):
            raise TygronError(f"Component {name} heeft geen verwachte lijststructuur.")
        return data

    def fetch_all(self) -> tuple[dict[str, list[dict[str, Any]]], list[str]]:
        warnings: list[str] = []
        components = {
            "overlays": self.fetch_component("overlays"),
            "indicators": self.fetch_component("indicators"),
            "measures": self.fetch_component("measures", "GEOJSON", 4326),
        }

        try:
            panels = self.fetch_component("panels", "JSON", 4326)
        except TygronError as exc:
            panels = []
            warnings.append(f"Panel-attenties konden niet worden opgehaald: {exc}")

        alerts: list[dict[str, Any]] = []
        for component_name, items in components.items():
            for item in items:
                alert = _warning_alert(component_name, item)
                if alert:
                    alerts.append(alert)
        for panel in panels:
            alert = _panel_alert(panel)
            if alert:
                alerts.append(alert)

        components["alerts"] = alerts
        if not alerts:
            warnings.append("Geen waarschuwingen of panel-attenties in deze sessie gevonden.")
        return components, warnings

    def fetch_overlay_geotiff(self, overlay_id: int) -> bytes:
        query = urllib.parse.urlencode({"id": overlay_id})
        return self._get(f"/api/session/overlay.geotiff?{query}", binary=True)


@dataclass
class TygronRootClient:
    base_url: str
    username: str
    login_key: str
    timeout: int = 45

    def __post_init__(self) -> None:
        self.base_url = _validate_base_url(self.base_url)
        if not self.username.strip() or not self.login_key.strip():
            raise TygronError("Gebruikersnaam en login key zijn verplicht.")

    @property
    def _authorization(self) -> str:
        credentials = f"{self.username}:{self.login_key}".encode("utf-8")
        return "Basic " + base64.b64encode(credentials).decode("ascii")

    def _post(self, path: str, payload: Any = None) -> Any:
        body = b"" if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=body,
            method="POST",
            headers={
                "Authorization": self._authorization,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
                if not raw:
                    return None
                try:
                    return json.loads(raw)
                except json.JSONDecodeError:
                    return raw.strip().strip('"')
        except urllib.error.HTTPError as exc:
            raise TygronError(f"Tygron root API antwoordde met HTTP {exc.code} voor {path}.") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            reason = exc.reason if hasattr(exc, "reason") else exc
            raise TygronError(f"Tygron root API is niet bereikbaar: {reason}") from exc

    def get_user(self) -> dict[str, Any]:
        user = self._post("/api/event/user/get_my_user/?f=JSON")
        if not isinstance(user, dict):
            raise TygronError("Tygron gaf geen bruikbare gebruikersinformatie terug.")
        return user

    def list_projects(self, domain: str = "") -> list[dict[str, Any]]:
        domain_name = domain.strip()
        if not domain_name:
            user = self.get_user()
            domain_name = str(user.get("domain") or user.get("domainName") or "").strip()
        if not domain_name:
            raise TygronError("Domeinnaam ontbreekt en kon niet uit het Tygron-account worden bepaald.")

        projects = self._post(
            "/api/event/io/get_domain_startable_projects/?f=JSON",
            domain_name,
        )
        if not isinstance(projects, list):
            raise TygronError("Tygron gaf geen projectlijst terug.")
        return projects

    def open_project(self, file_name: str) -> "TygronRootSession":
        if not file_name.strip():
            raise TygronError("Selecteer een Tygron-project.")
        session_id = self._post("/api/event/io/start/?f=JSON", ["EDITOR", file_name])
        joined = self._post(
            "/api/event/io/join/?f=JSON",
            [session_id, "EDITOR", "ScenarioDossier"],
        )
        if not isinstance(joined, dict):
            raise TygronError("Tygron gaf na het joinen geen sessietokens terug.")

        api_token = joined.get("apiToken") or joined.get("token")
        client = joined.get("client")
        client_token = joined.get("clientToken")
        if not client_token and isinstance(client, dict):
            client_token = client.get("clientToken")
        if not api_token or not client_token:
            raise TygronError("API-token of client-token ontbreekt in het Tygron-antwoord.")
        return TygronRootSession(self, session_id, str(client_token), str(api_token))

    def close(self, session_id: Any, client_token: str) -> None:
        self._post("/api/event/io/close/?f=JSON", [session_id, client_token, False])


@dataclass
class TygronRootSession:
    root: TygronRootClient
    session_id: Any
    client_token: str
    api_token: str
    closed: bool = False

    @property
    def client(self) -> TygronClient:
        return TygronClient(self.root.base_url, self.api_token)

    def close(self) -> None:
        if not self.closed:
            self.root.close(self.session_id, self.client_token)
            self.closed = True

    def __enter__(self) -> "TygronRootSession":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
