from base64 import b64encode

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

import requests
import json
import os
import random

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_SECRET_ID = os.getenv("SPOTIFY_SECRET_ID")
BASE_URL = os.getenv("BASE_URL")

REDIRECT_URI = "{}/callback".format(BASE_URL)

# scope user-read-currently-playing,user-read-recently-played
SPOTIFY_URL_REFRESH_TOKEN = "https://accounts.spotify.com/api/token"
SPOTIFY_URL_NOW_PLAYING = (
    "https://api.spotify.com/v1/me/player/currently-playing?additional_types=track,episode"
)
SPOTIFY_URL_RECENTLY_PLAY = "https://api.spotify.com/v1/me/player/recently-played?limit=10"

SPOTIFY_URL_GENERATE_TOKEN = "https://accounts.spotify.com/api/token"
SPOTIFY_URL_USER_INFO = "https://api.spotify.com/v1/me"


def get_authorization():

    return b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_SECRET_ID}".encode()).decode("ascii")


def generate_token(authorization_code):

    data = {
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code": authorization_code,
    }

    headers = {"Authorization": "Basic {}".format(get_authorization())}

    response = requests.post(SPOTIFY_URL_GENERATE_TOKEN, data=data, headers=headers)
    repsonse_json = response.json()

    return repsonse_json


def refresh_token(refresh_token):

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }

    headers = {"Authorization": "Basic {}".format(get_authorization())}

    response = requests.post(SPOTIFY_URL_REFRESH_TOKEN, data=data, headers=headers)
    repsonse_json = response.json()

    return repsonse_json


def get_user_profile(access_token):

    headers = {"Authorization": "Bearer {}".format(access_token)}

    response = requests.get(SPOTIFY_URL_USER_INFO, headers=headers)
    repsonse_json = response.json()

    return repsonse_json


def get_recently_play(access_token):

    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(SPOTIFY_URL_RECENTLY_PLAY, headers=headers)

    if response.status_code == 204:
        return {}

    repsonse_json = response.json()
    return repsonse_json


def get_now_playing(access_token):

    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(SPOTIFY_URL_NOW_PLAYING, headers=headers)

    if response.status_code == 204:
        return {}

    repsonse_json = response.json()
    return repsonse_json

