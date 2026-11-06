from ..i18n import CATALOGS
from ..models.api.requests.settings import TranslationsRequest
from ..models.api.responses.settings import MapConfigResponse, ManualResponse, TranslationsResponse
from ..services.file_service import FileService


class SettingsController:
    def __init__(self, config, root):
        self.config = config
        self.files = FileService(config['EXPORT_DIR'], root / 'docs')

    def map_config(self) -> MapConfigResponse:
        return MapConfigResponse(self.config['MAP_STYLE_URL'])

    def manual(self, language='nl') -> ManualResponse:
        return ManualResponse(self.files.manual(language))

    def translations(self, payload: TranslationsRequest) -> TranslationsResponse:
        return TranslationsResponse(CATALOGS['nl'] | CATALOGS[payload.language])
