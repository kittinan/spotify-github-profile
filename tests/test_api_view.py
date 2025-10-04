import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to the path to import the api module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def client():
    """Create a test client for the view Flask application."""
    from api.view import app
    app.config.update({"TESTING": True})
    
    with app.test_client() as client:
        yield client


def test_catch_all_without_uid(client):
    """Test that request without uid parameter returns error."""
    response = client.get('/')
    
    assert response.status_code == 200
    assert response.data == b'not ok'


@patch('api.view.get_song_info')
@patch('api.view.make_svg')
def test_catch_all_with_valid_uid_offline(mock_make_svg, mock_get_song_info, client):
    """Test request with valid uid but user is offline."""
    # Mock song info to return None (offline)
    mock_get_song_info.return_value = (None, False, None, None)
    mock_make_svg.return_value = '<svg>offline</svg>'
    
    response = client.get('/?uid=test_user&show_offline=true')
    
    assert response.status_code == 200
    assert response.mimetype == 'image/svg+xml'
    assert response.headers['Cache-Control'] == 's-maxage=1'
    
    # Verify make_svg was called with offline parameters
    mock_make_svg.assert_called_once()
    args, kwargs = mock_make_svg.call_args
    assert args[0] in ["Currently not playing on Spotify", "Offline"]  # artist_name
    assert args[1] in ["Offline", "Currently not playing on Spotify"]  # song_name


@patch('api.view.get_song_info')
@patch('api.view.make_svg')
def test_catch_all_with_valid_uid_now_playing(mock_make_svg, mock_get_song_info, client):
    """Test request with valid uid and user is currently playing."""
    # Mock song info for currently playing track
    mock_item = {
        "name": "Test Song",
        "artists": [{"name": "Test Artist"}],
        "album": {"images": [{"url": "http://example.com/image.jpg"}] * 3},
        "uri": "spotify:track:123",
        "currently_playing_type": "track",
        "duration_ms": 240000
    }
    mock_get_song_info.return_value = (mock_item, True, 120000, 240000)
    mock_make_svg.return_value = '<svg>now playing</svg>'
    
    with patch('api.view.load_image', return_value=b'fake_image_data'):
        response = client.get('/?uid=test_user')
        
        assert response.status_code == 200
        assert response.mimetype == 'image/svg+xml'
        assert response.headers['Cache-Control'] == 's-maxage=1'
        
        # Verify make_svg was called with correct parameters
        mock_make_svg.assert_called_once()
        args, kwargs = mock_make_svg.call_args
        assert args[0] == "Test Artist"  # artist_name
        assert args[1] == "Test Song"    # song_name


@patch('api.view.get_song_info')
def test_catch_all_with_redirect(mock_get_song_info, client):
    """Test request with redirect parameter."""
    mock_item = {
        "uri": "spotify:track:123",
        "currently_playing_type": "track"
    }
    mock_get_song_info.return_value = (mock_item, True, None, None)
    
    response = client.get('/?uid=test_user&redirect=true')
    
    assert response.status_code == 302
    assert response.headers['Location'] == 'spotify:track:123'


@patch('api.view.get_song_info')
def test_catch_all_invalid_token_error(mock_get_song_info, client):
    """Test handling of invalid Spotify token."""
    from util.spotify import InvalidTokenError
    mock_get_song_info.side_effect = InvalidTokenError("Invalid token")
    
    response = client.get('/?uid=test_user')
    
    assert response.status_code == 200
    assert b'Invalid Spotify access_token or refresh_token' in response.data


@pytest.mark.parametrize("theme,expected_height", [
    ("default", 445),
    ("compact", 400),
    ("natemoo-re", 84),
    ("novatorem", 100),
    ("apple", 534),
    ("spotify-embed", 152)
])
@patch('api.view.get_song_info')
@patch('api.view.make_svg')
def test_different_themes(mock_make_svg, mock_get_song_info, client, theme, expected_height):
    """Test different theme parameters."""
    mock_item = {
        "name": "Test Song",
        "artists": [{"name": "Test Artist"}],
        "album": {"images": [{"url": "http://example.com/image.jpg"}] * 3},
        "currently_playing_type": "track"
    }
    mock_get_song_info.return_value = (mock_item, True, None, None)
    mock_make_svg.return_value = f'<svg height="{expected_height}"></svg>'
    
    with patch('api.view.load_image', return_value=b'fake_image_data'):
        response = client.get(f'/?uid=test_user&theme={theme}')
        
        assert response.status_code == 200
        mock_make_svg.assert_called_once()


