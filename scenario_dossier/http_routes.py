from flask import Blueprint, jsonify, request
from scenario_dossier.controllers.demo_controller import DemoController

api = Blueprint('api', __name__, url_prefix='/api')
demo_controller = DemoController()

@api.get("/demo/projects")
def get_projects():
    projects = demo_controller.get_projects()
    return jsonify(projects)

@api.get("/demo/scenarios/<project_id>")
def get_scenarios_by_project(project_id):
    scenarios = demo_controller.get_scenarios(project_id)
    return jsonify(scenarios)

@api.post("/inspect")
def inspect():
    data = request.get_json()
    inspected = demo_controller.inspect(data)
    return jsonify(inspected)