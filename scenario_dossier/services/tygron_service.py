from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from threading import RLock
from weakref import WeakValueDictionary

from scenario_dossier.tygron import TygronRootSession
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
    # Preview, controle en export mogen hetzelfde project niet tegelijk openen.
    _session_locks = WeakValueDictionary()
    _session_locks_guard = RLock()

    @contextmanager
    def project_session(self, credentials, file_name):
        key = (credentials.base_url.rstrip('/'), file_name)
        with self._session_locks_guard:
            lock = self._session_locks.get(key)
            if lock is None:
                lock = RLock()
                self._session_locks[key] = lock
        with lock:
            with self._root_client(credentials).open_project(file_name) as session:
                yield session

    def project_thumbnail(self, credentials, file_name):
        with self.project_session(credentials, file_name) as session:
            return session.client.fetch_map_thumbnail()

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
        connection = self.active_connection(credentials)
        return TygronFetchResult(connection.data, connection.warnings)

    def active_connection(
        self,
        credentials: ActiveSessionCredentials,
    ) -> TygronConnection:
        return self._connection(self._active_client(credentials))

    @staticmethod
    def _connection(client: TygronClient) -> TygronConnection:
        data, warnings = client.fetch_all()
        return TygronConnection(
            data=ScenarioData.from_dict(data),
            warnings=warnings,
            raster_fetcher=client.fetch_overlay_geotiff,
        )

    def open_project_from_root(
        self,
        credentials: ProjectCredentials,
        file_name: str
    ) -> "TygronRootSession":
        root = self._root_client(credentials)
        return root.open_project(file_name)

    @contextmanager
    def project_connection(
        self,
        credentials: ProjectCredentials,
        file_name: str,
    ) -> Iterator[TygronConnection]:
        with self.project_session(credentials, file_name) as session:
            yield self._connection(session.client)

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
