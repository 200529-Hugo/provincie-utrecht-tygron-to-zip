"""Gedeeld HTTP-transport zonder project-, sessie- of exportlogica."""

import json
import urllib.error
import urllib.parse
import urllib.request

from .errors import TygronError


class CredentialRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Stuur Authorization nooit door naar een andere bestemming.
        raise urllib.error.HTTPError(req.full_url, code, 'Authenticated redirects are disabled', headers, fp)


def validate_base_url(value: str) -> str:
    parsed = urllib.parse.urlsplit(value.strip())
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise TygronError('Gebruik een Tygron-URL zonder inloggegevens of queryparameters.')
    local_http = parsed.scheme == 'http' and parsed.hostname in ('localhost', '127.0.0.1', '::1')
    if not parsed.hostname or (parsed.scheme != 'https' and not local_http):
        raise TygronError('Gebruik een HTTPS-adres voor Tygron.')
    return value.strip().rstrip('/')


def read_response(request, opener, timeout, *, binary=False, max_bytes=None, allow_text=False):
    try:
        with opener(request, timeout=timeout) as response:
            body = response.read(max_bytes + 1) if max_bytes else response.read()
        if max_bytes and len(body) > max_bytes:
            raise TygronError('Het Tygron-antwoord is te groot.')
        if binary:
            return body
        raw = body.decode('utf-8')
        if not raw and allow_text:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            if allow_text:
                return raw.strip().strip('"')
            raise
    except urllib.error.HTTPError as error:
        raise TygronError(f'Tygron antwoordde met HTTP {error.code}.', status_code=error.code) from error
    except (urllib.error.URLError, TimeoutError) as error:
        raise TygronError('Tygron is niet bereikbaar.') from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise TygronError('Onverwacht antwoord van Tygron.') from error
