from flask import Response, jsonify, send_file

from ..models.api.base import JsonModel
from ..models.api.responses.common import FileResponse, ImageResponse, TextResponse


def model_response(model, status=200):
    """Alle API-routes gebruiken dezelfde omzetting naar een HTTP-antwoord."""
    if isinstance(model, ImageResponse):
        if model.data is None:
            return Response(status=204)
        return Response(model.data, mimetype=model.mimetype, status=status)
    if isinstance(model, FileResponse):
        return send_file(model.path, mimetype=model.mimetype, as_attachment=model.as_attachment)
    if isinstance(model, TextResponse):
        return Response(model.content, mimetype=model.mimetype, status=status)
    if isinstance(model, JsonModel):
        return jsonify(model.to_dict()), status
    raise TypeError('Een API-route moet een responsemodel teruggeven.')
