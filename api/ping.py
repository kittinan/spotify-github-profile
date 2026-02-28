from flask import Flask, Response, jsonify

app = Flask(__name__)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):
    """
    Simple ping endpoint for health checks.
    Only responds to root path, returns 404 for any other path.
    Returns a JSON response with status and message.
    """
    # Only respond to the root path for a more focused health check
    if path:
        return jsonify({
            "status": "error",
            "message": "Not found"
        }), 404
    
    return jsonify({
        "status": "ok",
        "message": "pong"
    }), 200


if __name__ == "__main__":
    app.run(debug=True, port=5004)
