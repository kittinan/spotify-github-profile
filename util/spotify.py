from base64 import b64encode
from time import time

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

import os

import requests

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_SECRET_ID = os.getenv("SPOTIFY_SECRET_ID")
BASE_URL = os.getenv("BASE_URL")

REDIRECT_URI = "{}/callback".format(BASE_URL)

OAUTH_STATE_COOKIE_NAME = "spotify_oauth_state"
OAUTH_STATE_MAX_AGE_SECONDS = 600

# scope user-read-currently-playing,user-read-recently-played
SPOTIFY_URL_REFRESH_TOKEN = "https://accounts.spotify.com/api/token"
SPOTIFY_URL_NOW_PLAYING = "https://api.spotify.com/v1/me/player/currently-playing?additional_types=track,episode"
SPOTIFY_URL_RECENTLY_PLAY = (
    "https://api.spotify.com/v1/me/player/recently-played?limit=10"
)

SPOTIFY_URL_GENERATE_TOKEN = "https://accounts.spotify.com/api/token"
SPOTIFY_URL_USER_INFO = "https://api.spotify.com/v1/me"


class InvalidTokenError(Exception):
    pass


class TokenRefreshError(Exception):
    """Raised when a refresh fails without proving the refresh token is invalid."""

    pass


def normalize_token_info(token_info, existing_refresh_token=None, now=None):
    """Normalize Spotify token metadata before persisting or caching it.

    Spotify may omit ``refresh_token`` from a refresh response. In that case,
    the previous refresh token must be retained. ``expired_ts`` is stored as an
    absolute timestamp so callers do not need to refresh a freshly-issued token
    on its first use.
    """
    normalized = dict(token_info)

    if existing_refresh_token and not normalized.get("refresh_token"):
        normalized["refresh_token"] = existing_refresh_token

    expires_in = normalized.get("expires_in")
    if expires_in is not None:
        try:
            expires_in = max(0, int(expires_in))
        except (TypeError, ValueError) as exc:
            raise ValueError("Spotify token expires_in must be an integer") from exc

        normalized["expires_in"] = expires_in
        current_ts = int(time() if now is None else now)
        normalized["expired_ts"] = current_ts + expires_in

    return normalized


def get_authorization():

    return b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_SECRET_ID}".encode()).decode(
        "ascii"
    )


def generate_token(authorization_code):

    data = {
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code": authorization_code,
    }

    headers = {"Authorization": f"Basic {get_authorization()}"}

    response = requests.post(SPOTIFY_URL_GENERATE_TOKEN, data=data, headers=headers)
    response_json = response.json()

    return response_json


def refresh_token(refresh_token):

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }

    headers = {"Authorization": f"Basic {get_authorization()}"}

    response = requests.post(SPOTIFY_URL_REFRESH_TOKEN, data=data, headers=headers)
    response_json = response.json()

    return response_json


def get_user_profile_raw(access_token):
    """Return the raw Response object for flexible error handling by callers."""
    headers = {"Authorization": f"Bearer {access_token}"}
    return requests.get(SPOTIFY_URL_USER_INFO, headers=headers)


def get_user_profile(access_token):

    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(SPOTIFY_URL_USER_INFO, headers=headers)
    response_json = response.json()

    return response_json


def get_recently_play(access_token):

    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(SPOTIFY_URL_RECENTLY_PLAY, headers=headers)

    if response.status_code == 204:
        return {}

    response_json = response.json()
    return response_json


def get_now_playing(access_token):

    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(SPOTIFY_URL_NOW_PLAYING, headers=headers)

    if response.status_code == 204:
        return {}

    response_json = response.json()
    return response_json
