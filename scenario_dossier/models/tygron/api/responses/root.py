from dataclasses import dataclass, field
from typing import Any

from .....integrations.tygron.errors import TygronError


@dataclass(frozen=True)
class LoginKeyResponse:
    key: str = field(repr=False)

    @classmethod
    def from_api(cls, value):
        if (not isinstance(value, str) or not value.strip() or len(value) > 4096
                or any(character.isspace() or character in '<>"' for character in value)):
            raise TygronError('Tygron gaf geen geldige login key terug.')
        return cls(value.strip())


@dataclass(frozen=True)
class UserResponse:
    details: dict[str, Any] = field(repr=False)

    @property
    def domain(self):
        return str(self.details.get('domain') or self.details.get('domainName') or '').strip()

    @classmethod
    def from_api(cls, value):
        if not isinstance(value, dict):
            raise TygronError('Tygron gaf geen bruikbare gebruikersinformatie terug.')
        return cls(value)


@dataclass(frozen=True)
class StartableProjectsResponse:
    projects: list[dict[str, Any]]

    @classmethod
    def from_api(cls, value):
        if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
            raise TygronError('Tygron gaf geen projectlijst terug.')
        return cls(value)


@dataclass(frozen=True)
class StartProjectResponse:
    session_id: Any

    @classmethod
    def from_api(cls, value):
        if value is None:
            raise TygronError('Tygron gaf geen sessie-ID terug.')
        return cls(value)


@dataclass(frozen=True)
class JoinSessionResponse:
    api_token: str = field(repr=False)
    client_token: str = field(repr=False)

    @classmethod
    def from_api(cls, value):
        if not isinstance(value, dict):
            raise TygronError('Tygron gaf na het joinen geen sessietokens terug.')
        api_token = value.get('apiToken') or value.get('token')
        client = value.get('client')
        client_token = value.get('clientToken')
        if not client_token and isinstance(client, dict):
            client_token = client.get('clientToken')
        if not api_token or not client_token:
            raise TygronError('API-token of client-token ontbreekt in het Tygron-antwoord.')
        return cls(str(api_token), str(client_token))


@dataclass(frozen=True)
class CloseSessionResponse:
    closed: bool = True

    @classmethod
    def from_api(cls, value):
        return cls()