@pytest.mark.parametrize("cover_image,expected_call", [
    ("true", True),
    ("false", False),
    ("", True)  # default value
])
@patch('api.view.get_song_info')
@patch('api.view.make_svg')
@patch('api.view.load_image')
def test_cover_image_parameter(mock_load_image, mock_make_svg, mock_get_song_info, client, cover_image, expected_call):
    """Test cover_image parameter handling."""
    mock_item = {
        "name": "Test Song", 
        "artists": [{"name": "Test Artist"}],
        "album": {"images": [{"url": "http://example.com/image.jpg"}] * 3},
        "currently_playing_type": "track"
    }
    mock_get_song_info.return_value = (mock_item, False, None, None)
    mock_make_svg.return_value = '<svg></svg>'
    mock_load_image.return_value = b'fake_image_data'
    
    if cover_image:
        response = client.get(f'/?uid=test_user&cover_image={cover_image}')
    else:
        response = client.get('/?uid=test_user')
    
    assert response.status_code == 200
    
    if expected_call:
        mock_load_image.assert_called_once()
    else:
        mock_load_image.assert_not_called()


@patch('api.view.get_song_info')
@patch('api.view.make_svg')
@patch('api.view.load_image')
def test_interchange_parameter(mock_load_image, mock_make_svg, mock_get_song_info, client):
    """Test interchange parameter swaps artist and song names."""
    mock_item = {
        "name": "Test Song",
        "artists": [{"name": "Test Artist"}],
        "album": {"images": [{"url": "http://example.com/image.jpg"}] * 3},
        "currently_playing_type": "track"
    }
    mock_get_song_info.return_value = (mock_item, True, None, None)
    mock_make_svg.return_value = '<svg></svg>'
    mock_load_image.return_value = b'fake_image_data'
    
    response = client.get('/?uid=test_user&interchange=true&cover_image=false')
    
    assert response.status_code == 200
    
    # Verify that artist and song names are swapped
    mock_make_svg.assert_called_once()
    args, kwargs = mock_make_svg.call_args
    assert args[0] == "Test Song"    # artist_name (swapped)
    assert args[1] == "Test Artist"  # song_name (swapped)


def test_helper_function_format_time_ms():
    """Test format_time_ms utility function."""
    from api.view import format_time_ms
    
    assert format_time_ms(0) == "0:00"
    assert format_time_ms(30000) == "0:30"
    assert format_time_ms(90000) == "1:30"
    assert format_time_ms(3600000) == "60:00"
    assert format_time_ms(None) == "0:00"
    assert format_time_ms(-1000) == "0:00"


def test_helper_function_calculate_progress_data():
    """Test calculate_progress_data utility function."""
    from api.view import calculate_progress_data
    
    # Test normal case
    result = calculate_progress_data(60000, 180000)
    assert result["progress_percentage"] == pytest.approx(33.33, rel=1e-2)
    assert result["current_time"] == "1:00"
    assert result["remaining_time"] == "-2:00"
    
    # Test edge cases
    result = calculate_progress_data(None, 180000)
    assert result["progress_percentage"] == 0
    assert result["current_time"] == "0:00"
    
    result = calculate_progress_data(60000, None)
    assert result["progress_percentage"] == 0
    
    # Test progress exceeds duration
    result = calculate_progress_data(200000, 180000)
    assert result["progress_percentage"] == 100


def test_helper_function_isLightOrDark():
    """Test isLightOrDark utility function."""
    from api.view import isLightOrDark
    
    # Test light colors
    assert isLightOrDark([255, 255, 255]) == "light"  # white
    assert isLightOrDark([200, 200, 200]) == "light"  # light gray
    
    # Test dark colors  
    assert isLightOrDark([0, 0, 0]) == "dark"      # black
    assert isLightOrDark([50, 50, 50]) == "dark"   # dark gray


def test_helper_function_encode_html_entities():
    """Test encode_html_entities utility function."""
    from api.view import encode_html_entities
    
    assert encode_html_entities("normal text") == "normal text"
    assert encode_html_entities("text & more") == "text &amp; more"
    assert encode_html_entities("<script>") == "&lt;script&gt;"
    assert encode_html_entities('"quotes"') == "&quot;quotes&quot;"


@patch('api.view.get_song_info')
@patch('api.view.make_svg')
def test_episode_handling(mock_make_svg, mock_get_song_info, client):
    """Test handling of podcast episodes."""
    mock_item = {
        "name": "Test Episode",
        "show": {"publisher": "Test Podcast"},
        "images": [{"url": "http://example.com/image.jpg"}] * 3,
        "currently_playing_type": "episode"
    }
    mock_get_song_info.return_value = (mock_item, True, None, None)
    mock_make_svg.return_value = '<svg></svg>'
    
    with patch('api.view.load_image', return_value=b'fake_image_data'):
        response = client.get('/?uid=test_user')
        
        assert response.status_code == 200
        
        # Verify correct artist/song names for episodes
        mock_make_svg.assert_called_once()
        args, kwargs = mock_make_svg.call_args
        assert args[0] == "Test Podcast"  # artist_name (publisher)
        assert args[1] == "Test Episode"  # song_name


