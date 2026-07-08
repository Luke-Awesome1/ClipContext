"""In-memory, thread-safe job registry and background pipeline execution.

Limitation (documented, acceptable for hackathon scope): job state lives in
process memory only and is lost on backend restart. Final pipeline artifacts
are still persisted to disk under outputs/<job_id>/, so a restart loses only
the *tracking* of in-flight jobs, not completed results on disk.
"""

import logging
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from src.api.schemas import JobStatus
from src.pipeline.runner import PipelineError, run_pipeline
from src.pipeline.schemas import PipelineResult, PipelineStage


logger = logging.getLogger(__name__)


@dataclass
class JobRecord:
    job_id: str
    status: JobStatus = JobStatus.QUEUED
    stage: PipelineStage = PipelineStage.QUEUED
    progress: int = 0
    message: str = "Job queued"
    result: Optional[PipelineResult] = None
    error: Optional[str] = None
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False)


class JobRegistry:
    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}
        self._registry_lock = threading.Lock()

    def get(self, job_id: str) -> Optional[JobRecord]:
        with self._registry_lock:
            return self._jobs.get(job_id)

    def get_or_create(self, job_id: str) -> tuple[JobRecord, bool]:
        with self._registry_lock:
            existing = self._jobs.get(job_id)

            if existing is not None:
                return existing, False

            record = JobRecord(job_id=job_id)
            self._jobs[job_id] = record
            return record, True

    def update_progress(
        self,
        job_id: str,
        stage: PipelineStage,
        progress: int,
        message: str,
    ) -> None:
        record = self.get(job_id)

        if record is None:
            return

        with record.lock:
            record.status = JobStatus.PROCESSING
            record.stage = stage
            record.progress = progress
            record.message = message

    def set_result(self, job_id: str, result: PipelineResult) -> None:
        record = self.get(job_id)

        if record is None:
            return

        with record.lock:
            record.status = JobStatus.COMPLETED
            record.stage = PipelineStage.COMPLETED
            record.progress = 100
            record.message = "Pipeline complete"
            record.result = result
            record.error = None

    def set_error(self, job_id: str, error_message: str) -> None:
        record = self.get(job_id)

        if record is None:
            return

        with record.lock:
            record.status = JobStatus.FAILED
            record.error = error_message
            record.message = "Job failed"


registry = JobRegistry()


def _run_job(job_id: str, video_path: Path, creator_handle: str, platform: str) -> None:
    def progress_callback(stage: PipelineStage, progress: int, message: str) -> None:
        registry.update_progress(job_id, stage, progress, message)

    try:
        result = run_pipeline(
            video_path=video_path,
            creator_handle=creator_handle,
            platform=platform,
            progress_callback=progress_callback,
        )
        registry.set_result(job_id, result)

    except PipelineError as error:
        logger.warning("Pipeline failed for job_id=%s: %s", job_id, error)
        registry.set_error(job_id, str(error))

    except Exception:
        logger.exception("Unhandled pipeline error for job_id=%s", job_id)
        registry.set_error(
            job_id,
            "An internal error occurred while processing this video. "
            "Please try again.",
        )


def start_job(
    job_id: str,
    video_path: Path,
    creator_handle: str,
    platform: str,
) -> JobStatus:
    record, created = registry.get_or_create(job_id)

    if not created:
        return record.status

    thread = threading.Thread(
        target=_run_job,
        args=(job_id, video_path, creator_handle, platform),
        daemon=True,
    )
    thread.start()

    return record.status
