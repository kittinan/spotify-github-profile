from flask import Flask, Response, jsonify, render_template, redirect, request
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

import os

import spotify

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

    print("XXX")
    code = request.args.get("code")

    if code is None:
        return Response("not ok")

    print("code: {}".format(code))

    token = spotify.generate_token(code)
    print(token)

    return Response("ok")


if __name__ == "__main__":
    app.run(debug=True)
