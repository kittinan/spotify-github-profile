from base64 import b64decode

from dotenv import find_dotenv, load_dotenv
from flask import Flask, Response, jsonify, redirect, render_template, request

load_dotenv(find_dotenv())

import json
import os

import firebase_admin
from firebase_admin import credentials, firestore

from util import spotify

print("Starting Server")

firebase_config = os.getenv("FIREBASE")
firebase_dict = json.loads(b64decode(firebase_config))

cred = credentials.Certificate(firebase_dict)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

app = Flask(__name__)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):
    code = request.args.get("code")

    if code is None:
        # TODO: no code
        return Response("not ok")

    token_info = spotify.generate_token(code)

    if "access_token" not in token_info:
        error = token_info.get("error", "unknown")
        desc = token_info.get("error_description", "")
        return Response(f"Token exchange failed: {error} - {desc}", status=400)

    access_token = token_info["access_token"]

    profile_resp = spotify.get_user_profile_raw(access_token)
    if profile_resp.status_code != 200 or not profile_resp.text.strip():
        return Response(
            f"Spotify profile fetch failed: HTTP {profile_resp.status_code} - {profile_resp.text[:300]}",
            status=502,
        )

    spotify_user = profile_resp.json()
    user_id = spotify_user["id"]

    doc_ref = db.collection("users").document(user_id)
    doc_ref.set(token_info)

    rendered_data = {
        "uid": user_id,
        "BASE_URL": spotify.BASE_URL,
    }

    return render_template("callback.html.j2", **rendered_data)


if __name__ == "__main__":
    app.run(debug=True)
