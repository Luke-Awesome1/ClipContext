from enum import Enum
from typing import Optional

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
