from flask import Flask, Response, jsonify, render_template, redirect
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

import os

"""
Inspired from https://github.com/natemoo-re
"""

print("Starting Server")


SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_SECRET_ID = os.getenv("SPOTIFY_SECRET_ID")
REDIRECT_URI = os.getenv("REDIRECT_URI")

app = Flask(__name__)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):

    login_url = f"https://accounts.spotify.com/authorize?client_id={SPOTIFY_CLIENT_ID}&response_type=code&scope=user-read-currently-playing,user-read-recently-played&redirect_uri={REDIRECT_URI}"

    return redirect(login_url)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
