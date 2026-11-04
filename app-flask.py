"""Oud startcommando dat dezelfde Flask-applicatie blijft starten."""
from scenario_dossier.web import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=False)
