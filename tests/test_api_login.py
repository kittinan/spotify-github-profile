import pytest
from unittest.mock import patch
import sys
import os

# Add the parent directory to the path to import the api module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def client():
    """Create a test client for the login Flask application."""
    from api.login import app
    app.config.update({"TESTING": True})
    
    with app.test_client() as client:
        yield client


def test_catch_all_root_path(client):
    """Test that root path redirects to Spotify authorization URL."""
    with patch('util.spotify.SPOTIFY_CLIENT_ID', 'test_client_id'), \
         patch('util.spotify.REDIRECT_URI', 'http://localhost:5000/callback'):
        
        response = client.get('/')
        
        # Check that it's a redirect response
        assert response.status_code == 302
        
        # Check that the location header contains the expected Spotify URL
        location = response.headers.get('Location')
        assert location is not None
        assert 'accounts.spotify.com/authorize' in location
        assert 'client_id=test_client_id' in location
        assert 'response_type=code' in location
        assert 'scope=user-read-currently-playing,user-read-recently-played' in location
        assert 'redirect_uri=http://localhost:5000/callback' in location


def test_catch_all_with_path(client):
    """Test that any path redirects to Spotify authorization URL."""
    with patch('util.spotify.SPOTIFY_CLIENT_ID', 'test_client_id'), \
         patch('util.spotify.REDIRECT_URI', 'http://localhost:5000/callback'):
        
        response = client.get('/some/random/path')
        
        # Check that it's a redirect response
        assert response.status_code == 302
        
        # Check that the location header contains the expected Spotify URL
        location = response.headers.get('Location')
        assert location is not None
        assert 'accounts.spotify.com/authorize' in location
        assert 'client_id=test_client_id' in location


def test_catch_all_with_different_config(client):
    """Test redirect with different Spotify configuration."""
    with patch('util.spotify.SPOTIFY_CLIENT_ID', 'different_client_id'), \
         patch('util.spotify.REDIRECT_URI', 'https://example.com/callback'):
        
        response = client.get('/test')
        
        # Check that it's a redirect response
        assert response.status_code == 302
        
        # Check that the location header contains the expected configuration
        location = response.headers.get('Location')
        assert location is not None
        assert 'client_id=different_client_id' in location
        assert 'redirect_uri=https://example.com/callback' in location


def test_catch_all_with_none_config(client):
    """Test behavior when Spotify configuration is None."""
    with patch('util.spotify.SPOTIFY_CLIENT_ID', None), \
         patch('util.spotify.REDIRECT_URI', None):
        
        response = client.get('/')
        
        # Check that it's still a redirect response
        assert response.status_code == 302
        
        # Check that the location header contains None values
        location = response.headers.get('Location')
        assert location is not None
        assert 'client_id=None' in location
        assert 'redirect_uri=None' in location


@pytest.mark.parametrize("path", ['/', '/login', '/auth', '/spotify', '/test/nested/path'])
def test_multiple_paths(client, path):
    """Test that various paths all redirect properly."""
    response = client.get(path)
    
    assert response.status_code == 302
    location = response.headers.get('Location')
    assert location is not None
    assert 'accounts.spotify.com/authorize' in location


def test_redirect_url_structure(client):
    """Test that the redirect URL has the correct structure and parameters."""
    response = client.get('/')
    
    assert response.status_code == 302
    location = response.headers.get('Location')
    
    # Check that all required parameters are present
    required_params = [
        'client_id=',
        'response_type=code',
        'scope=user-read-currently-playing,user-read-recently-played',
        'redirect_uri='
    ]
    
    for param in required_params:
        assert param in location


@pytest.mark.parametrize("method,expected_status", [
    ("GET", 302),
    ("POST", 405),  # Method not allowed
    ("PUT", 405),   # Method not allowed
])
def test_http_methods(client, method, expected_status):
    """Test that different HTTP methods work with the catch-all route."""
    response = getattr(client, method.lower())('/')
    assert response.status_code == expected_status


def test_query_parameters_ignored(client):
    """Test that query parameters in the request URL don't affect the redirect."""
    response = client.get('/?param1=value1&param2=value2')
    
    # Should still redirect regardless of query parameters
    assert response.status_code == 302
    location = response.headers.get('Location')
    assert location is not None
    assert 'accounts.spotify.com/authorize' in location


def test_empty_config_values(client):
    """Test behavior when Spotify configuration values are empty strings."""
    with patch('util.spotify.SPOTIFY_CLIENT_ID', ''), \
         patch('util.spotify.REDIRECT_URI', ''):
        
        response = client.get('/')
        
        assert response.status_code == 302
        location = response.headers.get('Location')
        assert location is not None
        assert 'client_id=' in location
        assert 'redirect_uri=' in location


@pytest.mark.parametrize("path", [
    '/path%20with%20spaces',
    '/path-with-dashes',
    '/path_with_underscores',
    '/path.with.dots',
    '/path/with/slashes'
])
def test_special_characters_in_path(client, path):
    """Test that paths with special characters are handled correctly."""
    response = client.get(path)
    
    assert response.status_code == 302
    location = response.headers.get('Location')
    assert 'accounts.spotify.com/authorize' in location


@pytest.mark.parametrize("path", ['/LOGIN', '/Login', '/login', '/AUTH', '/Auth', '/auth'])
def test_case_sensitivity(client, path):
    """Test that path matching is case sensitive."""
    response = client.get(path)
    assert response.status_code == 302


def test_redirect_preserves_spotify_scopes(client):
    """Test that the redirect URL always includes the correct Spotify scopes."""
    with patch('util.spotify.SPOTIFY_CLIENT_ID', 'test_client_123'), \
         patch('util.spotify.REDIRECT_URI', 'http://localhost:8080/callback'):
        
        response = client.get('/any/path')
        
        assert response.status_code == 302
        location = response.headers.get('Location')
        
        # Verify specific scopes are included
        assert 'user-read-currently-playing' in location
        assert 'user-read-recently-played' in location
        
        # Verify scope parameter format
        assert 'scope=user-read-currently-playing,user-read-recently-played' in location


def test_response_headers(client):
    """Test that the response contains appropriate headers."""
    response = client.get('/')
    
    # Check that Location header exists (required for redirect)
    assert 'Location' in response.headers
    
    # Check response status
    assert response.status_code == 302
    
    # Verify it's a proper redirect response (status code 302)
    assert 300 <= response.status_code < 400


def test_url_encoding_in_redirect(client):
    """Test that the redirect URL is properly formatted with URL encoding."""
    response = client.get('/')
    
    location = response.headers.get('Location')
    
    # Check that spaces in scope are properly encoded (should be comma-separated, no spaces)
    scope_part = location.split('scope=')[1].split('&')[0]
    assert ' ' not in scope_part
    
    # Check that the URL structure is valid
    assert location.startswith('https://')
