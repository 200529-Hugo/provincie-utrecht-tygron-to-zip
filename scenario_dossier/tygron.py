from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

'''
This module provides a client for interacting with the Tygron API, allowing users to fetch components, overlays, and manage sessions.
'''


# Custom exception for Tygron-related errors
class TygronError(RuntimeError):
    pass


# Helper function to validate the base URL for Tygron API access
def _validate_base_url(value: str) -> str:
    base_url = value.rstrip("/")
    # Ensure the base URL starts with HTTPS or is a localhost address
    if not base_url.startswith("https://") and not base_url.startswith("http://localhost"):
        raise TygronError("Gebruik een HTTPS-adres voor Tygron.")
    return base_url


# Helper function to extract properties from a Tygron item, handling both Feature and non-Feature types
def _item_properties(item: dict[str, Any]) -> dict[str, Any]:
    if item.get("type") == "Feature":
        return item.get("properties", {})
    return item


# Helper function to create a warning alert from a Tygron component item
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


# Helper function to create an alert for a Tygron panel that requires attention
def _panel_alert(panel: dict[str, Any]) -> dict[str, Any] | None:
    props = _item_properties(panel)
    attention = (props.get("attributes") or {}).get("ATTENTION", [0])
    if not attention or float(attention[0]) <= 0:
        return None

    # Create an alert dictionary with relevant information about the panel
    alert: dict[str, Any] = {
        "id": f"panel-{props.get('id', 'onbekend')}",
        "name": props.get("name") or "Tygron-attentie",
        "severity": "attention",
        "status": "open",
        "description": props.get("warnings") or props.get("text") or "Panel vraagt aandacht.",
        "source": "panels",
    }

    # If the panel has a geometry (point or polygons), include it in the alert as a GeoJSON Feature
    geometry = props.get("point") or props.get("polygons")
    if geometry:
        return {"type": "Feature", "geometry": geometry, "properties": alert}
    return alert


# The TygronClient class provides methods to interact with the Tygron API, including fetching components and overlays.
@dataclass
class TygronClient:
    # The base URL of the Tygron API (must be HTTPS or localhost)
    base_url: str
    # The API token used for authentication with the Tygron API
    token: str
    # The timeout in seconds for API requests (default is 25 seconds)
    timeout: int = 25

    # Post-initialization method to validate the base URL and ensure the API token is provided
    def __post_init__(self) -> None:
        self.base_url = _validate_base_url(self.base_url)
        if not self.token.strip():
            raise TygronError("Een API-token is verplicht.")

    # Internal method to perform a GET request to the Tygron API, handling errors and returning the response data.
    def _get(self, path: str, binary: bool = False) -> Any:
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            headers={"Authorization": f"Bearer {self.token}", "Accept": "application/json"},
        )
        # Handle the request and catch potential errors, raising TygronError with appropriate messages
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

    # Fetch a specific component from the Tygron API, returning a list of dictionaries representing the component's features or items.
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
        # Perform the GET request to fetch the component data from the Tygron API
        data = self._get(f"/api/session/items/{name}/?{encoded}")
        if isinstance(data, dict) and data.get("type") == "FeatureCollection":
            return data.get("features", [])
        if not isinstance(data, list):
            raise TygronError(f"Component {name} heeft geen verwachte lijststructuur.")
        return data

    # Fetch all relevant components (overlays, indicators, measures, panels) from the Tygron API and return them along with any warnings encountered during the fetch process.
    def fetch_all(self) -> tuple[dict[str, list[dict[str, Any]]], list[str]]:
        warnings: list[str] = []
        components = {
            "overlays": self.fetch_component("overlays"),
            "indicators": self.fetch_component("indicators"),
            "measures": self.fetch_component("measures", "GEOJSON", 4326),
        }

        # Attempt to fetch panel attentions, handling any errors and appending warnings if necessary
        try:
            panels = self.fetch_component("panels", "JSON", 4326)
        except TygronError as exc:
            panels = []
            warnings.append(f"Panel-attenties konden niet worden opgehaald: {exc}")

        # Generate alerts for any warnings found in the components and panels, appending them to the alerts list
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

        # If no alerts were found, add a warning message indicating that no warnings or panel attentions were found in the session
        if not alerts:
            warnings.append("Geen waarschuwingen of panel-attenties in deze sessie gevonden.")
        return components, warnings

    # Fetch a specific overlay in GeoTIFF format from the Tygron API, returning the binary data of the GeoTIFF file.
    def fetch_overlay_geotiff(self, overlay_id: int) -> bytes:
        query = urllib.parse.urlencode({"id": overlay_id})
        return self._get(f"/api/session/overlay.geotiff?{query}", binary=True)


