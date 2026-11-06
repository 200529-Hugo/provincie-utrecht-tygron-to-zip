from flask import g, session
from werkzeug.exceptions import HTTPException

from ..i18n import translate_message
from ..models.api.requests.workflow import InspectRequest
from ..models.api.responses.common import ErrorResponse
from ..tygron import TygronError
from .responses import model_response


def register_error_handlers(app):
    def error_response(message, status):
        return model_response(ErrorResponse(translate_message(message, g.language)), status)

    @app.errorhandler(TygronError)
    def tygron_error(error):
        if error.status_code in (401, 403):
            payload = getattr(g, 'api_payload', None)
            if isinstance(payload, InspectRequest) and payload.source == 'tygron':
                return error_response('De actieve sessie is niet toegankelijk. Controleer de sessie-URL en het API-token.', 401)
            if g.account:
                app.extensions['auth'].logout(session.pop('account_id', None))
                message = 'Je sessie is verlopen. Log opnieuw in.'
            else:
                message = 'Inloggen mislukt. Controleer je gegevens. Neem bij tweestapsverificatie contact op met Tygron Support.'
            return error_response(message, 401)
        # Antwoorden van Tygron kunnen credentials bevatten en blijven intern.
        return error_response('Tygron is niet bereikbaar of gaf een onverwacht antwoord. Probeer opnieuw.', 502)

    @app.errorhandler(ValueError)
    @app.errorhandler(LookupError)
    def input_error(error):
        return error_response(str(error), 400)

    @app.errorhandler(HTTPException)
    def http_error(error):
        messages = {401: 'Je sessie is verlopen. Log opnieuw in.', 404: 'Niet gevonden.'}
        return error_response(messages.get(error.code, 'Het verzoek kon niet worden verwerkt.'), error.code)

    @app.errorhandler(Exception)
    def unexpected_error(error):
        app.logger.error('Request failed: %s', type(error).__name__)
        return error_response('De bewerking is onverwacht mislukt.', 500)
