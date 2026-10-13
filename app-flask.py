from flask import Flask, render_template, jsonify
from werkzeug.exceptions import HTTPException, NotFound

from scenario_dossier.controllers.demo_controller import DemoController
from scenario_dossier.http_routes import api

app = Flask(__name__)
app.register_blueprint(api)

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

@app.errorhandler(HTTPException)
def handle_http_error(e: HTTPException):
    return jsonify({
        "error": e.name,
        "message": e.description
    }), e.code

if __name__ == "__main__":
    app.run(debug=True)