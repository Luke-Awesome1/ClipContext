import io

import pytest
from fastapi.testclient import TestClient

from src.api.app import app
from src.api.schemas import JobStatus
import src.api.routes as routes_module


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_provider_status_endpoint_defaults_to_fireworks_only(client):
    response = client.get("/api/providers/status")
    assert response.status_code == 200
    body = response.json()
    assert body["stages"]["content_generation"]["provider_requested"] == "fireworks"
    assert body["stages"]["discriminator"]["provider_requested"] == "fireworks"
    # No stage is configured for AMD by default, so it must not appear —
    # this also guarantees no live network call to an unconfigured AMD
    # endpoint happens on a routine status check.
    assert "amd_vllm" not in body["providers"]
    assert body["providers"]["fireworks"]["configured"] is True


def test_create_job_rejects_unsupported_extension(client):
    response = client.post(
        "/api/jobs",
        files={"video": ("clip.exe", io.BytesIO(b"not a video"), "application/octet-stream")},
        data={"creator_handle": "someone", "platform": "youtube"},
    )
    assert response.status_code == 400
    assert "format" in response.json()["detail"].lower()


def test_create_job_rejects_unsupported_platform(client):
    response = client.post(
        "/api/jobs",
        files={"video": ("clip.mp4", io.BytesIO(b"fake bytes"), "video/mp4")},
        data={"creator_handle": "someone", "platform": "tiktok"},
    )
    assert response.status_code == 400
    assert "platform" in response.json()["detail"].lower()


def test_create_job_allows_empty_creator_handle(client, monkeypatch):
    monkeypatch.setattr(
        routes_module, "start_job", lambda **kwargs: JobStatus.QUEUED
    )

    response = client.post(
        "/api/jobs",
        files={"video": ("clip.mp4", io.BytesIO(b"fake bytes"), "video/mp4")},
        data={"platform": "youtube"},
    )

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["job_id"], str) and body["job_id"]
    assert body["status"] == "queued"


def test_create_job_success_calls_start_job(client, monkeypatch):
    captured = {}

    def fake_start_job(job_id, video_path, creator_handle, platform):
        captured["job_id"] = job_id
        captured["creator_handle"] = creator_handle
        captured["platform"] = platform
        return JobStatus.QUEUED

    monkeypatch.setattr(routes_module, "start_job", fake_start_job)

    response = client.post(
        "/api/jobs",
        files={"video": ("clip.mp4", io.BytesIO(b"fake video bytes"), "video/mp4")},
        data={"creator_handle": "@SomeCreator", "platform": "youtube"},
    )

    assert response.status_code == 200
    assert captured["creator_handle"] == "somecreator"
    assert captured["platform"] == "youtube"


def test_get_job_returns_404_for_unknown_job(client):
    response = client.get("/api/jobs/does-not-exist")
    assert response.status_code == 404


def test_get_job_returns_current_status(client, monkeypatch):
    from src.api.jobs import registry
    from src.pipeline.schemas import PipelineStage

    registry.get_or_create("known-job")
    registry.update_progress(
        "known-job",
        stage=PipelineStage.TRANSCRIBING,
        progress=32,
        message="Transcribing audio",
    )

    response = client.get("/api/jobs/known-job")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "processing"
    assert body["stage"] == "transcribing"
    assert body["progress"] == 32
