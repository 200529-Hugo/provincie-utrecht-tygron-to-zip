from flask import Flask, render_template
from scenario_dossier.controllers.demo_controller import DemoController

app = Flask(__name__)
demo_controller = DemoController()

@app.route("/")
def index():
    projects = demo_controller.get_projects()
    selected_project_id = projects[0].id
    scenarios = demo_controller.get_scenarios(selected_project_id)
    return render_template("index-new.html",
                           selected_project_id = selected_project_id,
                           projects = projects,
                           scenarios = scenarios)

@app.route("/controle")
def controle():
    return render_template("controle-new.html")

@app.route("/werkinstructie")
def werkinstructie():
    return render_template("werkinstructie-new.html")