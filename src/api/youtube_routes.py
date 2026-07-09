"""Connect with YouTube + Upload to YouTube API endpoints.

Session handling: every endpoint here reads (and, where relevant, creates)
the opaque ClipContext session cookie via src/youtube/session.py. OAuth
`state` is bound to that session id and validated on callback
(src/youtube/state_store.py). Credentials are stored server-side, keyed by
session id, and never returned to the browser
(src/youtube/token_store.py).
"""

import logging
import threading

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from googleapiclient.errors import HttpError

from src.api.jobs import registry as job_registry
from src.api.schemas import JobStatus
from src.config import (
    get_frontend_url,
    is_youtube_oauth_configured,
)
from src.pipeline.paths import resolve_upload_video_path
from src.youtube.oauth import (
    NoChannelError,
    build_authorization_url,
    credentials_to_stored,
    exchange_code,
    fetch_channel_info,
    generate_code_verifier,
    revoke_credentials,
)
from src.youtube.schemas import (
    YouTubeConnectionStatus,
    YouTubeErrorCode,
    YouTubeUploadCreated,
    YouTubeUploadRequest,
    YouTubeUploadStatus,
)
from src.youtube.session import get_session_id, new_session_id, set_session_cookie
from src.youtube.state_store import oauth_state_store
from src.youtube.token_store import credential_store
from src.youtube.upload import run_youtube_upload, upload_registry

logger = logging.getLogger(__name__)

router = APIRouter()


def _error(status_code: int, code: YouTubeErrorCode, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code.value, "message": message})


@router.get("/api/youtube/status", response_model=YouTubeConnectionStatus)
async def youtube_status(request: Request) -> YouTubeConnectionStatus:
    session_id = get_session_id(request)

    if not session_id:
        return YouTubeConnectionStatus(connected=False)

    stored = credential_store.get(session_id)

    if stored is None:
        return YouTubeConnectionStatus(connected=False)

    return YouTubeConnectionStatus(
        connected=True,
        channel_id=stored.channel_id,
        channel_title=stored.channel_title,
        channel_thumbnail_url=stored.channel_thumbnail_url,
    )


@router.get("/api/youtube/connect")
async def youtube_connect(request: Request) -> RedirectResponse:
    if not is_youtube_oauth_configured():
        raise _error(
            503,
            YouTubeErrorCode.YOUTUBE_OAUTH_NOT_CONFIGURED,
            "YouTube OAuth is not configured on this server yet.",
        )

    existing_session_id = get_session_id(request)
    session_id = existing_session_id or new_session_id()
    code_verifier = generate_code_verifier()
    state = oauth_state_store.create(session_id, code_verifier)
    authorization_url = build_authorization_url(state, code_verifier)

    logger.info(
        "YouTube OAuth connect: %s session_id=%s...%s",
        "reusing" if existing_session_id else "creating",
        session_id[:6],
        session_id[-4:],
    )

    redirect = RedirectResponse(url=authorization_url, status_code=302)
    set_session_cookie(redirect, session_id)
    return redirect


@router.get("/api/youtube/callback")
async def youtube_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    frontend_url = get_frontend_url()
    session_id = get_session_id(request)

    def redirect_with(code_value: str) -> RedirectResponse:
        return RedirectResponse(
            url=f"{frontend_url}/results?youtube=error&code={code_value}", status_code=302
        )

    if error:
        logger.info("YouTube OAuth denied or errored: %s", error)
        return redirect_with(YouTubeErrorCode.OAUTH_DENIED.value)

    if not session_id:
        logger.warning("YouTube OAuth callback had no cc_session cookie on the request.")
        return redirect_with(YouTubeErrorCode.OAUTH_STATE_INVALID.value)

    if not state:
        logger.warning("YouTube OAuth callback had no state query parameter.")
        return redirect_with(YouTubeErrorCode.OAUTH_STATE_INVALID.value)

    code_verifier = oauth_state_store.consume(state, session_id)

    if code_verifier is None:
        logger.warning(
            "YouTube OAuth state consume() rejected state for session_id=%s...%s "
            "(state unknown, expired, or bound to a different session).",
            session_id[:6],
            session_id[-4:],
        )
        return redirect_with(YouTubeErrorCode.OAUTH_STATE_INVALID.value)

    if not code:
        return redirect_with(YouTubeErrorCode.OAUTH_EXCHANGE_FAILED.value)

    try:
        credentials = exchange_code(code, code_verifier)
    except Exception:
        logger.exception("YouTube OAuth code exchange failed")
        return redirect_with(YouTubeErrorCode.OAUTH_EXCHANGE_FAILED.value)

    try:
        channel_info = fetch_channel_info(credentials)
    except NoChannelError:
        return redirect_with(YouTubeErrorCode.YOUTUBE_NO_CHANNEL.value)
    except HttpError:
        logger.exception("Failed to fetch YouTube channel info after OAuth")
        return redirect_with(YouTubeErrorCode.YOUTUBE_UPLOAD_FAILED.value)

    stored = credentials_to_stored(credentials, **channel_info)
    credential_store.save(session_id, stored)

    return RedirectResponse(url=f"{frontend_url}/results?youtube=connected", status_code=302)


