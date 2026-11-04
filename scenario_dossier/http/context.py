from flask import g, request, session
from werkzeug.exceptions import Unauthorized

from ..i18n import CATALOGS, translate
from ..models.api.responses.common import ErrorResponse
from .responses import model_response


def current_account():
    if g.account is None:
        raise Unauthorized()
    return g.account


def register_request_context(app):
    @app.before_request
    def prepare_request():
        g.language = request.cookies.get('language', 'nl')
        if g.language not in CATALOGS:
            g.language = 'nl'
        g.account = app.extensions['auth'].get(session.get('account_id'))
        if request.method == 'POST':
            origin = request.headers.get('Origin')
            if origin and origin != request.host_url.rstrip('/'):
                return model_response(ErrorResponse(translate('Dit verzoek is niet toegestaan.', g.language)), 403)

    @app.context_processor
    def template_context():
        return {'t': lambda text: translate(text, g.language), 'language': g.language,
                'catalog': CATALOGS['nl'] | CATALOGS[g.language], 'account': g.account}

    @app.after_request
    def response_headers(response):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Referrer-Policy'] = 'same-origin'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response
