from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from src.models.discriminator.discriminator import DiscriminatorResult
from src.models.generated_content import GeneratedContent
from src.pipeline.schemas import VideoContextSummary


class ArtifactCreateRequest(BaseModel):
    job_id: str
    selected_title_id: int
    selected_description_id: int
    selected_hashtag_set_id: int
    # Cosmetic only (e.g. "my-video.mp4") — never treated as canonical
    # pipeline output. The canonical artifact content always comes from the
    # server-side job result, never from the request body.
    video_display_name: Optional[str] = None


class ArtifactSelection(BaseModel):
    title_id: int
    description_id: int
    hashtag_set_id: int


class ArtifactVideoInfo(BaseModel):
    original_filename: Optional[str] = None
    display_name: Optional[str] = None


class SavedYouTubeUploadMetadata(BaseModel):
    uploaded: bool = False
    video_id: Optional[str] = None
    video_url: Optional[str] = None
    privacy_status: Optional[str] = None
    channel_id: Optional[str] = None
    channel_title: Optional[str] = None
    uploaded_at: Optional[datetime] = None


class SavedArtifact(BaseModel):
    artifact_id: str
    source_job_id: str
    created_at: datetime
    updated_at: datetime
    video: ArtifactVideoInfo
    video_context: VideoContextSummary
    generated_content: GeneratedContent
    rankings: DiscriminatorResult
    selection: ArtifactSelection
    youtube_upload: SavedYouTubeUploadMetadata


class ArtifactSummary(BaseModel):
    artifact_id: str
    created_at: datetime
    topic: str
    content_type: str
    selected_title: str
    youtube_uploaded: bool


class ArtifactListResponse(BaseModel):
    artifacts: list[ArtifactSummary]
