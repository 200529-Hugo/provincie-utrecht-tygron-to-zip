"""Lees payloads en koppel iedere API-route aan twee expliciete modellen."""

from dataclasses import dataclass
from functools import wraps

from flask import g, request

from ..models.api.base import EmptyRequest
from .responses import model_response


@dataclass(frozen=True)
class ApiContract:
    path: str
    method: str
    request_model: type
    response_model: type
    endpoint: str


API_CONTRACTS: list[ApiContract] = []


def api_endpoint(blueprint, path, request_model, response_model, *, method='GET'):
    """De route zelf ontvangt een model en hoeft geen JSON te ontleden."""
    def register(handler):
        endpoint = handler.__module__.rsplit('.', 1)[-1] + '_' + handler.__name__
        contract = ApiContract((blueprint.url_prefix or '') + path, method, request_model, response_model, endpoint)
        API_CONTRACTS.append(contract)

        @wraps(handler)
        def handle_request(**path_values):
            if hasattr(request_model, 'from_bytes'):
                payload = request_model.from_bytes(request.get_data())
            elif method == 'POST' and issubclass(request_model, EmptyRequest) and not request.get_data():
                payload = request_model.from_dict({})
            elif method == 'POST':
                payload = request_model.from_dict(request.get_json())
            else:
                payload = request_model.from_dict(dict(request.args) | path_values)
            g.api_payload = payload
            result = handler(payload)
            if not isinstance(result, response_model):
                raise TypeError(f'{endpoint} moet {response_model.__name__} teruggeven.')
            return model_response(result)

        handle_request.api_contract = contract
        blueprint.add_url_rule(path, endpoint=endpoint, view_func=handle_request, methods=[method])
        return handle_request
    return register
