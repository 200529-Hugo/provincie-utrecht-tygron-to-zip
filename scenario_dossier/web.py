"""Bouw de Flask-app door configuratie, controllers en routes te verbinden."""

from flask import Flask

from .config import ROOT, default_config
from .controllers.auth_controller import AuthController
from .controllers.file_controller import FileController
from .controllers.project_controller import ProjectController
from .controllers.settings_controller import SettingsController
from .controllers.workflow_controller import WorkflowController
from .http.context import register_request_context
from .http.errors import register_error_handlers
from .models import ScenarioData
from .routes import api, pages
from .services.auth_service import AuthService
from .services.scenario_service import ScenarioService
from .services.thumbnail_service import ThumbnailService

EXPORTS = ROOT / 'exports'


def _item_inventory(data):
    return [item.to_dict() for item in ScenarioService().inventory(ScenarioData.from_dict(data))]


def _select_data(data, selected_components=None, selected_items=None):
    return ScenarioService().select(data=ScenarioData.from_dict(data),
                                    selected_components=selected_components,
                                    selected_items=selected_items).to_dict()


def create_app(config=None):
    app = Flask(__name__, template_folder=str(ROOT / 'templates'), static_folder=str(ROOT / 'static'))
    app.config.update(default_config())
    app.config.update(config or {})
    auth = AuthService(lifetime=app.config['AUTH_SESSION_LIFETIME'])
    thumbnails = ThumbnailService(lifetime=app.config['THUMBNAIL_LIFETIME'],
                                  failure_lifetime=app.config['THUMBNAIL_FAILURE_LIFETIME'],
                                  capacity=app.config['THUMBNAIL_CAPACITY'],
                                  max_parallel=app.config['THUMBNAIL_CONCURRENCY'],
                                  cache_dir=app.config['THUMBNAIL_CACHE_DIR'])
    app.extensions['auth'] = auth
    app.extensions['thumbnails'] = thumbnails
    app.extensions['controllers'] = {
        'auth': AuthController(auth),
        'projects': ProjectController(thumbnails),
        'workflow': WorkflowController(app.config['EXPORT_DIR']),
        'files': FileController(app.config['EXPORT_DIR'], ROOT / 'docs'),
        'settings': SettingsController(app.config, ROOT),
    }
    register_request_context(app)
    register_error_handlers(app)
    app.register_blueprint(api)
    app.register_blueprint(pages)
    return app


def serve(host='127.0.0.1', port=8080):
    create_app().run(host=host, port=port, debug=False)
