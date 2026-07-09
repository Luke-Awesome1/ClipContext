import time
import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

import src.api.artifact_routes as artifact_routes
from src.api.app import app
from src.api.auth_dependencies import get_current_user
from src.api.jobs import registry as job_registry
from src.api.schemas import JobStatus
from src.artifacts.schemas import (
    ArtifactSelection,
    ArtifactSummary,
    ArtifactVideoInfo,
    SavedArtifact,
    SavedYouTubeUploadMetadata,
)
from src.firebase.auth import AuthenticatedUser
from src.models.discriminator.discriminator import DiscriminatorResult
from src.models.generated_content import GeneratedContent
from src.pipeline.schemas import PipelineResult, VideoContextSummary


def _ranked_pool() -> list[dict]:
    return [{"id": i, "rank": i, "score": 100 - i, "reason": "why"} for i in range(1, 11)]


def _make_pipeline_result(job_id: str) -> PipelineResult:
    return PipelineResult(
        job_id=job_id,
        video_context=VideoContextSummary(
            topic="Topic",
            content_type="short",
            multimodal_summary="Summary",
            core_message="Message",
        ),
        generated_content=GeneratedContent(
            titles=[{"id": i, "text": f"Title {i}"} for i in range(1, 11)],
            descriptions=[{"id": i, "text": f"Description {i}"} for i in range(1, 11)],
            hashtags=[{"id": i, "tags": [f"#tag{i}"]} for i in range(1, 11)],
        ),
        rankings=DiscriminatorResult(
            titles=_ranked_pool(), descriptions=_ranked_pool(), hashtags=_ranked_pool()
        ),
    )


def _complete_job(job_id: str) -> None:
    record, _ = job_registry.get_or_create(job_id)
    with record.lock:
        record.status = JobStatus.COMPLETED
        record.result = _make_pipeline_result(job_id)


