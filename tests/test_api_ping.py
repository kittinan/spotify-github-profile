import pytest
import sys
import os

# Add the parent directory to the path to import the api module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def client():
    """Create a test client for the ping Flask application."""
    from api.ping import app
    app.config.update({"TESTING": True})
    
    with app.test_client() as client:
        yield client


def test_ping_root_path(client):
    """Test that root path returns pong response."""
    response = client.get('/')
    
    # Check that it's a successful response
    assert response.status_code == 200
    
    # Check the response is JSON
    assert response.content_type == 'application/json'
    
    # Check the response data
    data = response.get_json()
    assert data is not None
    assert data['status'] == 'ok'
    assert data['message'] == 'pong'


def test_ping_with_path(client):
    """Test that any path returns pong response."""
    response = client.get('/some/random/path')
    
    # Check that it's a successful response
    assert response.status_code == 200
    
    # Check the response data
    data = response.get_json()
    assert data is not None
    assert data['status'] == 'ok'
    assert data['message'] == 'pong'


@pytest.mark.parametrize("path", ['/', '/ping', '/health', '/status', '/test/nested/path'])
def test_multiple_paths(client, path):
    """Test that various paths all return pong properly."""
    response = client.get(path)
    
    assert response.status_code == 200
    data = response.get_json()
    assert data is not None
    assert data['status'] == 'ok'
    assert data['message'] == 'pong'


def test_response_structure(client):
    """Test that the response has the correct structure."""
    response = client.get('/')
    
    assert response.status_code == 200
    data = response.get_json()
    
    # Check that both required fields are present
    assert 'status' in data
    assert 'message' in data
    
    # Check that values are strings
    assert isinstance(data['status'], str)
    assert isinstance(data['message'], str)


@pytest.mark.parametrize("method,expected_status", [
    ("GET", 200),
    ("POST", 405),  # Method not allowed
    ("PUT", 405),   # Method not allowed
    ("DELETE", 405),  # Method not allowed
])
def test_http_methods(client, method, expected_status):
    """Test that different HTTP methods work correctly."""
    response = getattr(client, method.lower())('/')
    assert response.status_code == expected_status


def test_query_parameters_ignored(client):
    """Test that query parameters in the request URL don't affect the response."""
    response = client.get('/?param1=value1&param2=value2')
    
    # Should still return pong regardless of query parameters
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'ok'
    assert data['message'] == 'pong'


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
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'ok'
    assert data['message'] == 'pong'


@pytest.mark.parametrize("path", ['/PING', '/Ping', '/ping', '/HEALTH', '/Health', '/health'])
def test_case_sensitivity(client, path):
    """Test that path matching is case sensitive."""
    response = client.get(path)
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'ok'


def test_response_headers(client):
    """Test that the response contains appropriate headers."""
    response = client.get('/')
    
    # Check content type
    assert response.content_type == 'application/json'
    
    # Check response status
    assert response.status_code == 200


def test_json_content_type(client):
    """Test that the response is proper JSON."""
    response = client.get('/')
    
    # Check that content-type is application/json
    assert 'application/json' in response.content_type
    
    # Verify we can parse it as JSON
    data = response.get_json()
    assert data is not None
    assert isinstance(data, dict)


def test_pong_message_consistency(client):
    """Test that pong message is consistent across multiple requests."""
    responses = [client.get('/') for _ in range(5)]
    
    for response in responses:
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'ok'
        assert data['message'] == 'pong'


def test_no_side_effects(client):
    """Test that ping endpoint has no side effects."""
    # Make multiple requests
    for _ in range(10):
        response = client.get('/')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'ok'
        assert data['message'] == 'pong'


def test_response_is_not_html(client):
    """Test that response is JSON, not HTML."""
    response = client.get('/')
    
    # Should be JSON, not HTML
    assert 'text/html' not in response.content_type
    assert 'application/json' in response.content_type


def test_no_redirect(client):
    """Test that ping endpoint doesn't redirect."""
    response = client.get('/')
    
    # Should be a direct response, not a redirect
    assert response.status_code == 200
    assert not (300 <= response.status_code < 400)


@pytest.mark.parametrize("path", ['/', '/ping', '/status'])
def test_always_returns_ok_status(client, path):
    """Test that all requests return 'ok' status."""
    response = client.get(path)
    data = response.get_json()
    assert data['status'] == 'ok'


def test_response_time_reasonable(client):
    """Test that ping responds quickly (basic performance check)."""
    import time
    
    start_time = time.time()
    response = client.get('/')
    end_time = time.time()
    
    # Should respond in less than 1 second (very generous for a simple endpoint)
    assert (end_time - start_time) < 1.0
    assert response.status_code == 200
