from flask import current_app, g, session

from . import api
from ..http.contracts import api_endpoint
from ..models.api.requests.auth import LoginRequest, LogoutRequest, SessionStatusRequest
from ..models.api.responses.auth import LoginResponse, LogoutResponse, SessionStatusResponse


@api_endpoint(api, '/auth/login', LoginRequest, LoginResponse, method='POST')
def login(payload):
    controller = current_app.extensions['controllers']['auth']
    token = controller.login(payload, session.get('account_id'))
    session.clear()
    session['account_id'] = token
    return LoginResponse()


@api_endpoint(api, '/auth/logout', LogoutRequest, LogoutResponse, method='POST')
def logout(payload):
    current_app.extensions['controllers']['auth'].logout(session.pop('account_id', None))
    session.clear()
    return LogoutResponse()


@api_endpoint(api, '/auth/session', SessionStatusRequest, SessionStatusResponse)
def account_session(payload):
    return SessionStatusResponse(authenticated=bool(g.account))
