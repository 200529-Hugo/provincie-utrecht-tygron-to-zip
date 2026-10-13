from werkzeug.exceptions import NotFound

from ..services.demo_service import DemoService

class DemoController:
    def __init__(self):
        self.demo_service = DemoService()

    def get_projects(self):
        return self.demo_service.list_projects()

    def get_project(self, project_id):
        try:
            return self.demo_service.get_project(project_id)
        except LookupError as le:
            raise NotFound(description=str(le)) from le

    def get_scenarios(self, project_id):
        try:
            return self.demo_service.get_scenarios(project_id)
        except LookupError as le:
            raise NotFound(description=str(le)) from le

    def inspect(self, payload):
        return self.demo_service.inspect(payload)
