import secrets

from flask import Flask, redirect

from util import spotify

app = Flask(__name__)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):
    state = secrets.token_urlsafe(32)
    login_url = (
        "https://accounts.spotify.com/authorize"
        f"?client_id={spotify.SPOTIFY_CLIENT_ID}"
        "&response_type=code"
        "&scope=user-read-currently-playing,user-read-recently-played"
        f"&redirect_uri={spotify.REDIRECT_URI}"
        f"&state={state}"
    )

    response = redirect(login_url)
    response.set_cookie(
        spotify.OAUTH_STATE_COOKIE_NAME,
        state,
        max_age=spotify.OAUTH_STATE_MAX_AGE_SECONDS,
        httponly=True,
        secure=bool(spotify.REDIRECT_URI and spotify.REDIRECT_URI.startswith("https://")),
        samesite="Lax",
        path="/",
    )
    return response


if __name__ == "__main__":
    app.run(debug=True, port=5001)
