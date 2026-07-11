from enum import Enum
from typing import Optional

from pydantic import BaseModel

from src.models.discriminator.discriminator import DiscriminatorResult
from src.models.generated_content import GeneratedContent


class PipelineStage(str, Enum):
    QUEUED = "queued"
    VALIDATING = "validating"
    EXTRACTING_AUDIO = "extracting_audio"
    EXTRACTING_FRAMES = "extracting_frames"
    TRANSCRIBING = "transcribing"
    TEMPORAL_ALIGNMENT = "temporal_alignment"
    VISUAL_ANALYSIS = "visual_analysis"
    CONTEXT_GENERATION = "context_generation"
    WORLDWIDE_TRENDS = "worldwide_trends"
    CREATOR_TRENDS = "creator_trends"
    CONTENT_GENERATION = "content_generation"
    RANKING = "ranking"
    COMPLETED = "completed"


STAGE_PROGRESS = {
    PipelineStage.QUEUED: 0,
    PipelineStage.VALIDATING: 5,
    PipelineStage.EXTRACTING_AUDIO: 12,
    PipelineStage.EXTRACTING_FRAMES: 20,
    PipelineStage.TRANSCRIBING: 32,
    PipelineStage.TEMPORAL_ALIGNMENT: 40,
    PipelineStage.VISUAL_ANALYSIS: 55,
    PipelineStage.CONTEXT_GENERATION: 68,
    PipelineStage.WORLDWIDE_TRENDS: 78,
    PipelineStage.CREATOR_TRENDS: 86,
    PipelineStage.CONTENT_GENERATION: 93,
    PipelineStage.RANKING: 98,
    PipelineStage.COMPLETED: 100,
}


class VideoContextSummary(BaseModel):
    topic: str
    content_type: str
    multimodal_summary: str
    core_message: str


class StageAiAudit(BaseModel):
    """Truthful execution record for one AI inference stage.

    provider_used may differ from provider_requested when the requested
    provider (e.g. amd_vllm) was unreachable or returned unusable output and
    the pipeline fell back to another configured provider — see
    src/ai/providers/orchestrator.py. The frontend must only show an "AMD
    inference" indicator when provider_used == "amd_vllm".
    """

    stage: str
    provider_requested: str
    provider_used: Optional[str] = None
    model: Optional[str] = None
    hardware: Optional[str] = None
    latency_ms: Optional[float] = None
    fallback_used: bool = False
    fallback_reason: Optional[str] = None


class PipelineResult(BaseModel):
    job_id: str
    video_context: VideoContextSummary
    generated_content: GeneratedContent
    rankings: DiscriminatorResult
    ai_audit: list[StageAiAudit] = []
