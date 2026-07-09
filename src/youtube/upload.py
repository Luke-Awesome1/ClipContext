"""Thread-safe YouTube upload registry + resumable upload worker.

Mirrors the pattern in src/api/jobs.py (JobRegistry): an in-memory,
lock-guarded dict of records, with a background daemon thread doing the
actual work and reporting progress back into the record. Same documented
hackathon-scope limitation: an upload's tracking record is lost on backend
restart, but nothing here duplicates that registry — it is a distinct
concept (a YouTube upload job, not a ClipContext pipeline job).
"""

import json
import logging
import random
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from src.youtube.constants import (
    MAX_UPLOAD_RETRIES,
    RETRIABLE_HTTP_STATUS_CODES,
    UPLOAD_CHUNK_SIZE,
)
from src.youtube.metadata import build_upload_body
from src.youtube.oauth import (
    NoChannelError,
    YouTubeReconnectRequired,
    build_youtube_client,
    ensure_valid_credentials,
)
from src.youtube.schemas import YouTubeErrorCode, YouTubeUploadRequest
from src.youtube.token_store import credential_store

logger = logging.getLogger(__name__)

_ACTIVE_STATUSES = ("queued", "uploading")


@dataclass
class UploadRecord:
    upload_id: str
    session_id: str
    job_id: str
    status: str = "queued"
    progress: int = 0
    message: str = "Upload queued"
    video_id: Optional[str] = None
    video_url: Optional[str] = None
    title: Optional[str] = None
    code: Optional[str] = None
    error: Optional[str] = None
    # Snapshotted at creation/completion so a saved artifact can safely
    # describe a past upload even after the user disconnects YouTube or the
    # session ends — see src/artifacts/repository.py.
    privacy_status: Optional[str] = None
    channel_id: Optional[str] = None
    channel_title: Optional[str] = None
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False)


class YouTubeUploadRegistry:
    def __init__(self) -> None:
        self._uploads: dict[str, UploadRecord] = {}
        self._registry_lock = threading.Lock()

    def create(
        self,
        session_id: str,
        job_id: str,
        privacy_status: Optional[str] = None,
    ) -> UploadRecord:
        upload_id = uuid.uuid4().hex
        record = UploadRecord(
            upload_id=upload_id,
            session_id=session_id,
            job_id=job_id,
            privacy_status=privacy_status,
        )

        with self._registry_lock:
            self._uploads[upload_id] = record

        return record

    def find_active(self, session_id: str, job_id: str) -> Optional[UploadRecord]:
        with self._registry_lock:
            for record in self._uploads.values():
                if (
                    record.session_id == session_id
                    and record.job_id == job_id
                    and record.status in _ACTIVE_STATUSES
                ):
                    return record

        return None

    def find_by_job(self, session_id: str, job_id: str) -> Optional[UploadRecord]:
        """Most recent record (any status) for this session+job, if any.

        Used to embed safe YouTube upload metadata into a saved artifact —
        distinct from find_active, which only cares about in-progress
        uploads for duplicate-prevention.
        """
        with self._registry_lock:
            candidates = [
                record
                for record in self._uploads.values()
                if record.session_id == session_id and record.job_id == job_id
            ]

        return candidates[-1] if candidates else None

    def get(self, upload_id: str) -> Optional[UploadRecord]:
        with self._registry_lock:
            return self._uploads.get(upload_id)

    def update_progress(self, upload_id: str, progress: int, message: str) -> None:
        record = self.get(upload_id)

        if record is None:
            return

        with record.lock:
            record.status = "uploading"
            record.progress = progress
            record.message = message

    def set_completed(
        self,
        upload_id: str,
        video_id: str,
        video_url: str,
        title: str,
        channel_id: Optional[str] = None,
        channel_title: Optional[str] = None,
    ) -> None:
        record = self.get(upload_id)

        if record is None:
            return

        with record.lock:
            record.status = "completed"
            record.progress = 100
            record.message = "Uploaded to YouTube"
            record.video_id = video_id
            record.video_url = video_url
            record.title = title
            record.error = None
            record.code = None
            if channel_id is not None:
                record.channel_id = channel_id
            if channel_title is not None:
                record.channel_title = channel_title

    def set_error(self, upload_id: str, code: YouTubeErrorCode, message: str) -> None:
        record = self.get(upload_id)

        if record is None:
            return

        with record.lock:
            record.status = "failed"
            record.message = "Upload failed"
            record.code = code.value
            record.error = message


upload_registry = YouTubeUploadRegistry()


