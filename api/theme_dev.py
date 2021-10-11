from flask import Flask, Response, jsonify, render_template, redirect, request
from base64 import b64decode, b64encode

from view import generate_css_bar, load_image_b64

app = Flask(__name__)


def make_svg(artist_name, song_name, img, is_now_playing, cover_image, theme, bar_color):
    height = 445 if cover_image else 145
    num_bar = 75

    if is_now_playing:
        title_text = "Now playing"
        content_bar = "".join(["<div class='bar'></div>" for i in range(num_bar)])
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
    }

    return render_template(f"spotify.{theme}.html.j2", **rendered_data)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):

    artist_name = "Spotify Github Profile"
    song_name = "Revolution with very long text - ft. someone"

    img_url = "https://avatars1.githubusercontent.com/u/144775?s=300&v=4"
    img = load_image_b64(img_url)
    is_now_playing = True
    cover_image = True
    theme = 'default'
    bar_color = '53b14f'

    svg = make_svg(artist_name, song_name, img, is_now_playing, cover_image, theme, bar_color)

    resp = Response(svg, mimetype="image/svg+xml")
    resp.headers["Cache-Control"] = "s-maxage=1"

    return resp


if __name__ == "__main__":
    # python api/theme_dev.py
    app.run(debug=True, port=5004)
