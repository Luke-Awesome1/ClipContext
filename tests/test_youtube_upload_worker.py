from pathlib import Path

import pytest
from googleapiclient.errors import HttpError

import src.youtube.upload as upload_module
from src.youtube.oauth import YouTubeReconnectRequired
from src.youtube.schemas import YouTubeUploadRequest
from src.youtube.token_store import StoredCredentials, credential_store
from src.youtube.upload import run_youtube_upload, upload_registry


class _FakeStatus:
    def __init__(self, fraction: float):
        self._fraction = fraction

    def progress(self) -> float:
        return self._fraction


class _FakeInsertRequest:
    def __init__(self, chunks):
        self._chunks = list(chunks)

    def next_chunk(self):
        item = self._chunks.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class _FakeVideosResource:
    def __init__(self, insert_request):
        self._insert_request = insert_request

    def insert(self, part, body, media_body):
        return self._insert_request


class _FakeYouTubeClient:
    def __init__(self, insert_request):
        self._insert_request = insert_request

    def videos(self):
        return _FakeVideosResource(self._insert_request)


def _payload(**overrides) -> YouTubeUploadRequest:
    defaults = dict(
        title="My Video",
        description="Description",
        hashtags=["#AI"],
        privacy_status="private",
        made_for_kids=False,
    )
    defaults.update(overrides)
    return YouTubeUploadRequest(**defaults)


def _stored_credentials() -> StoredCredentials:
    return StoredCredentials(
        access_token="token",
        refresh_token="refresh",
        token_uri="https://oauth2.googleapis.com/token",
        scopes=["https://www.googleapis.com/auth/youtube.upload"],
        expiry=None,
    )


@pytest.fixture(autouse=True)
def _fast_sleep(monkeypatch):
    monkeypatch.setattr(upload_module.time, "sleep", lambda _seconds: None)


@pytest.fixture(autouse=True)
def _no_real_media(monkeypatch):
    monkeypatch.setattr(upload_module, "MediaFileUpload", lambda *a, **k: object())


def test_successful_upload_sets_completed_status_and_video_url(monkeypatch):
    session_id = "session-success"
    credential_store.save(session_id, _stored_credentials())

    chunks = [
        (_FakeStatus(0.5), None),
        (None, {"id": "vid123"}),
    ]
    monkeypatch.setattr(
        upload_module, "ensure_valid_credentials", lambda stored: (object(), False)
    )
    monkeypatch.setattr(
        upload_module,
        "build_youtube_client",
        lambda credentials: _FakeYouTubeClient(_FakeInsertRequest(chunks)),
    )

    record = upload_registry.create(session_id=session_id, job_id="job-1")
    run_youtube_upload(record.upload_id, session_id, Path("/tmp/fake.mp4"), _payload())

    final = upload_registry.get(record.upload_id)
    assert final.status == "completed"
    assert final.progress == 100
    assert final.video_id == "vid123"
    assert final.video_url == "https://www.youtube.com/watch?v=vid123"
    assert final.title == "My Video"

    credential_store.delete(session_id)


def test_retryable_server_error_is_retried_then_succeeds(monkeypatch):
    session_id = "session-retry"
    credential_store.save(session_id, _stored_credentials())

    class _FakeResp:
        status = 503
        reason = "Service Unavailable"

    chunks = [
        HttpError(resp=_FakeResp(), content=b"{}"),
        (None, {"id": "vid456"}),
    ]
    monkeypatch.setattr(
        upload_module, "ensure_valid_credentials", lambda stored: (object(), False)
    )
    monkeypatch.setattr(
        upload_module,
        "build_youtube_client",
        lambda credentials: _FakeYouTubeClient(_FakeInsertRequest(chunks)),
    )

    record = upload_registry.create(session_id=session_id, job_id="job-2")
    run_youtube_upload(record.upload_id, session_id, Path("/tmp/fake.mp4"), _payload())

    final = upload_registry.get(record.upload_id)
    assert final.status == "completed"
    assert final.video_id == "vid456"

    credential_store.delete(session_id)


def test_reconnect_required_marks_upload_failed_and_clears_credentials(monkeypatch):
    session_id = "session-reconnect"
    credential_store.save(session_id, _stored_credentials())

    def _raise_reconnect(stored):
        raise YouTubeReconnectRequired("expired")

    monkeypatch.setattr(upload_module, "ensure_valid_credentials", _raise_reconnect)

    record = upload_registry.create(session_id=session_id, job_id="job-3")
    run_youtube_upload(record.upload_id, session_id, Path("/tmp/fake.mp4"), _payload())

    final = upload_registry.get(record.upload_id)
    assert final.status == "failed"
    assert final.code == "YOUTUBE_RECONNECT_REQUIRED"
    assert credential_store.get(session_id) is None


def test_missing_credentials_marks_upload_not_connected():
    session_id = "session-missing"
    record = upload_registry.create(session_id=session_id, job_id="job-4")

    run_youtube_upload(record.upload_id, session_id, Path("/tmp/fake.mp4"), _payload())

    final = upload_registry.get(record.upload_id)
    assert final.status == "failed"
    assert final.code == "YOUTUBE_NOT_CONNECTED"


def test_quota_exceeded_http_error_maps_to_quota_exceeded_code(monkeypatch):
    session_id = "session-quota"
    credential_store.save(session_id, _stored_credentials())

    class _FakeResp:
        status = 403
        reason = "Forbidden"

    content = b'{"error": {"errors": [{"reason": "quotaExceeded"}]}}'
    chunks = [HttpError(resp=_FakeResp(), content=content)]

    monkeypatch.setattr(
        upload_module, "ensure_valid_credentials", lambda stored: (object(), False)
    )
    monkeypatch.setattr(
        upload_module,
        "build_youtube_client",
        lambda credentials: _FakeYouTubeClient(_FakeInsertRequest(chunks)),
    )

    record = upload_registry.create(session_id=session_id, job_id="job-5")
    run_youtube_upload(record.upload_id, session_id, Path("/tmp/fake.mp4"), _payload())

    final = upload_registry.get(record.upload_id)
    assert final.status == "failed"
    assert final.code == "YOUTUBE_QUOTA_EXCEEDED"

    credential_store.delete(session_id)


def test_upload_registry_find_active_only_matches_queued_or_uploading():
    session_id = "session-active"
    record = upload_registry.create(session_id=session_id, job_id="job-6")

    assert upload_registry.find_active(session_id, "job-6") is not None

    upload_registry.set_completed(record.upload_id, "vid", "url", "title")

    assert upload_registry.find_active(session_id, "job-6") is None
