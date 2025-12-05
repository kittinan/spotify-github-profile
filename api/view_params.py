from dataclasses import dataclass

@dataclass
class ViewParams:
    uid: str
    cover_image: bool
    is_redirect: bool
    theme: str
    bar_color: str
    background_color: str
    is_bar_color_from_cover: bool
    show_offline: bool
    interchange: bool
    mode: str
    is_enable_profanity: bool

