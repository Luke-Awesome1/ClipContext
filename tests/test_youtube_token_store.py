from src.youtube.token_store import StoredCredentials, YouTubeCredentialStore


def _credentials(**overrides) -> StoredCredentials:
    defaults = dict(
        access_token="access-token",
        refresh_token="refresh-token",
        token_uri="https://oauth2.googleapis.com/token",
        scopes=["https://www.googleapis.com/auth/youtube.upload"],
        expiry=None,
        channel_id="UC123",
        channel_title="Test Channel",
        channel_thumbnail_url="https://example.com/thumb.jpg",
    )
    defaults.update(overrides)
    return StoredCredentials(**defaults)


def test_save_and_get_round_trips():
    store = YouTubeCredentialStore()
    store.save("session-a", _credentials())

    result = store.get("session-a")
    assert result is not None
    assert result.channel_title == "Test Channel"


def test_sessions_are_isolated():
    store = YouTubeCredentialStore()
    store.save("session-a", _credentials(channel_title="Channel A"))
    store.save("session-b", _credentials(channel_title="Channel B"))

    assert store.get("session-a").channel_title == "Channel A"
    assert store.get("session-b").channel_title == "Channel B"
    assert store.get("session-c") is None


def test_delete_removes_only_that_session():
    store = YouTubeCredentialStore()
    store.save("session-a", _credentials())
    store.save("session-b", _credentials())

    store.delete("session-a")

    assert store.get("session-a") is None
    assert store.get("session-b") is not None


def test_update_tokens_preserves_channel_metadata():
    store = YouTubeCredentialStore()
    store.save("session-a", _credentials(access_token="old-token", expiry=None))

    store.update_tokens("session-a", access_token="new-token", expiry="2030-01-01T00:00:00")

    result = store.get("session-a")
    assert result.access_token == "new-token"
    assert result.expiry == "2030-01-01T00:00:00"
    assert result.channel_title == "Test Channel"


def test_update_tokens_on_unknown_session_is_a_no_op():
    store = YouTubeCredentialStore()
    store.update_tokens("missing-session", access_token="x", expiry=None)

    assert store.get("missing-session") is None
