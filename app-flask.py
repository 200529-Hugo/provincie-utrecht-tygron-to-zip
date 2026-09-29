from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index-new.html")

@app.route("/controle")
def controle():
    return render_template("controle-new.html")

@app.route("/werkinstructie")
def werkinstructie():
    return render_template("werkinstructie-new.html")