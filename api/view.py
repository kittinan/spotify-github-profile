import math

import colorgram
from flask import Flask, Response, render_template, redirect, request
from dotenv import load_dotenv, find_dotenv

from api.view_params import ViewParams
from api.view_utils import load_cover_image_if_needed, extract_bar_color_from_image, resolve_artist_and_song_names, \
    to_img_b64, load_image
from util.firestore import get_firestore_db
from util.profanity import profanity_check

load_dotenv(find_dotenv())

from sys import getsizeof
from PIL import ImageFile

from time import time

from util import spotify
import random
import functools
import html

ImageFile.LOAD_TRUNCATED_IMAGES = True

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
        css_bar += (
            ".bar:nth-child({})  {{ left: {}px; animation-duration: {}ms; }}".format(
                i, left, anim
            )
        )
        left += 4

    return css_bar




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


def encode_html_entities(text):
    return html.escape(text)


def format_time_ms(milliseconds):
    """Convert milliseconds to MM:SS format"""
    if milliseconds is None or milliseconds < 0:
        return "0:00"

    seconds = milliseconds // 1000
    minutes = seconds // 60
    seconds = seconds % 60

    return f"{minutes}:{seconds:02d}"


def calculate_progress_data(progress_ms, duration_ms):
    """Calculate progress percentage and formatted times"""
    if not progress_ms or not duration_ms or duration_ms <= 0:
        return {
            "progress_percentage": 0,
            "current_time": "0:00",
            "remaining_time": "0:00",
        }

    # Ensure progress doesn't exceed duration
    progress_ms = min(progress_ms, duration_ms)

    # Calculate percentage
    progress_percentage = (progress_ms / duration_ms) * 100

    # Format times
    current_time = format_time_ms(progress_ms)
    remaining_ms = duration_ms - progress_ms
    remaining_time = f"-{format_time_ms(remaining_ms)}"

    return {
        "progress_percentage": progress_percentage,
        "current_time": current_time,
        "remaining_time": remaining_time,
    }


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
        mode,
        progress_ms=None,
        duration_ms=None,
):
    height = 0
    num_bar = 75

    # Sanitize input
    artist_name = encode_html_entities(artist_name)
    song_name = encode_html_entities(song_name)

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
    elif theme == "apple":
        height = 534
        num_bar = 0
    elif theme == "spotify-embed":
        height = 152
        num_bar = 0
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

    # Calculate progress data for Apple and Spotify Embed themes
    progress_data = {}
    if theme in ["apple", "spotify-embed"] and duration_ms is not None:
        if is_now_playing and progress_ms is not None:
            # Currently playing - show real progress
            progress_data = calculate_progress_data(progress_ms, duration_ms)
        else:
            # Recently played - show 0 progress but real duration
            progress_data = calculate_progress_data(0, duration_ms)

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
        "mode": mode,
        "is_now_playing": is_now_playing,
        "progress_data": progress_data,
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


def delete_cache_token_info(uid):
    global CACHE_TOKEN_INFO

    if uid in CACHE_TOKEN_INFO:
        del CACHE_TOKEN_INFO[uid]


def get_access_token(uid):
    global CACHE_TOKEN_INFO

    # Load token from cache memory
    token_info = get_cache_token_info(uid)

    if token_info is None:
        # Load from firebase
        doc_ref = db.collection("users").document(uid)
        doc = doc_ref.get()

        if not doc.exists:
            print("not exist data in firebase: {}".format(uid))
            return None

        token_info = doc.to_dict()

        CACHE_TOKEN_INFO[uid] = token_info

    current_ts = int(time())
    access_token = token_info.get("access_token", None)
    print(access_token)

    # Check token expired
    expired_ts = token_info.get("expired_ts")
    if expired_ts is None or current_ts >= expired_ts:
        # Refresh token
        refresh_token = token_info["refresh_token"]

        new_token = spotify.refresh_token(refresh_token)

        # Handle refresh token revoke
        if new_token.get("error") == "invalid_grant":
            # Delete token in firebase
            doc_ref = db.collection("users").document(uid)
            doc_ref.delete()

            # Delete token in memory cache
            delete_cache_token_info(uid)
            return None

        expired_ts = int(time()) + new_token["expires_in"]
        update_data = {
            "access_token": new_token["access_token"],
            "expired_ts": expired_ts,
        }
        doc_ref = db.collection("users").document(uid)
        doc_ref.update(update_data)

        access_token = new_token["access_token"]

        # Save in memory cache
        CACHE_TOKEN_INFO[uid] = update_data

    return access_token


