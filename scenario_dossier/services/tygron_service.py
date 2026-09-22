from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from ..models import (
    ActiveSessionCredentials,
    ProjectCredentials,
    ScenarioData,
    TygronConnection,
    TygronFetchResult,
    TygronProject,
)
from ..tygron import TygronClient, TygronRootClient


class TygronService:
    def list_projects(self, credentials: ProjectCredentials) -> list[TygronProject]:
        client = self._root_client(credentials)
        return [
            TygronProject.from_api(item)
            for item in client.list_projects(credentials.domain)
        ]

    def fetch_active_session(
        self,
        credentials: ActiveSessionCredentials,
    ) -> TygronFetchResult:
        data, warnings = self._active_client(credentials).fetch_all()
        return TygronFetchResult(ScenarioData.from_dict(data), warnings)

    def active_connection(
        self,
        credentials: ActiveSessionCredentials,
    ) -> TygronConnection:
        client = self._active_client(credentials)
        data, warnings = client.fetch_all()
        return TygronConnection(
            data=ScenarioData.from_dict(data),
            warnings=warnings,
            raster_fetcher=client.fetch_overlay_geotiff,
        )

    @contextmanager
    def project_connection(
        self,
        credentials: ProjectCredentials,
        file_name: str,
    ) -> Iterator[TygronConnection]:
        root = self._root_client(credentials)
        with root.open_project(file_name) as session:
            client = session.client
            data, warnings = client.fetch_all()
            yield TygronConnection(
                data=ScenarioData.from_dict(data),
                warnings=warnings,
                raster_fetcher=client.fetch_overlay_geotiff,
            )

    @staticmethod
    def _active_client(credentials: ActiveSessionCredentials) -> TygronClient:
        return TygronClient(credentials.base_url, credentials.token)

    @staticmethod
    def _root_client(credentials: ProjectCredentials) -> TygronRootClient:
        return TygronRootClient(
            credentials.base_url,
            credentials.username,
            credentials.login_key,
        )
