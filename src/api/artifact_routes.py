"""Saved ClipContext artifact API — requires a ClipContext (Firebase) login.

Distinct from the YouTube OAuth session (src/api/youtube_routes.py): a
request here is identified by a verified Firebase ID token, never by the
`cc_session` cookie used for YouTube authorization. The two may or may not
both be present on the same request; neither implies the other.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request

from src.api.auth_dependencies import get_current_user
from src.api.jobs import registry as job_registry
from src.api.schemas import JobStatus
from src.artifacts.repository import ArtifactRepository, ArtifactRepositoryError
from src.artifacts.schemas import (
    ArtifactCreateRequest,
    ArtifactListResponse,
    SavedArtifact,
)
from src.firebase.admin import get_firestore_client, is_firebase_configured
from src.firebase.auth import AuthenticatedUser
from src.youtube.session import get_session_id
from src.youtube.upload import upload_registry

logger = logging.getLogger(__name__)

router = APIRouter()


def _require_firebase() -> None:
    if not is_firebase_configured():
        raise HTTPException(
            status_code=503,
            detail={
                "code": "FIREBASE_NOT_CONFIGURED",
                "message": "Cloud save is not configured on this server yet.",
            },
        )


def _repository() -> ArtifactRepository:
    return ArtifactRepository(get_firestore_client())


def _safe_youtube_metadata(request: Request, job_id: str) -> dict:
    """Best-effort, safe (no tokens) YouTube upload metadata for this job.

    Looked up via the YouTube session cookie, entirely independent of the
    Firebase-authenticated user — a ClipContext account and a YouTube
    connection are not the same identity (see module docstring).
    """
    session_id = get_session_id(request)

    if not session_id:
        return {"uploaded": False}

    record = upload_registry.find_by_job(session_id, job_id)

    if record is None or record.status != "completed":
        return {"uploaded": False}

    return {
        "uploaded": True,
        "video_id": record.video_id,
        "video_url": record.video_url,
        "privacy_status": record.privacy_status,
        "channel_id": record.channel_id,
        "channel_title": record.channel_title,
        "uploaded_at": datetime.now(timezone.utc),
    }


@router.post("/api/artifacts", response_model=SavedArtifact)
async def create_artifact(
    payload: ArtifactCreateRequest,
    request: Request,
    user: AuthenticatedUser = Depends(get_current_user),
) -> SavedArtifact:
    _require_firebase()

    job_record = job_registry.get(payload.job_id)

    if job_record is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "JOB_NOT_FOUND", "message": "This ClipContext job could not be found."},
        )

    with job_record.lock:
        status = job_record.status
        result = job_record.result

    if status != JobStatus.COMPLETED or result is None:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "JOB_INCOMPLETE",
                "message": (
                    "ClipContext is still processing this video, or its result is "
                    "no longer available on this server (e.g. after a restart)."
                ),
            },
        )

    title_ids = {candidate.id for candidate in result.generated_content.titles}
    description_ids = {candidate.id for candidate in result.generated_content.descriptions}
    hashtag_ids = {candidate.id for candidate in result.generated_content.hashtags}

    if payload.selected_title_id not in title_ids:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_SELECTION", "message": "Invalid title selection."},
        )

    if payload.selected_description_id not in description_ids:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_SELECTION", "message": "Invalid description selection."},
        )

    if payload.selected_hashtag_set_id not in hashtag_ids:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_SELECTION", "message": "Invalid hashtag selection."},
        )

    youtube_upload = _safe_youtube_metadata(request, payload.job_id)

    try:
        artifact = _repository().upsert_by_source_job(
            uid=user.uid,
            job_id=payload.job_id,
            video_context=result.video_context,
            generated_content=result.generated_content,
            rankings=result.rankings,
            selection={
                "title_id": payload.selected_title_id,
                "description_id": payload.selected_description_id,
                "hashtag_set_id": payload.selected_hashtag_set_id,
            },
            video_display_name=payload.video_display_name,
            youtube_upload=youtube_upload,
        )
    except ArtifactRepositoryError:
        logger.exception(
            "Failed to save artifact for uid=%s job_id=%s", user.uid, payload.job_id
        )
        raise HTTPException(
            status_code=502,
            detail={
                "code": "ARTIFACT_SAVE_FAILED",
                "message": "Could not save this artifact right now. Please try again.",
            },
        )

    return artifact


@router.get("/api/artifacts", response_model=ArtifactListResponse)
async def list_artifacts(
    user: AuthenticatedUser = Depends(get_current_user),
) -> ArtifactListResponse:
    _require_firebase()

    try:
        artifacts = _repository().list_artifacts(user.uid)
    except ArtifactRepositoryError:
        logger.exception("Failed to list artifacts for uid=%s", user.uid)
        raise HTTPException(
            status_code=502,
            detail={
                "code": "ARTIFACT_LIST_FAILED",
                "message": "Could not load your artifacts right now.",
            },
        )

    return ArtifactListResponse(artifacts=artifacts)


@router.get("/api/artifacts/{artifact_id}", response_model=SavedArtifact)
async def get_artifact(
    artifact_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
) -> SavedArtifact:
    _require_firebase()

    try:
        artifact = _repository().get_artifact(user.uid, artifact_id)
    except ArtifactRepositoryError:
        logger.exception(
            "Failed to load artifact for uid=%s artifact_id=%s", user.uid, artifact_id
        )
        raise HTTPException(
            status_code=502,
            detail={
                "code": "ARTIFACT_LOAD_FAILED",
                "message": "Could not load this artifact right now.",
            },
        )

    if artifact is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "ARTIFACT_NOT_FOUND", "message": "Artifact not found."},
        )

    return artifact


@router.delete("/api/artifacts/{artifact_id}", status_code=204)
async def delete_artifact(
    artifact_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
) -> None:
    _require_firebase()

    try:
        deleted = _repository().delete_artifact(user.uid, artifact_id)
    except ArtifactRepositoryError:
        logger.exception(
            "Failed to delete artifact for uid=%s artifact_id=%s", user.uid, artifact_id
        )
        raise HTTPException(
            status_code=502,
            detail={
                "code": "ARTIFACT_DELETE_FAILED",
                "message": "Could not delete this artifact right now.",
            },
        )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail={"code": "ARTIFACT_NOT_FOUND", "message": "Artifact not found."},
        )