def _classify_http_error(exc: HttpError) -> tuple[YouTubeErrorCode, str]:
    status = exc.resp.status if exc.resp is not None else 0
    reason = ""

    try:
        content = exc.content
        payload = json.loads(content.decode("utf-8") if isinstance(content, bytes) else content)
        errors = payload.get("error", {}).get("errors", [])
        if errors:
            reason = str(errors[0].get("reason", ""))
    except Exception:
        reason = ""

    if status == 403 and "quota" in reason.lower():
        return (
            YouTubeErrorCode.YOUTUBE_QUOTA_EXCEEDED,
            "The YouTube API quota is currently exhausted. Try again later.",
        )

    if status == 403 and "accessnotconfigured" in reason.lower():
        return (
            YouTubeErrorCode.YOUTUBE_API_DISABLED,
            "YouTube Data API v3 is not enabled for this project.",
        )

    if status in (401, 403):
        return (
            YouTubeErrorCode.YOUTUBE_INSUFFICIENT_SCOPE,
            "ClipContext is not authorized to upload to this YouTube account. "
            "Please reconnect.",
        )

    return (
        YouTubeErrorCode.YOUTUBE_UPLOAD_FAILED,
        "The upload to YouTube failed. Please try again.",
    )


def run_youtube_upload(
    upload_id: str,
    session_id: str,
    video_path: Path,
    payload: YouTubeUploadRequest,
) -> None:
    stored = credential_store.get(session_id)

    if stored is None:
        upload_registry.set_error(
            upload_id,
            YouTubeErrorCode.YOUTUBE_NOT_CONNECTED,
            "Your YouTube connection was lost. Please reconnect.",
        )
        return

    try:
        credentials, refreshed = ensure_valid_credentials(stored)
    except YouTubeReconnectRequired:
        credential_store.delete(session_id)
        upload_registry.set_error(
            upload_id,
            YouTubeErrorCode.YOUTUBE_RECONNECT_REQUIRED,
            "Your YouTube connection has expired. Please reconnect your account.",
        )
        return

    if refreshed:
        credential_store.update_tokens(
            session_id,
            access_token=credentials.token,
            expiry=credentials.expiry.isoformat() if credentials.expiry else None,
        )

    upload_registry.update_progress(upload_id, 0, "Starting upload")

    body = build_upload_body(
        title=payload.title,
        description=payload.description,
        hashtags=payload.hashtags,
        privacy_status=payload.privacy_status,
        made_for_kids=payload.made_for_kids,
    )

    try:
        youtube = build_youtube_client(credentials)
        media = MediaFileUpload(
            str(video_path),
            chunksize=UPLOAD_CHUNK_SIZE,
            resumable=True,
            mimetype="video/mp4",
        )
        insert_request = youtube.videos().insert(
            part="snippet,status", body=body, media_body=media
        )

        response = None
        retry_count = 0

        while response is None:
            try:
                status_obj, response = insert_request.next_chunk()

                if status_obj is not None:
                    progress = int(status_obj.progress() * 100)
                    upload_registry.update_progress(
                        upload_id, progress, "Uploading video to YouTube"
                    )
            except HttpError as exc:
                status = exc.resp.status if exc.resp is not None else 0

                if status in RETRIABLE_HTTP_STATUS_CODES and retry_count < MAX_UPLOAD_RETRIES:
                    retry_count += 1
                    backoff = min(2**retry_count, 32) + random.uniform(0, 1)
                    logger.warning(
                        "Retryable YouTube upload error (status=%s) for upload_id=%s, "
                        "retry %d/%d in %.1fs",
                        status,
                        upload_id,
                        retry_count,
                        MAX_UPLOAD_RETRIES,
                        backoff,
                    )
                    time.sleep(backoff)
                    continue

                raise

        video_id = response.get("id") if response else None

        if not video_id:
            raise RuntimeError("YouTube did not return a video id.")

        upload_registry.set_completed(
            upload_id,
            video_id=video_id,
            video_url=f"https://www.youtube.com/watch?v={video_id}",
            title=payload.title,
            channel_id=stored.channel_id,
            channel_title=stored.channel_title,
        )

    except HttpError as exc:
        code, message = _classify_http_error(exc)
        logger.warning("YouTube upload failed for upload_id=%s: %s", upload_id, exc)
        upload_registry.set_error(upload_id, code, message)

    except NoChannelError:
        upload_registry.set_error(
            upload_id,
            YouTubeErrorCode.YOUTUBE_NO_CHANNEL,
            "No YouTube channel is available for this Google account.",
        )

    except Exception:
        logger.exception("Unexpected error during YouTube upload upload_id=%s", upload_id)
        upload_registry.set_error(
            upload_id,
            YouTubeErrorCode.YOUTUBE_UPLOAD_FAILED,
            "The upload to YouTube failed. Please try again.",
        )
