import sys
import os

# Add the parent directory to the path to import the util module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_profanity_check_clean_text():
    """Test that clean text is returned unchanged."""
    from util.profanity import profanity_check

    result = profanity_check("Hello World")

    assert result == "Hello World"


def test_profanity_check_profane_text():
    """Test that profane text is censored."""
    from util.profanity import profanity_check

    result = profanity_check("fuck")

    # The exact censoring depends on the library, but should be different
    assert result != "fuck"
    assert "*" in result  # Should contain censoring characters
