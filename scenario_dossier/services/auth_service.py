from secrets import token_urlsafe
from threading import RLock
from time import monotonic

from ..models import ProjectCredentials
from ..models.auth.account_session import AccountSession
from ..tygron import TygronRootClient


class AuthService:
    """Bewaar login keys in het geheugen en geef de browser alleen een sessie-ID."""

    def __init__(self, lifetime=1800):
        self.lifetime = lifetime
        self._sessions = {}
        self._lock = RLock()

    def login(self, base_url, username, password, domain=''):
        if not isinstance(username, str) or not username.strip() or ':' in username:
            raise ValueError('Gebruikersnaam is verplicht.')
        if not isinstance(password, str) or not password:
            raise ValueError('Wachtwoord is verplicht.')
        root = TygronRootClient(base_url, username, password)
        try:
            key = root.get_login_key()
        finally:
            root.login_key = ''
        credentials = ProjectCredentials(base_url, username, key, domain)
        with self._lock:
            self._prune()
            token = token_urlsafe(32)
            self._sessions[token] = AccountSession(credentials, monotonic() + self.lifetime)
        return token

    def _prune(self):
        now = monotonic()
        for token in list(self._sessions):
            if self._sessions[token].expires_at <= now:
                del self._sessions[token]

    def get(self, token):
        with self._lock:
            self._prune()
            return self._sessions.get(token)

    def logout(self, token):
        with self._lock:
            self._sessions.pop(token, None)
