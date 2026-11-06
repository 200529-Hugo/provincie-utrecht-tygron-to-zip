"""Koppel toegangscontrole aan de bestaande cache zonder API-logica te kopiëren."""

from .demo_service import DemoService
from .project_service import ProjectService
from .thumbnail_service import Thumbnail, ThumbnailService
from .tygron_service import TygronService


class ProjectPreviewService:
    def __init__(self, cache: ThumbnailService):
        self.cache = cache
        self.projects = ProjectService()
        self.tygron = TygronService()
        self.demo = DemoService()

    def project(self, account, file_name):
        project = self.projects.accessible_project(account, file_name)
        credentials = account.credentials
        key = ('tygron', credentials.base_url.rstrip('/'), credentials.username,
               project.get('domain') or credentials.domain, project['file_name'],
               tuple(project['versions']), project.get('revision', ''))
        return self.cache.get(key, lambda: Thumbnail(
            self.tygron.project_thumbnail(credentials, project['file_name']), 'image/png'))

    def demo_project(self, project_id):
        project = self.demo.get_project(project_id)
        key = ('demo', project.id, self.demo.data_path.stat().st_mtime_ns)
        return self.cache.get(key, lambda: ThumbnailService.demo(project))
