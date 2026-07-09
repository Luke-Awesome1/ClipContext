from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from src.youtube.constants import MAX_DESCRIPTION_LENGTH, MAX_TITLE_LENGTH


class YouTubeErrorCode(str, Enum):
    YOUTUBE_NOT_CONNECTED = "YOUTUBE_NOT_CONNECTED"
    YOUTUBE_RECONNECT_REQUIRED = "YOUTUBE_RECONNECT_REQUIRED"
    YOUTUBE_NO_CHANNEL = "YOUTUBE_NO_CHANNEL"
    YOUTUBE_QUOTA_EXCEEDED = "YOUTUBE_QUOTA_EXCEEDED"
    YOUTUBE_API_DISABLED = "YOUTUBE_API_DISABLED"
    YOUTUBE_INSUFFICIENT_SCOPE = "YOUTUBE_INSUFFICIENT_SCOPE"
    YOUTUBE_UPLOAD_FAILED = "YOUTUBE_UPLOAD_FAILED"
    YOUTUBE_UPLOAD_IN_PROGRESS = "YOUTUBE_UPLOAD_IN_PROGRESS"
    YOUTUBE_OAUTH_NOT_CONFIGURED = "YOUTUBE_OAUTH_NOT_CONFIGURED"
    OAUTH_STATE_INVALID = "OAUTH_STATE_INVALID"
    OAUTH_DENIED = "OAUTH_DENIED"
    OAUTH_EXCHANGE_FAILED = "OAUTH_EXCHANGE_FAILED"
    VIDEO_SOURCE_MISSING = "VIDEO_SOURCE_MISSING"
    JOB_NOT_FOUND = "JOB_NOT_FOUND"
    JOB_INCOMPLETE = "JOB_INCOMPLETE"
    UPLOAD_NOT_FOUND = "UPLOAD_NOT_FOUND"


class YouTubeConnectionStatus(BaseModel):
    connected: bool
    channel_id: Optional[str] = None
    channel_title: Optional[str] = None
    channel_thumbnail_url: Optional[str] = None


class YouTubeUploadRequest(BaseModel):
    title: str
    description: str = ""
    hashtags: list[str] = Field(default_factory=list)
    privacy_status: Literal["private", "unlisted", "public"]
    made_for_kids: bool

    @field_validator("title")
    @classmethod
    def _validate_title(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Title must not be empty.")

        if len(value) > MAX_TITLE_LENGTH:
            raise ValueError(f"Title must be {MAX_TITLE_LENGTH} characters or fewer.")

        return value

    @field_validator("description")
    @classmethod
    def _validate_description(cls, value: str) -> str:
        if len(value) > MAX_DESCRIPTION_LENGTH:
            raise ValueError(
                f"Description must be {MAX_DESCRIPTION_LENGTH} characters or fewer."
            )

        return value

    @field_validator("hashtags")
    @classmethod
    def _validate_hashtags(cls, value: list[str]) -> list[str]:
        return [tag for tag in value if isinstance(tag, str) and tag.strip()]


class YouTubeUploadCreated(BaseModel):
    upload_id: str
    status: str


class YouTubeUploadStatus(BaseModel):
    upload_id: str
    status: Literal["queued", "uploading", "completed", "failed"]
    progress: int
    message: Optional[str] = None
    video_id: Optional[str] = None
    video_url: Optional[str] = None
    title: Optional[str] = None
    code: Optional[str] = None
    error: Optional[str] = None
