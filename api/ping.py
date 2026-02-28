from flask import Flask, Response, jsonify

app = Flask(__name__)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):
    """
    Simple ping endpoint for health checks.
    Returns a JSON response with status and message.
    """
    return jsonify({
        "status": "ok",
        "message": "pong"
    }), 200


if __name__ == "__main__":
    app.run(debug=True, port=5004)