def get_song_info(uid, show_offline):
    access_token = get_access_token(uid)

    item = None
    is_now_playing = False
    progress_ms = None
    duration_ms = None

    # Handle refrest_token revoke or invalid token
    if access_token is None:
        raise spotify.InvalidTokenError("Invalid Spotify access_token or refresh_token")

    data = spotify.get_now_playing(access_token)

    if data:
        item = data["item"]
        item["currently_playing_type"] = data["currently_playing_type"]
        is_now_playing = True

        # Extract progress data for currently playing tracks
        progress_ms = data.get("progress_ms")
        if item and item.get("duration_ms"):
            duration_ms = item["duration_ms"]
    elif show_offline:
        return None, False, None, None
    else:
        recent_plays = spotify.get_recently_play(access_token)
        size_recent_play = len(recent_plays["items"])

        # Handle empty recently play, should offline
        if size_recent_play == 0:
            return None, False, None, None

        idx = random.randint(0, size_recent_play - 1)
        item = recent_plays["items"][idx]["track"]
        item["currently_playing_type"] = "track"
        is_now_playing = False
        # No progress data for recently played tracks, but get duration
        if item and item.get("duration_ms"):
            duration_ms = item["duration_ms"]

    return item, is_now_playing, progress_ms, duration_ms


def parse_view_params():
    uid = request.args.get("uid")
    return ViewParams(
        uid=uid,
        cover_image=request.args.get("cover_image", default="true") == "true",
        is_redirect=request.args.get("redirect", default="false") == "true",
        theme=request.args.get("theme", default="default"),
        bar_color=request.args.get("bar_color", default="53b14f"),
        background_color=request.args.get("background_color", default="121212"),
        is_bar_color_from_cover=(
                request.args.get("bar_color_cover", default="false") == "true"
        ),
        show_offline=request.args.get("show_offline", default="false") == "true",
        interchange=request.args.get("interchange", default="false") == "true",
        mode=request.args.get("mode", default="light"),
        is_enable_profanity=request.args.get("profanity", default="false") == "true",
    )


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):
    params = parse_view_params()

    # Handle invalid request
    if not params.uid:
        return Response("not ok")

    try:
        item, is_now_playing, progress_ms, duration_ms = get_song_info(
            params.uid, params.show_offline
        )
    except spotify.InvalidTokenError:
        return Response(
            "Error: Invalid Spotify access_token or refresh_token. Possibly the token revoked. "
            "Please re-login at https://github.com/kittinan/spotify-github-profile"
        )

    if (params.show_offline and not is_now_playing) or (item is None):
        return build_offline_response(params, is_now_playing, progress_ms, duration_ms)

    currently_playing_type = item.get("currently_playing_type", "track")

    if params.is_redirect:
        return redirect(item["uri"], code=302)

    img, img_b64 = load_cover_image_if_needed(
        params.cover_image, currently_playing_type, item, load_image, to_img_b64,
    )

    bar_color = params.bar_color
    if params.is_bar_color_from_cover and img is not None:
        bar_color = extract_bar_color_from_image(img, params.theme, bar_color, isLightOrDark, colorgram)

    artist_name, song_name = resolve_artist_and_song_names(
        item, currently_playing_type
    )

    if params.is_enable_profanity:
        artist_name = profanity_check(artist_name)
        song_name = profanity_check(song_name)

    if params.interchange:
        artist_name, song_name = song_name, artist_name

    svg = make_svg(
        artist_name,
        song_name,
        img_b64,
        is_now_playing,
        params.cover_image,
        params.theme,
        bar_color,
        params.show_offline,
        params.background_color,
        params.mode,
        progress_ms,
        duration_ms,
    )

    resp = Response(svg, mimetype="image/svg+xml")
    resp.headers["Cache-Control"] = "s-maxage=1"

    print("cache size:", getsizeof(CACHE_TOKEN_INFO))

    return resp


def build_offline_response(params, is_now_playing, progress_ms, duration_ms):
    if params.interchange:
        artist_name = "Currently not playing on Spotify"
        song_name = "Offline"
    else:
        artist_name = "Offline"
        song_name = "Currently not playing on Spotify"

    svg = make_svg(
        artist_name,
        song_name,
        img_b64="",
        is_now_playing=is_now_playing,
        cover_image=False,
        theme=params.theme,
        bar_color=params.bar_color,
        show_offline=params.show_offline,
        background_color=params.background_color,
        mode=params.mode,
        progress_ms=progress_ms,
        duration_ms=duration_ms,
    )
    resp = Response(svg, mimetype="image/svg+xml")
    resp.headers["Cache-Control"] = "s-maxage=1"
    return resp



if __name__ == "__main__":
    app.run(debug=True, port=5003)
