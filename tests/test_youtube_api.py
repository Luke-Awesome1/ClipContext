import threading

import pytest
from fastapi.testclient import TestClient

import src.api.youtube_routes as youtube_routes
from src.api.app import app
from src.api.jobs import registry as job_registry
from src.api.schemas import JobStatus
from src.youtube.token_store import StoredCredentials, credential_store


@pytest.fixture
def client():
    return TestClient(app)


def _connect_session(client: TestClient, session_id: str) -> None:
    client.cookies.set("cc_session", session_id)
    credential_store.save(
        session_id,
        StoredCredentials(
            access_token="token",
            refresh_token="refresh",
            token_uri="https://oauth2.googleapis.com/token",
            scopes=["https://www.googleapis.com/auth/youtube.upload"],
            expiry=None,
            channel_id="UC1",
            channel_title="Test Channel",
            channel_thumbnail_url="https://example.com/thumb.jpg",
        ),
    )


def _complete_job(job_id: str) -> None:
    record, _ = job_registry.get_or_create(job_id)
    with record.lock:
        record.status = JobStatus.COMPLETED


def test_status_disconnected_without_session_cookie(client):
    response = client.get("/api/youtube/status")
    assert response.status_code == 200
    assert response.json() == {
        "connected": False,
        "channel_id": None,
        "channel_title": None,
        "channel_thumbnail_url": None,
    }


def test_status_connected_reflects_stored_channel(client):
    _connect_session(client, "session-status-connected")

    response = client.get("/api/youtube/status")
    assert response.status_code == 200
    body = response.json()
    assert body["connected"] is True
    assert body["channel_title"] == "Test Channel"

    credential_store.delete("session-status-connected")


def test_connect_returns_structured_error_when_oauth_not_configured(client, monkeypatch):
    monkeypatch.setattr("src.api.youtube_routes.is_youtube_oauth_configured", lambda: False)

    response = client.get("/api/youtube/connect", follow_redirects=False)
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "YOUTUBE_OAUTH_NOT_CONFIGURED"


def test_disconnect_clears_stored_credentials(client, monkeypatch):
    monkeypatch.setattr(youtube_routes, "revoke_credentials", lambda stored: None)
    _connect_session(client, "session-disconnect")

    response = client.post("/api/youtube/disconnect")
    assert response.status_code == 200
    assert response.json()["connected"] is False
    assert credential_store.get("session-disconnect") is None


def test_upload_request_rejects_missing_made_for_kids(client):
    _connect_session(client, "session-validate-1")

    response = client.post(
        "/api/jobs/some-job/youtube/upload",
        json={
            "title": "T",
            "description": "D",
            "hashtags": [],
            "privacy_status": "private",
        },
    )
    assert response.status_code == 422
    credential_store.delete("session-validate-1")


def test_upload_request_rejects_invalid_privacy_status(client):
    _connect_session(client, "session-validate-2")

    response = client.post(
        "/api/jobs/some-job/youtube/upload",
        json={
            "title": "T",
            "description": "D",
            "hashtags": [],
            "privacy_status": "public-ish",
            "made_for_kids": False,
        },
    )
    assert response.status_code == 422
    credential_store.delete("session-validate-2")


def test_upload_request_rejects_empty_title(client):
    _connect_session(client, "session-validate-3")

    response = client.post(
        "/api/jobs/some-job/youtube/upload",
        json={
            "title": "   ",
            "description": "D",
            "hashtags": [],
            "privacy_status": "private",
            "made_for_kids": False,
        },
    )
    assert response.status_code == 422
    credential_store.delete("session-validate-3")


def _valid_payload():
    return {
        "title": "My Video",
        "description": "Desc",
        "hashtags": ["#AI"],
        "privacy_status": "private",
        "made_for_kids": False,
    }


def test_create_upload_requires_youtube_connection(client):
    response = client.post("/api/jobs/some-job/youtube/upload", json=_valid_payload())
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "YOUTUBE_NOT_CONNECTED"


def test_create_upload_returns_job_not_found(client):
    _connect_session(client, "session-job-missing")

    response = client.post("/api/jobs/does-not-exist-job/youtube/upload", json=_valid_payload())
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "JOB_NOT_FOUND"

    credential_store.delete("session-job-missing")


def test_create_upload_returns_job_incomplete(client):
    _connect_session(client, "session-job-incomplete")
    job_registry.get_or_create("job-incomplete-1")

    response = client.post("/api/jobs/job-incomplete-1/youtube/upload", json=_valid_payload())
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "JOB_INCOMPLETE"

    credential_store.delete("session-job-incomplete")


def test_create_upload_returns_video_source_missing(client, monkeypatch):
    _connect_session(client, "session-video-missing")
    _complete_job("job-video-missing")
    monkeypatch.setattr(youtube_routes, "resolve_upload_video_path", lambda job_id: None)

    response = client.post("/api/jobs/job-video-missing/youtube/upload", json=_valid_payload())
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "VIDEO_SOURCE_MISSING"

    credential_store.delete("session-video-missing")


def test_create_upload_prevents_duplicate_active_upload(client, monkeypatch, tmp_path):
    _connect_session(client, "session-duplicate")
    _complete_job("job-duplicate")

    video_path = tmp_path / "job-duplicate.mp4"
    video_path.write_bytes(b"fake")
    monkeypatch.setattr(youtube_routes, "resolve_upload_video_path", lambda job_id: video_path)

    release = threading.Event()

    def _blocking_upload(upload_id, session_id, path, payload):
        release.wait(timeout=5)

    monkeypatch.setattr(youtube_routes, "run_youtube_upload", _blocking_upload)

    try:
        first = client.post("/api/jobs/job-duplicate/youtube/upload", json=_valid_payload())
        assert first.status_code == 200
        assert first.json()["status"] == "queued"

        second = client.post("/api/jobs/job-duplicate/youtube/upload", json=_valid_payload())
        assert second.status_code == 409
        assert second.json()["detail"]["code"] == "YOUTUBE_UPLOAD_IN_PROGRESS"
    finally:
        release.set()
        credential_store.delete("session-duplicate")


def test_upload_status_endpoint_is_isolated_per_session(client, monkeypatch, tmp_path):
    _connect_session(client, "session-owner")
    _complete_job("job-owner")

    video_path = tmp_path / "job-owner.mp4"
    video_path.write_bytes(b"fake")
    monkeypatch.setattr(youtube_routes, "resolve_upload_video_path", lambda job_id: video_path)

    release = threading.Event()

    def _blocking_upload(upload_id, session_id, path, payload):
        release.wait(timeout=5)

    monkeypatch.setattr(youtube_routes, "run_youtube_upload", _blocking_upload)

    try:
        created = client.post("/api/jobs/job-owner/youtube/upload", json=_valid_payload())
        upload_id = created.json()["upload_id"]

        own_status = client.get(f"/api/youtube/uploads/{upload_id}")
        assert own_status.status_code == 200

        other_client = TestClient(app)
        other_client.cookies.set("cc_session", "session-intruder")
        intruder_status = other_client.get(f"/api/youtube/uploads/{upload_id}")
        assert intruder_status.status_code == 404
        assert intruder_status.json()["detail"]["code"] == "UPLOAD_NOT_FOUND"
    finally:
        release.set()
        credential_store.delete("session-owner")
