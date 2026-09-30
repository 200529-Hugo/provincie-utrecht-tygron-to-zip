from ..services.demo_service import DemoService

class DemoController:
    def __init__(self):
        self.demo_service = DemoService()

    def get_projects(self):
        return self.demo_service.list_projects()

    def get_project(self, project_id):
        return self.demo_service.get_project(project_id)

    def get_scenarios(self, project_id):
        return self.demo_service.get_scenarios(project_id)