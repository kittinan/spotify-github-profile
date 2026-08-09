import hmac
import json
import os
from base64 import b64decode

import firebase_admin
from dotenv import find_dotenv, load_dotenv
from firebase_admin import credentials, firestore
from flask import Flask, Response, make_response, render_template, request

from util import spotify

load_dotenv(find_dotenv())

print("Starting Server")

firebase_config = os.getenv("FIREBASE")
firebase_dict = json.loads(b64decode(firebase_config))

cred = credentials.Certificate(firebase_dict)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

app = Flask(__name__)


def _clear_oauth_state_cookie(response):
    response.delete_cookie(spotify.OAUTH_STATE_COOKIE_NAME, path="/")
    return response


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):
    state = request.args.get("state")
    expected_state = request.cookies.get(spotify.OAUTH_STATE_COOKIE_NAME)
    if (
        not state
        or not expected_state
        or not hmac.compare_digest(state, expected_state)
    ):
        return Response("Invalid OAuth state", status=400, mimetype="text/plain")

    oauth_error = request.args.get("error")
    if oauth_error:
        response = Response(
            f"Spotify authorization failed: {oauth_error}",
            status=400,
            mimetype="text/plain",
        )
        return _clear_oauth_state_cookie(response)

    code = request.args.get("code")
    if not code:
        response = Response(
            "Missing authorization code", status=400, mimetype="text/plain"
        )
        return _clear_oauth_state_cookie(response)

    token_info = spotify.generate_token(code)

    if "access_token" not in token_info:
        error = token_info.get("error", "unknown")
        desc = token_info.get("error_description", "")
        response = Response(
            f"Token exchange failed: {error} - {desc}",
            status=400,
            mimetype="text/plain",
        )
        return _clear_oauth_state_cookie(response)

    try:
        token_info = spotify.normalize_token_info(token_info)
    except ValueError:
        response = Response(
            "Token exchange returned invalid token metadata",
            status=502,
            mimetype="text/plain",
        )
        return _clear_oauth_state_cookie(response)

    access_token = token_info["access_token"]

    profile_resp = spotify.get_user_profile_raw(access_token)
    if profile_resp.status_code != 200 or not profile_resp.text.strip():
        response = Response(
            f"Spotify profile fetch failed: HTTP {profile_resp.status_code} - {profile_resp.text[:300]}",
            status=502,
            mimetype="text/plain",
        )
        return _clear_oauth_state_cookie(response)

    spotify_user = profile_resp.json()
    user_id = spotify_user["id"]

    doc_ref = db.collection("users").document(user_id)
    doc_ref.set(token_info)

    rendered_data = {
        "uid": user_id,
        "BASE_URL": spotify.BASE_URL,
    }

    response = make_response(render_template("callback.html.j2", **rendered_data))
    return _clear_oauth_state_cookie(response)


if __name__ == "__main__":
    app.run(debug=True)
