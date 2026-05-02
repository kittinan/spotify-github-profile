import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from util.remaster import remove_remaster


def test_no_remaster_unchanged():
    assert remove_remaster("Hotel California") == "Hotel California"


def test_remaster_suffix_dash():
    assert remove_remaster("Hotel California - 2013 Remaster") == "Hotel California"


def test_remaster_suffix_parens():
    assert remove_remaster("Come Together (Remastered)") == "Come Together"


def test_remastered_with_year_parens():
    assert remove_remaster("Roxanne (Remastered 2003)") == "Roxanne"


def test_remaster_year_before_keyword():
    assert remove_remaster("Starman - 2012 Remaster") == "Starman"


def test_remastered_version():
    assert remove_remaster("Heroes - Remastered Version") == "Heroes"


def test_remastered_year_version():
    assert remove_remaster("Life On Mars? (2015 Remastered Version)") == "Life On Mars?"


def test_case_insensitive():
    assert remove_remaster("Song Title - REMASTERED") == "Song Title"


def test_remaster_not_mid_title():
    """Remaster text in the middle of a title must not be removed."""
    title = "Remastered Soul"
    assert remove_remaster(title) == "Remastered Soul"