class FakeArtifactRepository:
    """In-memory stand-in for ArtifactRepository — no real Firestore calls."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, dict]] = {}

    def upsert_by_source_job(
        self,
        uid,
        job_id,
        video_context,
        generated_content,
        rankings,
        selection,
        video_display_name,
        youtube_upload,
    ) -> SavedArtifact:
        user_store = self._store.setdefault(uid, {})
        existing_id = next(
            (aid for aid, data in user_store.items() if data["source_job_id"] == job_id),
            None,
        )
        now = datetime.now(timezone.utc)

        if existing_id:
            artifact_id = existing_id
            created_at = user_store[artifact_id]["created_at"]
        else:
            artifact_id = uuid.uuid4().hex
            created_at = now

        user_store[artifact_id] = {
            "source_job_id": job_id,
            "created_at": created_at,
            "updated_at": now,
            "video_display_name": video_display_name,
            "video_context": video_context,
            "generated_content": generated_content,
            "rankings": rankings,
            "selection": selection,
            "youtube_upload": youtube_upload,
        }

        return SavedArtifact(
            artifact_id=artifact_id,
            source_job_id=job_id,
            created_at=created_at,
            updated_at=now,
            video=ArtifactVideoInfo(display_name=video_display_name),
            video_context=video_context,
            generated_content=generated_content,
            rankings=rankings,
            selection=ArtifactSelection(**selection),
            youtube_upload=SavedYouTubeUploadMetadata(**youtube_upload),
        )

    def list_artifacts(self, uid) -> list[ArtifactSummary]:
        user_store = self._store.get(uid, {})
        items = sorted(user_store.items(), key=lambda kv: kv[1]["created_at"], reverse=True)

        summaries = []
        for artifact_id, data in items:
            titles = data["generated_content"].titles
            selected_title = next(
                (t.text for t in titles if t.id == data["selection"]["title_id"]), ""
            )
            summaries.append(
                ArtifactSummary(
                    artifact_id=artifact_id,
                    created_at=data["created_at"],
                    topic=data["video_context"].topic,
                    content_type=data["video_context"].content_type,
                    selected_title=selected_title,
                    youtube_uploaded=bool(data["youtube_upload"].get("uploaded", False)),
                )
            )
        return summaries

    def get_artifact(self, uid, artifact_id):
        data = self._store.get(uid, {}).get(artifact_id)
        if data is None:
            return None

        return SavedArtifact(
            artifact_id=artifact_id,
            source_job_id=data["source_job_id"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            video=ArtifactVideoInfo(display_name=data["video_display_name"]),
            video_context=data["video_context"],
            generated_content=data["generated_content"],
            rankings=data["rankings"],
            selection=ArtifactSelection(**data["selection"]),
            youtube_upload=SavedYouTubeUploadMetadata(**data["youtube_upload"]),
        )

    def delete_artifact(self, uid, artifact_id) -> bool:
        user_store = self._store.get(uid, {})
        if artifact_id in user_store:
            del user_store[artifact_id]
            return True
        return False


@pytest.fixture
def fake_repo(monkeypatch):
    repo = FakeArtifactRepository()
    monkeypatch.setattr(artifact_routes, "_repository", lambda: repo)
    monkeypatch.setattr(artifact_routes, "is_firebase_configured", lambda: True)
    return repo


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def _clear_dependency_overrides():
    yield
    app.dependency_overrides.pop(get_current_user, None)


def _login_as(uid: str) -> None:
    def _override():
        return AuthenticatedUser(uid=uid, email=f"{uid}@example.com", display_name="Test User", photo_url=None)

    app.dependency_overrides[get_current_user] = _override


def _valid_payload(job_id: str) -> dict:
    return {
        "job_id": job_id,
        "selected_title_id": 1,
        "selected_description_id": 2,
        "selected_hashtag_set_id": 3,
    }


def test_create_artifact_requires_auth(client, fake_repo):
    response = client.post("/api/artifacts", json=_valid_payload("job-x"))
    assert response.status_code == 401


def test_create_artifact_rejects_missing_job(client, fake_repo):
    _login_as("uid-a")
    response = client.post("/api/artifacts", json=_valid_payload("does-not-exist"))
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "JOB_NOT_FOUND"


def test_create_artifact_rejects_incomplete_job(client, fake_repo):
    job_registry.get_or_create("job-incomplete")
    _login_as("uid-a")
    response = client.post("/api/artifacts", json=_valid_payload("job-incomplete"))
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "JOB_INCOMPLETE"


def test_create_artifact_rejects_invalid_selection(client, fake_repo):
    _complete_job("job-valid-1")
    _login_as("uid-a")
    payload = _valid_payload("job-valid-1")
    payload["selected_title_id"] = 999
    response = client.post("/api/artifacts", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "INVALID_SELECTION"


def test_create_artifact_succeeds_for_completed_job(client, fake_repo):
    _complete_job("job-valid-2")
    _login_as("uid-a")
    response = client.post("/api/artifacts", json=_valid_payload("job-valid-2"))
    assert response.status_code == 200

    body = response.json()
    assert body["source_job_id"] == "job-valid-2"
    assert body["selection"] == {"title_id": 1, "description_id": 2, "hashtag_set_id": 3}
    assert len(body["generated_content"]["titles"]) == 10
    assert len(body["generated_content"]["descriptions"]) == 10
    assert len(body["generated_content"]["hashtags"]) == 10
    assert len(body["rankings"]["titles"]) == 10
    assert body["youtube_upload"]["uploaded"] is False


def test_create_artifact_is_idempotent_by_source_job(client, fake_repo):
    _complete_job("job-valid-3")
    _login_as("uid-a")

    first = client.post("/api/artifacts", json=_valid_payload("job-valid-3"))

    payload2 = _valid_payload("job-valid-3")
    payload2["selected_title_id"] = 5
    second = client.post("/api/artifacts", json=payload2)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["artifact_id"] == second.json()["artifact_id"]
    assert second.json()["selection"]["title_id"] == 5

    listing = client.get("/api/artifacts")
    assert len(listing.json()["artifacts"]) == 1


def test_artifact_list_is_newest_first(client, fake_repo):
    _complete_job("job-order-a")
    _complete_job("job-order-b")
    _login_as("uid-list")

    first = client.post("/api/artifacts", json=_valid_payload("job-order-a"))
    time.sleep(0.01)
    second = client.post("/api/artifacts", json=_valid_payload("job-order-b"))

    response = client.get("/api/artifacts")
    assert response.status_code == 200

    ids_in_order = [a["artifact_id"] for a in response.json()["artifacts"]]
    assert ids_in_order == [second.json()["artifact_id"], first.json()["artifact_id"]]


def test_user_cannot_access_another_users_artifact(client, fake_repo):
    _complete_job("job-owner-only")
    _login_as("uid-owner")
    created = client.post("/api/artifacts", json=_valid_payload("job-owner-only"))
    artifact_id = created.json()["artifact_id"]

    _login_as("uid-intruder")
    response = client.get(f"/api/artifacts/{artifact_id}")
    assert response.status_code == 404


def test_user_cannot_delete_another_users_artifact(client, fake_repo):
    _complete_job("job-owner-only-2")
    _login_as("uid-owner-2")
    created = client.post("/api/artifacts", json=_valid_payload("job-owner-only-2"))
    artifact_id = created.json()["artifact_id"]

    _login_as("uid-intruder-2")
    response = client.delete(f"/api/artifacts/{artifact_id}")
    assert response.status_code == 404

    _login_as("uid-owner-2")
    still_there = client.get(f"/api/artifacts/{artifact_id}")
    assert still_there.status_code == 200


def test_artifact_deletion_succeeds_for_owner(client, fake_repo):
    _complete_job("job-delete-me")
    _login_as("uid-deleter")
    created = client.post("/api/artifacts", json=_valid_payload("job-delete-me"))
    artifact_id = created.json()["artifact_id"]

    response = client.delete(f"/api/artifacts/{artifact_id}")
    assert response.status_code == 204

    missing = client.get(f"/api/artifacts/{artifact_id}")
    assert missing.status_code == 404


def test_firebase_not_configured_returns_structured_error(client, monkeypatch):
    monkeypatch.setattr(artifact_routes, "is_firebase_configured", lambda: False)
    _login_as("uid-a")
    response = client.get("/api/artifacts")
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "FIREBASE_NOT_CONFIGURED"


def test_youtube_status_does_not_require_firebase_auth(client, fake_repo):
    # No Authorization header at all — YouTube status must still work,
    # proving YouTube session state is not coupled to Firebase auth.
    response = client.get("/api/youtube/status")
    assert response.status_code == 200
    assert response.json()["connected"] is False


def test_artifact_create_does_not_require_youtube_session(client, fake_repo):
    _complete_job("job-no-youtube")
    _login_as("uid-no-youtube")
    # No cc_session cookie set at all — Firebase login alone is enough.
    response = client.post("/api/artifacts", json=_valid_payload("job-no-youtube"))
    assert response.status_code == 200
    assert response.json()["youtube_upload"]["uploaded"] is False
