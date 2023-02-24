from flask import Flask, Response, jsonify, render_template, redirect, request
from base64 import b64decode, b64encode
from dotenv import load_dotenv, find_dotenv

from util.firestore import get_firestore_db

load_dotenv(find_dotenv())

from sys import getsizeof
from PIL import Image

from time import time

import io
from util import spotify
import random
import requests
import functools
import colorgram
import math

print("Starting Server")

db = get_firestore_db()
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
def load_image(url):
    resposne = requests.get(url)
    return resposne.content


def to_img_b64(content):
    return b64encode(content).decode("ascii")


def load_image_b64(url):
    return to_img_b64(load_image(url))


def isLightOrDark(rgbColor=[0, 128, 255], threshold=127.5):
    # https://stackoverflow.com/a/58270890
    [r, g, b] = rgbColor
    hsp = math.sqrt(0.299 * (r * r) + 0.587 * (g * g) + 0.114 * (b * b))
    if hsp > threshold:
        return "light"
    else:
        return "dark"


# @functools.lru_cache(maxsize=128)
def make_svg(
    artist_name,
    song_name,
    img,
    is_now_playing,
    cover_image,
    theme,
    bar_color,
    show_offline,
    background_color,
):
    height = 0
    num_bar = 75

    if theme == "compact":
        if cover_image:
            height = 400
        else:
            height = 100
    elif theme == "natemoo-re":
        height = 84
        num_bar = 100
    elif theme == "novatorem":
        height = 100
        num_bar = 100
    else:
        if cover_image:
            height = 445
        else:
            height = 145

    if is_now_playing:
        title_text = "Now playing"
        content_bar = "".join(["<div class='bar'></div>" for i in range(num_bar)])
        css_bar = generate_css_bar(num_bar)
    elif show_offline:
        title_text = "Not playing"
        content_bar = ""
        css_bar = None
    else:
        title_text = "Recently played"
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
        "bar_color": bar_color,
        "background_color": background_color,
    }

    return render_template(f"spotify.{theme}.html.j2", **rendered_data)


def get_cache_token_info(uid):
    global CACHE_TOKEN_INFO

    token_info = CACHE_TOKEN_INFO.get(uid, None)

    if type(token_info) == dict:
        current_ts = int(time())
        expired_ts = token_info.get("expired_ts")
        if expired_ts is None or current_ts >= expired_ts:
            return None

    return token_info


def get_access_token(uid):
    global CACHE_TOKEN_INFO

    # Load token from cache memory
    token_info = get_cache_token_info(uid)

    if token_info is None:
        # Load from firebase
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
    if expired_ts is None or current_ts >= expired_ts:
        # Refresh token
        refresh_token = token_info["refresh_token"]

        new_token = spotify.refresh_token(refresh_token)
        expired_ts = int(time()) + new_token["expires_in"]
        update_data = {"access_token": new_token["access_token"], "expired_ts": expired_ts}
        doc_ref = db.collection("users").document(uid)
        doc_ref.update(update_data)

        access_token = new_token["access_token"]

        # Save in memory cache
        CACHE_TOKEN_INFO[uid] = update_data

    return access_token


def get_song_info(uid, show_offline):
    access_token = get_access_token(uid)

    data = spotify.get_now_playing(access_token)

    if data:
        item = data["item"]
        item["currently_playing_type"] = data["currently_playing_type"]
        is_now_playing = True
    elif show_offline:
        return None, False
    else:
        recent_plays = spotify.get_recently_play(access_token)
        size_recent_play = len(recent_plays["items"])
        idx = random.randint(0, size_recent_play - 1)
        item = recent_plays["items"][idx]["track"]
        item["currently_playing_type"] = "track"
        is_now_playing = False

    return item, is_now_playing


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):
    uid = request.args.get("uid")
    cover_image = request.args.get("cover_image", default="true") == "true"
    is_redirect = request.args.get("redirect", default="false") == "true"
    theme = request.args.get("theme", default="default")
    bar_color = request.args.get("bar_color", default="53b14f")
    background_color = request.args.get("background_color", default="121212")
    is_bar_color_from_cover = request.args.get("bar_color_cover", default="false") == "true"
    show_offline = request.args.get("show_offline", default="false") == "true"
    interchange = request.args.get("interchange", default="false") == "true"

    item, is_now_playing = get_song_info(uid, show_offline)

    if show_offline and not is_now_playing:
        if interchange:
          artist_name = "Currently not playing on Spotify"
          song_name = "Offline"
        else:
          artist_name = "Offline"
          song_name = "Currently not playing on Spotify"
        img_b64 = ""
        cover_image = False
        svg = make_svg(
            artist_name,
            song_name,
            img_b64,
            is_now_playing,
            cover_image,
            theme,
            bar_color,
            show_offline,
            background_color,
        )
        resp = Response(svg, mimetype="image/svg+xml")
        resp.headers["Cache-Control"] = "s-maxage=1"
        return resp

    currently_playing_type = item.get("currently_playing_type", "track")

    if is_redirect:
        return redirect(item["uri"], code=302)

    img = None
    img_b64 = ""
    if cover_image:

        if currently_playing_type == "track":
            img = load_image(item["album"]["images"][1]["url"])
        elif currently_playing_type == "episode":
            img = load_image(item["images"][1]["url"])

        img_b64 = to_img_b64(img)

    # Extract cover image color
    if is_bar_color_from_cover and img:

        is_skip_dark = False
        if theme in ["default"]:
            is_skip_dark = True

        pil_img = Image.open(io.BytesIO(img))
        colors = colorgram.extract(pil_img, 5)

        for color in colors:

            rgb = color.rgb

            light_or_dark = isLightOrDark([rgb.r, rgb.g, rgb.b], threshold=80)

            if light_or_dark == "dark" and is_skip_dark:
                # Skip to use bar in dark color
                continue

            bar_color = "%02x%02x%02x" % rgb
            break

    # Find artist_name and song_name
    if currently_playing_type == "track":
        artist_name = item["artists"][0]["name"].replace("&", "&amp;")
        song_name = item["name"].replace("&", "&amp;")

    elif currently_playing_type == "episode":
        artist_name = item["show"]["publisher"].replace("&", "&amp;")
        song_name = item["name"].replace("&", "&amp;")

    if interchange:
      x = artist_name
      artist_name = song_name
      song_name = x
      
    svg = make_svg(
        artist_name,
        song_name,
        img_b64,
        is_now_playing,
        cover_image,
        theme,
        bar_color,
        show_offline,
        background_color,
    )

    resp = Response(svg, mimetype="image/svg+xml")
    resp.headers["Cache-Control"] = "s-maxage=1"

    print("cache size:", getsizeof(CACHE_TOKEN_INFO))

    return resp


if __name__ == "__main__":

    app.run(debug=True, port=5003)