@router.post("/api/youtube/disconnect", response_model=YouTubeConnectionStatus)
async def youtube_disconnect(request: Request) -> YouTubeConnectionStatus:
    session_id = get_session_id(request)

    if session_id:
        stored = credential_store.get(session_id)

        if stored is not None:
            revoke_credentials(stored)

        credential_store.delete(session_id)

    return YouTubeConnectionStatus(connected=False)


@router.post("/api/jobs/{job_id}/youtube/upload", response_model=YouTubeUploadCreated)
async def create_youtube_upload(
    job_id: str, payload: YouTubeUploadRequest, request: Request
) -> YouTubeUploadCreated:
    session_id = get_session_id(request)

    if not session_id:
        raise _error(
            401,
            YouTubeErrorCode.YOUTUBE_NOT_CONNECTED,
            "Connect your YouTube account before uploading.",
        )

    stored = credential_store.get(session_id)

    if stored is None:
        raise _error(
            401,
            YouTubeErrorCode.YOUTUBE_NOT_CONNECTED,
            "Connect your YouTube account before uploading.",
        )

    job_record = job_registry.get(job_id)

    if job_record is None:
        raise _error(404, YouTubeErrorCode.JOB_NOT_FOUND, "This ClipContext job could not be found.")

    with job_record.lock:
        job_status = job_record.status

    if job_status != JobStatus.COMPLETED:
        raise _error(
            409,
            YouTubeErrorCode.JOB_INCOMPLETE,
            "ClipContext is still processing this video.",
        )

    video_path = resolve_upload_video_path(job_id)

    if video_path is None or not video_path.exists():
        raise _error(
            404,
            YouTubeErrorCode.VIDEO_SOURCE_MISSING,
            "The original ClipContext video is no longer available.",
        )

    existing = upload_registry.find_active(session_id=session_id, job_id=job_id)

    if existing is not None:
        raise _error(
            409,
            YouTubeErrorCode.YOUTUBE_UPLOAD_IN_PROGRESS,
            "A YouTube upload for this video is already in progress.",
        )

    record = upload_registry.create(
        session_id=session_id, job_id=job_id, privacy_status=payload.privacy_status
    )

    thread = threading.Thread(
        target=run_youtube_upload,
        args=(record.upload_id, session_id, video_path, payload),
        daemon=True,
    )
    thread.start()

    return YouTubeUploadCreated(upload_id=record.upload_id, status=record.status)


@router.get("/api/youtube/uploads/{upload_id}", response_model=YouTubeUploadStatus)
async def get_youtube_upload(upload_id: str, request: Request) -> YouTubeUploadStatus:
    session_id = get_session_id(request)
    record = upload_registry.get(upload_id)

    if record is None or session_id is None or record.session_id != session_id:
        raise _error(404, YouTubeErrorCode.UPLOAD_NOT_FOUND, "Upload not found.")

    with record.lock:
        return YouTubeUploadStatus(
            upload_id=record.upload_id,
            status=record.status,
            progress=record.progress,
            message=record.message,
            video_id=record.video_id,
            video_url=record.video_url,
            title=record.title,
            code=record.code,
            error=record.error,
        )
