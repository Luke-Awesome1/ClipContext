import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, UploadFile

from src.ai.providers.health import get_ai_provider_status
from src.api.jobs import registry, start_job
from src.api.schemas import (
    HealthResponse,
    JobCreateResponse,
    JobStatusResponse,
    ProviderStatusResponse,
)
from src.config import get_max_upload_size_bytes
from src.pipeline.paths import (
    ALLOWED_VIDEO_EXTENSIONS,
    UPLOADS_DIR,
    compute_job_id,
    hash_file,
    normalize_creator_handle,
    safe_upload_filename,
)
from src.pipeline.runner import SUPPORTED_PLATFORMS


logger = logging.getLogger(__name__)

router = APIRouter()

UPLOAD_CHUNK_SIZE = 1024 * 1024


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/api/providers/status", response_model=ProviderStatusResponse)
async def provider_status() -> ProviderStatusResponse:
    """Which AI provider (fireworks / amd_vllm) is configured for each
    stage, and whether it's currently reachable. Checking AMD vLLM
    reachability makes a live request to the configured endpoint, so this
    is kept separate from GET /health rather than slowing down liveness
    checks.
    """
    return ProviderStatusResponse(**get_ai_provider_status())


@router.post("/api/jobs", response_model=JobCreateResponse)
async def create_job(
    video: UploadFile,
    creator_handle: str = Form(""),
    platform: str = Form("youtube"),
) -> JobCreateResponse:
    if platform not in SUPPORTED_PLATFORMS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported platform. Use one of: {', '.join(SUPPORTED_PLATFORMS)}",
        )

    # Creator handle is optional: when omitted, the pipeline skips
    # creator-specific trend analysis and falls back to worldwide syntax.
    normalized_handle = normalize_creator_handle(creator_handle)

    original_name = video.filename or ""
    extension = Path(original_name).suffix.lower()

    if extension not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported video format. Accepted formats: "
                + ", ".join(sorted(ALLOWED_VIDEO_EXTENSIONS))
            ),
        )

    max_size = get_max_upload_size_bytes()

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    staging_path = UPLOADS_DIR / f"staging-{uuid.uuid4().hex}{extension}"

    total_bytes = 0

    try:
        with staging_path.open("wb") as staging_file:
            while True:
                chunk = await video.read(UPLOAD_CHUNK_SIZE)

                if not chunk:
                    break

                total_bytes += len(chunk)

                if total_bytes > max_size:
                    raise HTTPException(
                        status_code=413,
                        detail=(
                            "Video exceeds the maximum upload size of "
                            f"{max_size // (1024 * 1024)}MB."
                        ),
                    )

                staging_file.write(chunk)

        if total_bytes == 0:
            raise HTTPException(status_code=400, detail="No video file was received.")

    except HTTPException:
        staging_path.unlink(missing_ok=True)
        raise

    except Exception:
        staging_path.unlink(missing_ok=True)
        logger.exception("Failed to store uploaded video")
        raise HTTPException(status_code=500, detail="Failed to store uploaded video.")

    finally:
        await video.close()

    try:
        video_hash = hash_file(staging_path)
        job_id = compute_job_id(video_hash, normalized_handle, platform)
        final_path = UPLOADS_DIR / safe_upload_filename(job_id, original_name)

        if staging_path != final_path:
            staging_path.replace(final_path)

        status = start_job(
            job_id=job_id,
            video_path=final_path,
            creator_handle=normalized_handle,
            platform=platform,
        )
    except Exception:
        staging_path.unlink(missing_ok=True)
        logger.exception("Failed to start pipeline job")
        raise HTTPException(status_code=500, detail="Failed to start processing job.")

    return JobCreateResponse(job_id=job_id, status=status)


@router.get("/api/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job(job_id: str) -> JobStatusResponse:
    record = registry.get(job_id)

    if record is None:
        raise HTTPException(status_code=404, detail="Job not found.")

    with record.lock:
        return JobStatusResponse(
            job_id=record.job_id,
            status=record.status,
            stage=record.stage,
            progress=record.progress,
            message=record.message,
            result=record.result,
            error=record.error,
        )