@pytest.mark.parametrize("show_offline,interchange,expected_artist,expected_song", [
    (True, False, "Offline", "Currently not playing on Spotify"),
    (True, True, "Currently not playing on Spotify", "Offline"),
    (False, False, "Offline", "Currently not playing on Spotify"),
    (False, True, "Currently not playing on Spotify", "Offline")
])
@patch('api.view.get_song_info')
@patch('api.view.make_svg')
def test_offline_text_with_interchange(mock_make_svg, mock_get_song_info, client, show_offline, interchange, expected_artist, expected_song):
    """Test offline text with different interchange settings."""
    mock_get_song_info.return_value = (None, False, None, None)
    mock_make_svg.return_value = '<svg></svg>'
    
    params = f'uid=test_user&show_offline={str(show_offline).lower()}&interchange={str(interchange).lower()}'
    response = client.get(f'/?{params}')
    
    assert response.status_code == 200
    
    mock_make_svg.assert_called_once()
    args, kwargs = mock_make_svg.call_args
    assert args[0] == expected_artist  # artist_name
    assert args[1] == expected_song    # song_name


def test_cache_functionality():
    """Test token caching functionality."""
    from api.view import get_cache_token_info, delete_cache_token_info, CACHE_TOKEN_INFO
    
    # Clear cache
    CACHE_TOKEN_INFO.clear()
    
    # Test empty cache
    result = get_cache_token_info("test_uid")
    assert result is None
    
    # Test cache deletion
    CACHE_TOKEN_INFO["test_uid"] = {"access_token": "test_token"}
    delete_cache_token_info("test_uid")
    assert "test_uid" not in CACHE_TOKEN_INFO


@patch('api.view.load_image')
def test_load_image_error_handling(mock_load_image):
    """Test load_image error handling."""
    from api.view import to_img_b64
    
    # Test when load_image returns None
    mock_load_image.return_value = None
    
    # to_img_b64 should handle None gracefully
    result = to_img_b64(None)
    assert result == ""  # Should return empty string for None input


@pytest.mark.parametrize("bar_color,background_color,mode", [
    ("ff0000", "000000", "light"),
    ("00ff00", "ffffff", "dark"), 
    ("0000ff", "121212", "light"),
    ("", "", "")  # test default values
])
@patch('api.view.get_song_info')
@patch('api.view.make_svg')
@patch('api.view.load_image')
def test_color_parameters(mock_load_image, mock_make_svg, mock_get_song_info, client, bar_color, background_color, mode):
    """Test color and mode parameters."""
    mock_item = {
        "name": "Test Song",
        "artists": [{"name": "Test Artist"}],
        "album": {"images": [{"url": "http://example.com/image.jpg"}] * 3},
        "currently_playing_type": "track"
    }
    mock_get_song_info.return_value = (mock_item, True, None, None)
    mock_make_svg.return_value = '<svg></svg>'
    mock_load_image.return_value = b'fake_image_data'
    
    params = f'uid=test_user&bar_color={bar_color}&background_color={background_color}&mode={mode}&cover_image=false'
    response = client.get(f'/?{params}')
    
    assert response.status_code == 200
    mock_make_svg.assert_called_once()


@patch('api.view.get_song_info')
@patch('api.view.make_svg')
@patch('api.view.load_image')
@patch('PIL.Image.open')
@patch('api.view.colorgram.extract')
def test_bar_color_from_cover(mock_extract, mock_pil_open, mock_load_image, mock_make_svg, mock_get_song_info, client):
    """Test extracting bar color from cover image."""
    # Mock PIL Image
    mock_image = MagicMock()
    mock_pil_open.return_value = mock_image
    
    # Mock colorgram color extraction
    mock_color = MagicMock()
    mock_color.rgb.r = 255
    mock_color.rgb.g = 100
    mock_color.rgb.b = 100
    mock_extract.return_value = [mock_color]
    
    mock_item = {
        "name": "Test Song",
        "artists": [{"name": "Test Artist"}],
        "album": {"images": [{"url": "http://example.com/image.jpg"}] * 3},
        "currently_playing_type": "track"
    }
    mock_get_song_info.return_value = (mock_item, True, None, None)
    mock_make_svg.return_value = '<svg></svg>'
    mock_load_image.return_value = b'fake_image_data'
    
    response = client.get('/?uid=test_user&bar_color_cover=true')
    
    assert response.status_code == 200
    mock_extract.assert_called_once()
    mock_make_svg.assert_called_once()


def test_generate_css_bar():
    """Test generate_css_bar utility function."""
    from api.view import generate_css_bar
    
    # Test basic functionality
    css = generate_css_bar(5)
    assert isinstance(css, str)
    assert 'bar:nth-child(' in css
    assert 'animation-duration:' in css
    
    # Test with different number of bars
    css_10 = generate_css_bar(10)
    css_20 = generate_css_bar(20)
    assert len(css_20) > len(css_10)  # More bars should generate more CSS
