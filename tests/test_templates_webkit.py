"""Guards against CSS that breaks the cards in WebKit (Safari, and every iOS browser).

The cards are HTML inside an SVG <foreignObject>. When GitHub shrinks the image
to fit a narrow README, WebKit does not scale any element that gets its own
compositing layer: it paints it at full size and in the wrong place. Positioned
elements, opacity and transforms all create such a layer, so the templates must
lay out and animate without them.
"""
import os
import re
import sys

import pytest

# Add the parent directory to the path to import the api module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

ALL_THEMES = ["default", "compact", "natemoo-re", "novatorem", "karaoke", "apple", "spotify-embed"]
BAR_THEMES = {"default": 75, "natemoo-re": 100, "novatorem": 100}

# compact and karaoke still carry an unused "@keyframes sound" that animates
# opacity. Nothing in those templates references it, so it cannot create a layer.
UNUSED_OPACITY_KEYFRAMES = {"compact", "karaoke"}

LAYER_CREATING_CSS = {
    "position": re.compile(r"(?<![-\w])position\s*:\s*(absolute|relative|fixed|sticky)"),
    "transform": re.compile(r"(?<![-\w])transform\s*:"),
    "opacity": re.compile(r"(?<![-\w])opacity\s*:"),
    "filter": re.compile(r"(?<![-\w])filter\s*:"),
}


def render(theme, is_now_playing=True, cover_image=True, show_offline=False,
           song_name="Test Song"):
    from api.view import app, make_svg

    with app.app_context():
        return make_svg(
            artist_name="Test Artist",
            song_name=song_name,
            img="",
            is_now_playing=is_now_playing,
            cover_image=cover_image,
            theme=theme,
            bar_color="53b14f",
            show_offline=show_offline,
            background_color="121212",
            mode="dark",
            progress_ms=65000,
            duration_ms=192000,
        )


def stylesheet(svg):
    css = "".join(re.findall(r"<style>(.*?)</style>", svg, flags=re.S))
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


@pytest.mark.parametrize("is_now_playing", [True, False])
@pytest.mark.parametrize("theme", ALL_THEMES)
def test_templates_avoid_css_that_webkit_does_not_scale(theme, is_now_playing):
    css = stylesheet(render(theme, is_now_playing=is_now_playing))

    assert css, "expected the card to carry its own stylesheet"
    for name, pattern in LAYER_CREATING_CSS.items():
        if name == "opacity" and theme in UNUSED_OPACITY_KEYFRAMES:
            continue
        match = pattern.search(css)
        assert match is None, (
            f"{theme} theme uses '{match.group(0)}', which WebKit will not "
            "scale inside <foreignObject>"
        )


@pytest.mark.parametrize("theme,num_bar", BAR_THEMES.items())
def test_equaliser_bars_are_laid_out_in_flow(theme, num_bar):
    svg = render(theme)
    css = stylesheet(svg)

    assert svg.count("class='bar'") == num_bar
    bars_rule = re.search(r"#bars\s*\{(.*?)\}", css, flags=re.S).group(1)
    assert "display: flex" in bars_rule
    assert "align-items: flex-end" in bars_rule
    # The bars still pulse: height and colour animate, opacity does not.
    keyframes = re.search(r"@keyframes sound\s*\{(.*)\}\s*\}", css, flags=re.S).group(1)
    assert "height" in keyframes
    assert "background" in keyframes


@pytest.mark.parametrize("theme", BAR_THEMES)
def test_equaliser_bars_hidden_when_offline(theme):
    svg = render(theme, is_now_playing=False, show_offline=True, song_name="")

    assert "class='bar'" not in svg
    assert "Nothing playing on Spotify" in svg


def test_novatorem_song_title_scrolls_without_transform():
    svg = render("novatorem", song_name="A Long Song Title")
    css = stylesheet(svg)

    track = re.search(r'<div class="song-track">(.*?)</div>\s*</div>', svg, flags=re.S).group(1)
    assert track.count("A Long Song Title") == 3
    keyframes = re.search(r"@keyframes marquee\s*\{(.*?\})\s*\}", css, flags=re.S).group(1)
    assert "margin-left" in keyframes
    assert "transform" not in keyframes


def test_spotify_embed_declares_view_box():
    svg = render("spotify-embed")

    assert '<svg width="460" height="152" viewBox="0 0 460 152"' in svg
