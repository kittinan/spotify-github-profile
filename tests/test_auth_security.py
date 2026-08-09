import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Add the repository root to the import path.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_login_generates_state_and_sets_hardened_cookie():
    """The authorization request must carry a state bound to an HttpOnly cookie."""
    from api.login import app

    with patch('api.login.secrets.token_urlsafe', return_value='test_state'), \
         patch('util.spotify.SPOTIFY_CLIENT_ID', 'test_client_id'), \
         patch('util.spotify.REDIRECT_URI', 'https://example.com/api/callback'):
        with app.test_client() as client:
            response = client.get('/')

    assert response.status_code == 302
    assert 'state=test_state' in response.headers['Location']

    cookie = response.headers.get('Set-Cookie', '')
    assert 'spotify_oauth_state=test_state' in cookie
    assert 'Max-Age=600' in cookie
    assert 'HttpOnly' in cookie
    assert 'Secure' in cookie
    assert 'SameSite=Lax' in cookie


def test_normalize_token_info_persists_expiry_and_existing_refresh_token():
    """Refresh responses that omit refresh_token must keep the previous token."""
    from util import spotify

    normalized = spotify.normalize_token_info(
        {
            'access_token': 'new_access_token',
            'expires_in': '3600',
        },
        existing_refresh_token='existing_refresh_token',
        now=1000,
    )

    assert normalized == {
        'access_token': 'new_access_token',
        'expires_in': 3600,
        'refresh_token': 'existing_refresh_token',
        'expired_ts': 4600,
    }


def _load_view_module():
    # Keep this test independent from the CI environment and from test order.
    with patch.dict(os.environ, {'TESTING': 'true'}):
        from api import view
    return view


def _mock_token_document(token_info):
    document = MagicMock()
    snapshot = MagicMock()
    snapshot.exists = True
    snapshot.to_dict.return_value = token_info
    document.get.return_value = snapshot

    collection = MagicMock()
    collection.document.return_value = document

    database = MagicMock()
    database.collection.return_value = collection
    return database, document


def test_get_access_token_does_not_log_bearer_token(capsys):
    """Bearer tokens are credentials and must never be printed to application logs."""
    view = _load_view_module()
    view.CACHE_TOKEN_INFO.clear()
    view.CACHE_TOKEN_INFO['test_uid'] = {
        'access_token': 'super_secret_access_token',
        'refresh_token': 'refresh_token',
        'expired_ts': 4600,
    }

    with patch.object(view, 'time', return_value=1000):
        assert view.get_access_token('test_uid') == 'super_secret_access_token'

    captured = capsys.readouterr()
    assert 'super_secret_access_token' not in captured.out
    assert 'super_secret_access_token' not in captured.err


def test_refresh_keeps_existing_refresh_token_when_spotify_omits_rotation():
    """A refresh response may omit refresh_token; the stored token must survive."""
    view = _load_view_module()
    view.CACHE_TOKEN_INFO.clear()

    database, document = _mock_token_document({
        'access_token': 'expired_access_token',
        'refresh_token': 'existing_refresh_token',
        'expires_in': 3600,
        'expired_ts': 900,
    })

    with patch.object(view, 'db', database), \
         patch.object(view, 'time', return_value=1000), \
         patch.object(
             view.spotify,
             'refresh_token',
             return_value={
                 'access_token': 'new_access_token',
                 'expires_in': 3600,
             },
         ):
        access_token = view.get_access_token('test_uid')

    assert access_token == 'new_access_token'
    document.update.assert_called_once_with({
        'access_token': 'new_access_token',
        'refresh_token': 'existing_refresh_token',
        'expires_in': 3600,
        'expired_ts': 4600,
    })
    assert view.CACHE_TOKEN_INFO['test_uid']['refresh_token'] == 'existing_refresh_token'


def test_refresh_persists_rotated_refresh_token():
    """If Spotify rotates the refresh token, the new value must replace the old one."""
    view = _load_view_module()
    view.CACHE_TOKEN_INFO.clear()

    database, document = _mock_token_document({
        'access_token': 'expired_access_token',
        'refresh_token': 'old_refresh_token',
        'expires_in': 3600,
        'expired_ts': 900,
    })

    with patch.object(view, 'db', database), \
         patch.object(view, 'time', return_value=1000), \
         patch.object(
             view.spotify,
             'refresh_token',
             return_value={
                 'access_token': 'new_access_token',
                 'refresh_token': 'rotated_refresh_token',
                 'expires_in': 1800,
             },
         ):
        access_token = view.get_access_token('test_uid')

    assert access_token == 'new_access_token'
    document.update.assert_called_once_with({
        'access_token': 'new_access_token',
        'refresh_token': 'rotated_refresh_token',
        'expires_in': 1800,
        'expired_ts': 2800,
    })
    assert view.CACHE_TOKEN_INFO['test_uid']['refresh_token'] == 'rotated_refresh_token'


def test_transient_refresh_error_does_not_delete_credentials():
    """Only invalid_grant should invalidate persisted Spotify credentials."""
    view = _load_view_module()
    view.CACHE_TOKEN_INFO.clear()

    database, document = _mock_token_document({
        'access_token': 'expired_access_token',
        'refresh_token': 'existing_refresh_token',
        'expires_in': 3600,
        'expired_ts': 900,
    })

    with patch.object(view, 'db', database), \
         patch.object(view, 'time', return_value=1000), \
         patch.object(
             view.spotify,
             'refresh_token',
             return_value={
                 'error': 'temporarily_unavailable',
                 'error_description': 'Please retry later',
             },
         ):
        with pytest.raises(view.spotify.TokenRefreshError, match='temporarily_unavailable'):
            view.get_access_token('test_uid')

    document.delete.assert_not_called()
    document.update.assert_not_called()
    assert view.CACHE_TOKEN_INFO['test_uid']['refresh_token'] == 'existing_refresh_token'


def test_malformed_refresh_response_does_not_invalidate_credentials():
    """Incomplete refresh metadata is a service failure, not revoked authorization."""
    view = _load_view_module()
    view.CACHE_TOKEN_INFO.clear()

    database, document = _mock_token_document({
        'access_token': 'expired_access_token',
        'refresh_token': 'existing_refresh_token',
        'expires_in': 3600,
        'expired_ts': 900,
    })

    with patch.object(view, 'db', database), \
         patch.object(view, 'time', return_value=1000), \
         patch.object(
             view.spotify,
             'refresh_token',
             return_value={'expires_in': 3600},
         ):
        with pytest.raises(view.spotify.TokenRefreshError, match='incomplete'):
            view.get_access_token('test_uid')

    document.delete.assert_not_called()
    document.update.assert_not_called()


def test_view_reports_transient_refresh_failure_without_reauth_message():
    """Temporary refresh failures should return a retryable server error."""
    view = _load_view_module()

    with patch.object(
        view,
        'get_song_info',
        side_effect=view.spotify.TokenRefreshError('temporary failure'),
    ):
        with view.app.test_client() as client:
            response = client.get('/?uid=test_user')

    assert response.status_code == 502
    assert b'temporarily unavailable' in response.data
    assert b'Please re-login' not in response.data


def test_normalize_token_info_rejects_invalid_expiry():
    """Invalid token metadata should fail clearly instead of poisoning the cache."""
    from util import spotify

    with pytest.raises(ValueError, match='expires_in'):
        spotify.normalize_token_info(
            {'access_token': 'token', 'expires_in': 'not-a-number'},
            now=1000,
        )
