from flask import Flask, Response

from view import load_image_b64, make_svg

app = Flask(__name__)

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
    is_offline = False
    rendered_data = 'ffffff00'

    svg = make_svg(artist_name, song_name, img, is_now_playing, cover_image, theme, bar_color, is_offline, background_color)

    resp = Response(svg, mimetype="image/svg+xml")
    resp.headers["Cache-Control"] = "s-maxage=1"

    return resp


if __name__ == "__main__":
    # python api/theme_dev.py
    app.run(debug=True, port=5004)
