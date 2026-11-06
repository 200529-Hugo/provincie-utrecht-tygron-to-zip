"""Tygron-clients met expliciete payloads en antwoorden voor iedere aanroep.

Transport staat in integrations/tygron en de API-modellen in models/tygron/api.
Dit importpad blijft bestaan voor bestaande scripts en tests.
"""

from __future__ import annotations

import base64
import json
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from .integrations.tygron.alerts import _warning_alert, _panel_alert
from .integrations.tygron.errors import TygronError
from .integrations.tygron.transport import (
    CredentialRedirectHandler as _CredentialRedirectHandler,
    read_response,
    validate_base_url as _validate_base_url,
)
from .models.tygron.api.requests.root import (
    CloseSessionRequest, JoinSessionRequest, LoginKeyRequest,
    StartableProjectsRequest, StartProjectRequest, UserRequest,
)
from .models.tygron.api.responses.root import (
    CloseSessionResponse, JoinSessionResponse, LoginKeyResponse,
    StartableProjectsResponse, StartProjectResponse, UserResponse,
)
from .models.tygron.api.requests.session import ComponentRequest, OverlayGeoTiffRequest
from .models.tygron.api.responses.session import ComponentResponse, OverlayGeoTiffResponse
from .models.tygron.api.requests.wms import WmsCapabilitiesRequest, WmsMapRequest
from .models.tygron.api.responses.wms import WmsCapabilitiesResponse, WmsMapResponse


def _open_authenticated(request, timeout):
    return urllib.request.build_opener(_CredentialRedirectHandler()).open(request, timeout=timeout)


@dataclass
class TygronClient:
    """Lees de gegevens van een al geopende Tygron-sessie."""

    base_url: str
    token: str = field(repr=False)
    timeout: int = 25

    def __post_init__(self):
        self.base_url = _validate_base_url(self.base_url)
        if not self.token.strip():
            raise TygronError('Een API-token is verplicht.')

    def _get(self, path: str, binary=False, max_bytes=None):
        request = urllib.request.Request(
            f'{self.base_url}{path}',
            headers={'Authorization': f'Bearer {self.token}',
                     'Accept': '*/*' if binary else 'application/json'},
        )
        return read_response(request, _open_authenticated, self.timeout,
                             binary=binary, max_bytes=max_bytes)

    def fetch_component(self, name: str, output_format='JSON', crs=None) -> list[dict[str, Any]]:
        payload = ComponentRequest(name, output_format, crs)
        return ComponentResponse.from_api(self._get(payload.path), name).items

    def fetch_all(self):
        warnings = []
        components = {
            'overlays': self.fetch_component('overlays'),
            'indicators': self.fetch_component('indicators'),
            'measures': self.fetch_component('measures', 'GEOJSON', 4326),
        }
        try:
            panels = self.fetch_component('panels', 'JSON', 4326)
        except TygronError as error:
            panels = []
            warnings.append(f'Panel-attenties konden niet worden opgehaald: {error}')
        alerts = []
        for name, items in components.items():
            for item in items:
                alert = _warning_alert(name, item)
                if alert:
                    alerts.append(alert)
        for panel in panels:
            alert = _panel_alert(panel)
            if alert:
                alerts.append(alert)
        components['alerts'] = alerts
        if not alerts:
            warnings.append('Geen waarschuwingen of panel-attenties in deze sessie gevonden.')
        return components, warnings

    def fetch_map_thumbnail(self) -> bytes:
        payload = WmsCapabilitiesRequest()
        document = self._get(payload.path, binary=True, max_bytes=payload.max_bytes)
        capabilities = WmsCapabilitiesResponse.from_bytes(document)
        payload = WmsMapRequest.from_project_bounds(capabilities.bounds)
        image = self._get(payload.path, binary=True, max_bytes=payload.max_bytes)
        return WmsMapResponse.from_bytes(image, payload.width, payload.height).data

    def fetch_overlay_geotiff(self, overlay_id: int) -> bytes:
        payload = OverlayGeoTiffRequest(overlay_id)
        return OverlayGeoTiffResponse.from_bytes(self._get(payload.path, binary=True)).data


@dataclass
class TygronRootClient:
    """Authenticeer een account en open projecten tijdelijk via de root-API."""

    base_url: str
    username: str
    login_key: str = field(repr=False)
    timeout: int = 45

    def __post_init__(self):
        self.base_url = _validate_base_url(self.base_url)
        if not self.username.strip() or not self.login_key.strip():
            raise TygronError('Gebruikersnaam en login key zijn verplicht.')

    @property
    def _authorization(self):
        credentials = f'{self.username}:{self.login_key}'.encode('utf-8')
        return 'Basic ' + base64.b64encode(credentials).decode('ascii')

    def _post(self, path, payload=None):
        body = b'' if payload is None else json.dumps(payload).encode('utf-8')
        request = urllib.request.Request(
            f'{self.base_url}{path}', data=body, method='POST',
            headers={'Authorization': self._authorization, 'Content-Type': 'application/json',
                     'Accept': 'application/json'},
        )
        return read_response(request, _open_authenticated, self.timeout, allow_text=True)

    def _event(self, payload, response_model):
        return response_model.from_api(self._post(payload.path, payload.to_payload()))

    def get_login_key(self) -> str:
        return self._event(LoginKeyRequest(), LoginKeyResponse).key

    def get_user(self) -> dict[str, Any]:
        return self._event(UserRequest(), UserResponse).details

    def list_projects(self, domain='') -> list[dict[str, Any]]:
        domain_name = domain.strip() or UserResponse.from_api(self.get_user()).domain
        if not domain_name:
            raise TygronError('Domeinnaam ontbreekt en kon niet uit het Tygron-account worden bepaald.')
        return self._event(StartableProjectsRequest(domain_name), StartableProjectsResponse).projects

    def open_project(self, file_name: str) -> 'TygronRootSession':
        if not file_name.strip():
            raise TygronError('Selecteer een Tygron-project.')
        started = self._event(StartProjectRequest(file_name), StartProjectResponse)
        joined = self._event(JoinSessionRequest(started.session_id), JoinSessionResponse)
        return TygronRootSession(self, started.session_id, joined.client_token, joined.api_token)

    def close(self, session_id, client_token):
        self._event(CloseSessionRequest(session_id, client_token), CloseSessionResponse)


@dataclass
class TygronRootSession:
    """Een with-blok sluit de tijdelijke sessie ook bij een fout."""

    root: TygronRootClient
    session_id: Any
    client_token: str = field(repr=False)
    api_token: str = field(repr=False)
    closed: bool = False

    @property
    def client(self) -> TygronClient:
        return TygronClient(self.root.base_url, self.api_token)

    def close(self):
        if not self.closed:
            self.root.close(self.session_id, self.client_token)
            self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
