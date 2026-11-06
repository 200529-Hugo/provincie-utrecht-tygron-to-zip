from dataclasses import dataclass, field

from ..base import EmptyRequest, JsonModel, object_value, text


@dataclass(frozen=True)
class LoginRequest(JsonModel):
    username: str
    password: str = field(repr=False)
    base_url: str = 'https://engine.tygron.com'
    domain: str = ''

    @classmethod
    def from_dict(cls, value: dict) -> 'LoginRequest':
        data = object_value(value)
        return cls(
            username=text(data, 'username'),
            password=text(data, 'password', strip=False),
            base_url=text(data, 'base_url', 'https://engine.tygron.com'),
            domain=text(data, 'domain'),
        )


@dataclass(frozen=True)
class LogoutRequest(EmptyRequest):
    pass


@dataclass(frozen=True)
class SessionStatusRequest(EmptyRequest):
    pass
