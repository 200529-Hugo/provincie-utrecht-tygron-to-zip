from dataclasses import dataclass

from ..base import JsonModel


@dataclass(frozen=True)
class LoginResponse(JsonModel):
    ok: bool = True


@dataclass(frozen=True)
class LogoutResponse(JsonModel):
    ok: bool = True


@dataclass(frozen=True)
class SessionStatusResponse(JsonModel):
    authenticated: bool
