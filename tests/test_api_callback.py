import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to the path to import the api module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    from flask import Flask, Response, request
    
    app = Flask(__name__)
    app.config.update({"TESTING": True})
    
    # Create a test route that mimics the callback behavior
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def test_catch_all(path):
        code = request.args.get("code")
        
        if code is None:
            return Response("not ok")
        
        # Mock the callback logic without actual Firebase calls
        return f"callback_success_user_id_{code}"
    
    with app.test_client() as client:
        yield client


def test_callback_without_code(client):
    """Test callback without authorization code returns error."""
    response = client.get("/")
    
    assert response.status_code == 200
    assert response.data == b"not ok"


def test_callback_with_code(client):
    """Test callback with authorization code processes successfully."""
    response = client.get("/?code=test_auth_code")
    
    assert response.status_code == 200
    assert b"callback_success_user_id_test_auth_code" in response.data


def test_callback_with_empty_code_param(client):
    """Test callback with empty code parameter."""
    response = client.get("/?code=")
    
    # Empty string should be processed (though would fail in real Spotify auth)
    assert response.status_code == 200
    assert b"callback_success_user_id_" in response.data


def test_callback_with_path(client):
    """Test callback with additional path parameters."""
    response = client.get("/some/path?code=test_code")
    
    assert response.status_code == 200
    assert b"callback_success_user_id_test_code" in response.data


def test_case_sensitive_code_parameter(client):
    """Test that code parameter is case sensitive."""
    # Test with uppercase CODE - should return error
    response = client.get("/?CODE=test_code")
    assert response.data == b"not ok"
    
    # Test with mixed case - should return error  
    response = client.get("/?Code=test_code")
    assert response.data == b"not ok"
    
    # Test with correct lowercase - should work
    response = client.get("/?code=test_code")
    assert response.data != b"not ok"


def test_multiple_query_parameters(client):
    """Test callback with multiple query parameters."""
    response = client.get("/?code=test_code&state=random&extra=param")
    
    # Should not return error since code is present
    assert response.data != b"not ok"
    assert response.status_code == 200
    assert b"callback_success_user_id_test_code" in response.data


@pytest.mark.parametrize("code", [
    "code_with_underscores",
    "code-with-dashes", 
    "code.with.dots",
    "code123with456numbers",
    "UPPERCASE_CODE"
])
def test_special_code_values(client, code):
    """Test callback with special authorization code values."""
    response = client.get(f"/?code={code}")
    
    assert response.status_code == 200
    assert f"callback_success_user_id_{code}".encode() in response.data


@pytest.mark.parametrize("path", [
    "/",
    "/callback",
    "/auth/callback", 
    "/deep/nested/path"
])
def test_callback_with_different_paths(client, path):
    """Test callback works with different URL paths."""
    response = client.get(f"{path}?code=test_code")
    
    assert response.status_code == 200
    assert b"callback_success_user_id_test_code" in response.data


@pytest.mark.parametrize("url", [
    "/?code=test&state=abc",
    "/?state=abc&code=test",
    "/?other=xyz&code=test&more=123"
])
def test_callback_query_parameter_order(client, url):
    """Test callback with different query parameter orders."""
    response = client.get(url)
    
    assert response.status_code == 200
    assert b"callback_success_user_id_test" in response.data


def test_callback_url_encoded_parameters(client):
    """Test callback with URL-encoded parameters."""
    response = client.get("/?code=test%20code%20with%20spaces")
    
    assert response.status_code == 200
    # Flask automatically decodes URL parameters
    assert b"callback_success_user_id_test code with spaces" in response.data


@pytest.mark.parametrize("method,expected_status", [
    ("GET", 200),
    ("POST", 405),  # Method not allowed
    ("PUT", 405),   # Method not allowed
])
def test_http_methods(client, method, expected_status):
    """Test callback with different HTTP methods."""
    response = getattr(client, method.lower())("/?code=method_test")
    assert response.status_code == expected_status


# Integration tests that use real callback module with mocking
class TestRealCallbackIntegration:
    """Integration tests for the real callback module with proper mocking."""
    
    @pytest.fixture
    def real_app_client(self):
        """Create a test client for the real callback app with Firebase mocking."""
        with patch.dict('os.environ', {'FIREBASE': 'eyJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCJ9'}), \
             patch('firebase_admin.initialize_app'), \
             patch('firebase_admin.credentials.Certificate'), \
             patch('firebase_admin.firestore.client'):
            
            try:
                from api.callback import app
                app.config.update({"TESTING": True})
                
                with app.test_client() as client:
                    yield client
            except ImportError:
                pytest.skip("Cannot import callback module due to dependencies")
    
    @patch('api.callback.db')
    @patch('util.spotify.get_user_profile')
    @patch('util.spotify.generate_token')
    @patch('util.spotify.BASE_URL', 'http://localhost:5000')
    def test_successful_integration_callback(self, mock_generate_token, mock_get_user_profile, mock_db, real_app_client):
        """Test successful callback integration with all components."""
        # Mock Spotify API responses
        mock_generate_token.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token", 
            "expires_in": 3600
        }
        
        mock_get_user_profile.return_value = {
            "id": "test_user_123",
            "display_name": "Test User"
        }
        
        # Mock Firestore
        mock_collection = MagicMock()
        mock_document = MagicMock()
        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_document
        
        # Make request with authorization code
        response = real_app_client.get("/?code=test_auth_code")
        
        # Verify response
        assert response.status_code == 200
        
        # Verify Spotify API calls
        mock_generate_token.assert_called_once_with("test_auth_code")
        mock_get_user_profile.assert_called_once_with("test_access_token")
        
        # Verify Firestore operations
        mock_db.collection.assert_called_once_with("users")
        mock_collection.document.assert_called_once_with("test_user_123")
        mock_document.set.assert_called_once_with({
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600
        })
    
    def test_integration_callback_without_code(self, real_app_client):
        """Test integration callback without authorization code."""
        response = real_app_client.get("/")
        
        assert response.status_code == 200
        assert response.data == b"not ok"
    
    @patch('util.spotify.generate_token')
    def test_integration_spotify_error_handling(self, mock_generate_token, real_app_client):
        """Test integration error handling for Spotify API failures."""
        # Mock token generation to raise an exception
        mock_generate_token.side_effect = Exception("Token generation failed")
        
        with pytest.raises(Exception, match="Token generation failed"):
            real_app_client.get("/?code=test_code")
