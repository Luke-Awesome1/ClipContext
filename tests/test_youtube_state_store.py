import time

from src.youtube.state_store import OAuthStateStore


def test_state_create_and_consume_returns_bound_code_verifier():
    store = OAuthStateStore()
    state = store.create("session-a", "verifier-123")

    assert store.consume(state, "session-a") == "verifier-123"


def test_state_consume_rejects_session_mismatch():
    store = OAuthStateStore()
    state = store.create("session-a", "verifier-123")

    assert store.consume(state, "session-b") is None


def test_state_consume_is_single_use():
    store = OAuthStateStore()
    state = store.create("session-a", "verifier-123")

    assert store.consume(state, "session-a") == "verifier-123"
    assert store.consume(state, "session-a") is None


def test_state_consume_rejects_unknown_state():
    store = OAuthStateStore()

    assert store.consume("not-a-real-state", "session-a") is None


def test_state_consume_rejects_expired_state(monkeypatch):
    store = OAuthStateStore()
    state = store.create("session-a", "verifier-123")

    # Force every stored entry to look expired without waiting on a real clock.
    future = time.time() + 10_000
    monkeypatch.setattr(time, "time", lambda: future)

    assert store.consume(state, "session-a") is None
