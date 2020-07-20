from flask import Flask, Response, jsonify, render_template, redirect, request
from base64 import b64decode, b64encode
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

from firebase_admin import credentials
from firebase_admin import firestore
import firebase_admin

from time import time

import os
import json
from util import spotify
import random
import requests


print("Starting Server")

firebase_config = os.getenv("FIREBASE")
firebase_dict = json.loads(b64decode(firebase_config))

cred = credentials.Certificate(firebase_dict)
firebase_admin.initialize_app(cred)

db = firestore.client()

app = Flask(__name__)


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


def load_image_b64(url):

    resposne = requests.get(url)
    return b64encode(resposne.content).decode("ascii")


def make_svg(item, is_now_playing):

    height = 445
    num_bar = 75

    if is_now_playing:
        title_text = "Now playing"
        content_bar = "".join(["<div class='bar'></div>" for i in range(num_bar)])
    else:
        title_text = "Recently play"
        content_bar = ""

    css_bar = generate_css_bar(num_bar)

    img = load_image_b64(item["album"]["images"][1]["url"])
    artist_name = item["artists"][0]["name"]
    song_name = item["name"]
    url = item["external_urls"]["spotify"]

    rendered_data = {
        "height": height,
        "num_bar": num_bar,
        "content_bar": content_bar,
        "css_bar": css_bar,
        "title_text": title_text,
        "artist_name": artist_name,
        "song_name": song_name,
        "content_bar": content_bar,
        "img": img,
    }

    return render_template("spotify.html.j2", **rendered_data)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):

    print("XXX")
    uid = request.args.get("uid")
    print(uid)

    doc_ref = db.collection("users").document(uid)
    doc = doc_ref.get()

    if not doc.exists:
        print("not exist")
        return Response("not ok")

    token_info = doc.to_dict()

    current_ts = int(time())
    access_token = token_info["access_token"]

    # check token expired
    expired_ts = token_info.get("expired_ts")
    print(current_ts)
    print(expired_ts)
    if expired_ts is None or current_ts >= expired_ts:
        # Refresh token

        refresh_token = token_info["refresh_token"]

        print(f"refresh_token : {refresh_token}")

        new_token = spotify.refresh_token(refresh_token)
        expired_ts = int(time()) + new_token["expires_in"]
        update_data = {"access_token": new_token["access_token"], "expired_ts": expired_ts}
        doc_ref.update(update_data)

        access_token = new_token["access_token"]

        print("new token")

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

    svg = make_svg(item, is_now_playing)

    resp = Response(svg, mimetype="image/svg+xml")
    resp.headers["Cache-Control"] = "s-maxage=1"

    return resp


if __name__ == "__main__":
    app.run(debug=True, port=5003)
