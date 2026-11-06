"""Haal projecten op en controleer toegang op een centrale plek."""

from ..models import ProjectCredentials
from .tygron_service import TygronService


class ProjectService:
    def __init__(self):
        self.tygron = TygronService()

    def list_projects(self, credentials: ProjectCredentials):
        return self.tygron.list_projects(credentials)

    def list_for_account(self, account):
        projects = self.list_projects(account.credentials)
        account.projects = {project.file_name: project.to_dict() for project in projects}
        return projects

    @staticmethod
    def accessible_project(account, file_name):
        project = account.projects.get(file_name)
        if not project:
            raise ValueError('Selecteer een Tygron-project.')
        return project
