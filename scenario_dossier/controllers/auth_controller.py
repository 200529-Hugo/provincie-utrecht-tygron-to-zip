from ..models.api.requests.auth import LoginRequest


class AuthController:
    def __init__(self, service):
        self.service = service

    def login(self, payload: LoginRequest, previous_session=None) -> str:
        token = self.service.login(payload.base_url, payload.username, payload.password, payload.domain)
        self.service.logout(previous_session)
        return token

    def logout(self, session_id):
        self.service.logout(session_id)
