from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel

from src.pipeline.schemas import PipelineResult, PipelineStage


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobCreateResponse(BaseModel):
    job_id: str
    status: JobStatus


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    stage: PipelineStage
    progress: int
    message: str
    result: Optional[PipelineResult] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str


class ProviderStatusResponse(BaseModel):
    """Safe-to-expose AI provider configuration/reachability, keyed by
    pipeline stage and by provider name. Never includes API keys, tokens,
    or the AMD endpoint URL — see src/ai/providers/health.py.
    """

    stages: dict[str, Any]
    providers: dict[str, Any]
