import functools
from base64 import b64encode

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

from PIL import Image, ImageFile

import io
import requests

ImageFile.LOAD_TRUNCATED_IMAGES = True

@functools.lru_cache(maxsize=128)
def load_image(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"Error loading image from {url}: {e}")
        # Return a placeholder or None to handle gracefully
        return None
    except Exception as e:
        print(f"Unexpected error loading image: {e}")
        return None

def to_img_b64(content):
    if content is None:
        return ""
    return b64encode(content).decode("ascii")

def load_cover_image_if_needed(cover_image, currently_playing_type, item, load_image_func, to_img_b64_func,):
    if not cover_image:
        return None, ""

    img = None
    if currently_playing_type == "track":
        img = load_image_func(item["album"]["images"][1]["url"])
    elif currently_playing_type == "episode":
        img = load_image_func(item["images"][1]["url"])

    if img is None:
        return None, ""

    return img, to_img_b64_func(img)

def extract_bar_color_from_image(img, theme, default_bar_color, isLightOrDark_func, colorgram_module,):
    is_skip_dark = theme in ["default"]

    try:
        pil_img = Image.open(io.BytesIO(img))
        colors = colorgram_module.extract(pil_img, 5)
    except Exception as e:
        print(f"Error extracting colors from image: {e}")
        return default_bar_color

    for color in colors:
        rgb = color.rgb
        light_or_dark = isLightOrDark_func([rgb.r, rgb.g, rgb.b], threshold=80)

        if light_or_dark == "dark" and is_skip_dark:
            # Skip to use bar in dark color
            continue

        return "%02x%02x%02x" % (rgb.r, rgb.g, rgb.b)

    return default_bar_color

def resolve_artist_and_song_names(item, currently_playing_type):
    if currently_playing_type == "track":
        return item["artists"][0]["name"], item["name"]
    if currently_playing_type == "episode":
        return item["show"]["publisher"], item["name"]
    return "", ""
