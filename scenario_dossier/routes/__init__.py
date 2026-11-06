"""Routes zijn per onderwerp verdeeld en bevatten alleen HTTP-doorverwijzingen."""

from flask import Blueprint

api = Blueprint('api', __name__, url_prefix='/api')

# Deze imports registreren de routes op dezelfde blueprint.
from . import auth, projects, demo, workflow, files, settings
from .pages import pages

__all__ = ['api', 'pages']
