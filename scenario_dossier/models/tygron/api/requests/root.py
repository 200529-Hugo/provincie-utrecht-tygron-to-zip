from dataclasses import dataclass, field
from typing import Any, ClassVar


@dataclass(frozen=True)
class LoginKeyRequest:
    path: ClassVar[str] = '/api/event/user/get_my_login_key/?f=JSON'

    def to_payload(self):
        return None


@dataclass(frozen=True)
class UserRequest:
    path: ClassVar[str] = '/api/event/user/get_my_user/?f=JSON'

    def to_payload(self):
        return None


@dataclass(frozen=True)
class StartableProjectsRequest:
    domain: str
    path: ClassVar[str] = '/api/event/io/get_domain_startable_projects/?f=JSON'

    def to_payload(self) -> str:
        return self.domain


@dataclass(frozen=True)
class StartProjectRequest:
    file_name: str
    role: str = 'EDITOR'
    path: ClassVar[str] = '/api/event/io/start/?f=JSON'

    def to_payload(self) -> list:
        return [self.role, self.file_name]


@dataclass(frozen=True)
class JoinSessionRequest:
    session_id: Any
    role: str = 'EDITOR'
    client_name: str = 'ScenarioDossier'
    path: ClassVar[str] = '/api/event/io/join/?f=JSON'

    def to_payload(self) -> list:
        return [self.session_id, self.role, self.client_name]


@dataclass(frozen=True)
class CloseSessionRequest:
    session_id: Any
    client_token: str = field(repr=False)
    keep_alive: bool = False
    path: ClassVar[str] = '/api/event/io/close/?f=JSON'

    def to_payload(self) -> list:
        return [self.session_id, self.client_token, self.keep_alive]
