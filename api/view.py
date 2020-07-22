from flask import Flask, Response, jsonify, render_template, redirect, request
from base64 import b64decode, b64encode
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

from firebase_admin import credentials
from firebase_admin import firestore
from sys import getsizeof
import firebase_admin

from time import time

import os
import json
from util import spotify
import random
import requests
import functools

print("Starting Server")

firebase_config = os.getenv("FIREBASE")
firebase_dict = json.loads(b64decode(firebase_config))

cred = credentials.Certificate(firebase_dict)
firebase_admin.initialize_app(cred)

db = firestore.client()
CACHE_TOKEN_INFO = {}

app = Flask(__name__)


@functools.lru_cache(maxsize=128)
def generate_css_bar(num_bar=75):
    css_bar = ""
    left = 1
    for i in range(1, num_bar + 1):

        anim = random.randint(350, 500)
        css_bar += ".bar:nth-child({})  {{ left: {}px; animation-duration: {}ms; }}".format(
            i, left, anim
        )
        left += 4

    return css_bar


@functools.lru_cache(maxsize=128)
def load_image_b64(url):

    resposne = requests.get(url)
    return b64encode(resposne.content).decode("ascii")


@functools.lru_cache(maxsize=128)
def make_svg(artist_name, song_name, img, is_now_playing, cover_image):

    print("make_svg")

    height = 445 if cover_image else 145
    num_bar = 75

    if is_now_playing:
        title_text = "Now playing"
        content_bar = "".join(["<div class='bar'></div>" for i in range(num_bar)])
    else:
        title_text = "Recently play"
        content_bar = ""

    css_bar = generate_css_bar(num_bar)

    rendered_data = {
        "height": height,
        "num_bar": num_bar,
        "content_bar": content_bar,
        "css_bar": css_bar,
        "title_text": title_text,
        "artist_name": artist_name,
        "song_name": song_name,
        "img": img,
        "cover_image": cover_image,
    }

    return render_template("spotify.html.j2", **rendered_data)


def get_cache_token_info(uid):
    global CACHE_TOKEN_INFO

    token_info = CACHE_TOKEN_INFO.get(uid, None)
    return token_info


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):

    global CACHE_TOKEN_INFO

    uid = request.args.get("uid")
    cover_image = request.args.get("cover_image", default='true') == 'true'

    # Load token from cache memory
    token_info = get_cache_token_info(uid)

    if token_info is None:
        # Load from firebase
        print("load token_info from firebase")

        doc_ref = db.collection("users").document(uid)
        doc = doc_ref.get()

        if not doc.exists:
            print("not exist")
            # TODO: show error
            return Response("not ok")

        token_info = doc.to_dict()

        CACHE_TOKEN_INFO[uid] = token_info

    current_ts = int(time())
    access_token = token_info["access_token"]

    # Check token expired
    expired_ts = token_info.get("expired_ts")
    print(current_ts, expired_ts)
    if expired_ts is None or current_ts >= expired_ts:
        # Refresh token

        print("Refresh token")

        refresh_token = token_info["refresh_token"]

        # print(f"refresh_token : {refresh_token}")

        new_token = spotify.refresh_token(refresh_token)
        expired_ts = int(time()) + new_token["expires_in"]
        update_data = {"access_token": new_token["access_token"], "expired_ts": expired_ts}
        doc_ref = db.collection("users").document(uid)
        doc_ref.update(update_data)

        access_token = new_token["access_token"]

        # Save in memory cache
        CACHE_TOKEN_INFO[uid] = update_data

    data = spotify.get_now_playing(access_token)
    if data:

        item = data["item"]
        is_now_playing = True
    else:

        content_bar = ""

        recent_plays = spotify.get_recently_play(access_token)
        size_recent_play = len(recent_plays["items"])
        idx = random.randint(0, size_recent_play - 1)
        item = recent_plays["items"][idx]["track"]
        is_now_playing = False

    img = ""
    if cover_image:
        img = load_image_b64(item["album"]["images"][1]["url"])
    artist_name = item["artists"][0]["name"].replace("&", "&amp;")
    song_name = item["name"].replace("&", "&amp;")

    svg = make_svg(artist_name, song_name, img, is_now_playing, cover_image)

    resp = Response(svg, mimetype="image/svg+xml")
    resp.headers["Cache-Control"] = "s-maxage=1"

    print(getsizeof(CACHE_TOKEN_INFO))

    return resp


if __name__ == "__main__":
    app.run(debug=True, port=5003)