# The TygronRootClient class provides methods to interact with the Tygron root API, allowing users to authenticate, list projects, and manage sessions.
@dataclass
class TygronRootClient:
    # The base URL of the Tygron root API (must be HTTPS or localhost)
    base_url: str
    # The username used for authentication with the Tygron root API
    username: str
    # The login key used for authentication with the Tygron root API
    login_key: str
    # The timeout in seconds for API requests (default is 45 seconds)
    timeout: int = 45

    # Post-initialization method to validate the base URL and ensure the username and login key are provided
    def __post_init__(self) -> None:
        self.base_url = _validate_base_url(self.base_url)
        if not self.username.strip() or not self.login_key.strip():
            raise TygronError("Gebruikersnaam en login key zijn verplicht.")

    # Generate the authorization header for the Tygron root API using Basic Authentication with the provided username and login key.
    @property
    def _authorization(self) -> str:
        credentials = f"{self.username}:{self.login_key}".encode("utf-8")
        return "Basic " + base64.b64encode(credentials).decode("ascii")

    # Internal method to perform a POST request to the Tygron root API, handling errors and returning the response data.
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

        # Handle the request and catch potential errors, raising TygronError with appropriate messages
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

    # Fetch the current user's information from the Tygron root API, returning a dictionary containing user details.
    def get_user(self) -> dict[str, Any]:
        user = self._post("/api/event/user/get_my_user/?f=JSON")
        if not isinstance(user, dict):
            raise TygronError("Tygron gaf geen bruikbare gebruikersinformatie terug.")
        return user

    # List all startable projects for a given domain from the Tygron root API, returning a list of dictionaries representing the projects.
    def list_projects(self, domain: str = "") -> list[dict[str, Any]]:
        domain_name = domain.strip()
        if not domain_name:
            user = self.get_user()
            domain_name = str(user.get("domain") or user.get("domainName") or "").strip()
        if not domain_name:
            raise TygronError("Domeinnaam ontbreekt en kon niet uit het Tygron-account worden bepaald.")

        # Fetch the list of startable projects for the specified domain from the Tygron root API
        projects = self._post(
            "/api/event/io/get_domain_startable_projects/?f=JSON",
            domain_name,
        )
        if not isinstance(projects, list):
            raise TygronError("Tygron gaf geen projectlijst terug.")
        return projects

    # Open a Tygron project by its file name, starting a session and returning a TygronRootSession object for further interaction with the project.
    def open_project(self, file_name: str) -> "TygronRootSession":
        if not file_name.strip():
            raise TygronError("Selecteer een Tygron-project.")
        session_id = self._post("/api/event/io/start/?f=JSON", ["EDITOR", file_name])
        # Check if the session ID is valid and raise an error if not
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

    # Close a Tygron session by its session ID and client token, terminating the session on the Tygron server.
    def close(self, session_id: Any, client_token: str) -> None:
        self._post("/api/event/io/close/?f=JSON", [session_id, client_token, False])


# The TygronRootSession class represents an active session with the Tygron API, providing methods to access the TygronClient and manage the session lifecycle.
@dataclass
class TygronRootSession:
    # The TygronRootClient instance used to interact with the Tygron root API
    root: TygronRootClient
    # The session ID for the active Tygron session
    session_id: Any
    # The client token for the active Tygron session, used for authentication with the Tygron API
    client_token: str
    # The API token for the active Tygron session, used for authentication with the Tygron API
    api_token: str
    # A flag indicating whether the session has been closed (default is False)
    closed: bool = False

    # The client property returns a TygronClient instance configured with the base URL and API token for the active session, allowing users to interact with the Tygron API.
    @property
    def client(self) -> TygronClient:
        return TygronClient(self.root.base_url, self.api_token)

    # Close the Tygron session if it has not already been closed, ensuring that resources are released on the Tygron server.
    def close(self) -> None:
        if not self.closed:
            self.root.close(self.session_id, self.client_token)
            self.closed = True

    # Context manager entry method, allowing the TygronRootSession to be used with a 'with' statement for automatic resource management.
    def __enter__(self) -> "TygronRootSession":
        return self

    # Context manager exit method, ensuring that the Tygron session is closed when exiting the 'with' block.
    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
