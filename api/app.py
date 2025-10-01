from flask import Flask
import importlib

# Import legacy handlers (order matters for Firebase init)
login_module = importlib.import_module("login")
callback_module = importlib.import_module("callback")
view_module = importlib.import_module("view")

login_handler = login_module.catch_all
callback_handler = callback_module.catch_all
view_handler = view_module.catch_all
view_svg_handler = view_handler  # view.svg.py is identical to view.py

app = Flask(__name__)


@app.route("/api/login", defaults={"path": ""})
@app.route("/api/login/<path:path>")
def login(path):
    return login_handler(path)


@app.route("/api/callback", defaults={"path": ""})
@app.route("/api/callback/<path:path>")
def callback(path):
    return callback_handler(path)


@app.route("/api/view", defaults={"path": ""})
@app.route("/api/view/<path:path>")
def view(path):
    return view_handler(path)


@app.route("/api/view.svg", defaults={"path": ""})
@app.route("/api/view.svg/<path:path>")
def view_svg(path):
    return view_svg_handler(path)


if __name__ == "__main__":
    app.run(debug=True, port=3000)
