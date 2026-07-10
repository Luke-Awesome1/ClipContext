"""Reusable ClipContext pipeline service.

Both the CLI (main.py) and the API job worker (src/api/jobs.py) call
run_pipeline() so there is exactly one implementation of the business
pipeline.
"""

import logging
from pathlib import Path
from typing import Callable, Optional

from src.ai.content_generator import (
    generate_content,
    save_generated_content,
)
from src.ai.context_builder import build_video_context
from src.ai.fireworks.multimodal import analyse_visual_window
from src.ai.temporal_alignment import build_temporal_windows
from src.ai.transcriber import transcribe_audio
from src.models.discriminator.discriminator import run_discriminator
from src.models.video_context import VideoContext
from src.models.visual_window import VisualWindowAnalysis
from src.pipeline.paths import build_job_paths, compute_job_id, hash_file
from src.pipeline.schemas import (
    STAGE_PROGRESS,
    PipelineResult,
    PipelineStage,
    StageAiAudit,
    VideoContextSummary,
)
from src.trends.trend_analyzer import run_creator_analysis
from src.trends.worldwide_analyzer import run_worldwide_analysis
from src.utils import load_json, save_json
from src.video.audio import extract_audio
from src.video.frames import extract_candidate_frames
from src.video.validator import validate_video


logger = logging.getLogger(__name__)

ProgressCallback = Callable[[PipelineStage, int, str], None]

SUPPORTED_PLATFORMS = ("youtube", "web")

WORLDWIDE_TARGET_COUNT = 30
CREATOR_TARGET_COUNT = 30


class PipelineError(RuntimeError):
    """Raised for pipeline failures that are safe to show to end users."""


def _report(
    callback: Optional[ProgressCallback],
    stage: PipelineStage,
    message: str,
) -> None:
    if callback is None:
        return

    callback(stage, STAGE_PROGRESS[stage], message)


def _serialize_visual_timeline(visual_timeline: list[dict]) -> list[dict]:
    output = []

    for event in visual_timeline:
        output.append(
            {
                "start_time": event["start_time"],
                "end_time": event["end_time"],
                "strict_spoken_text": event["strict_spoken_text"],
                "context_spoken_text": event["context_spoken_text"],
                "visual_analysis": event["visual_analysis"].model_dump(),
            }
        )

    return output


def _deserialize_visual_timeline(data: list[dict]) -> list[dict]:
    output = []

    for event in data:
        output.append(
            {
                "start_time": event["start_time"],
                "end_time": event["end_time"],
                "strict_spoken_text": event["strict_spoken_text"],
                "context_spoken_text": event["context_spoken_text"],
                "visual_analysis": VisualWindowAnalysis(
                    **event["visual_analysis"]
                ),
            }
        )

    return output


def _get_transcription(audio_path: Path, cache_path: Path) -> dict:
    cached = load_json(cache_path)

    if cached is not None:
        return cached

    transcription = transcribe_audio(str(audio_path))
    save_json(transcription, cache_path)
    return transcription


def _get_visual_timeline(
    windows: list[dict],
    cache_path: Path,
    callback: Optional[ProgressCallback],
) -> list[dict]:
    cached = load_json(cache_path)

    if cached is not None:
        return _deserialize_visual_timeline(cached)

    visual_timeline = []

    for index, window in enumerate(windows, start=1):
        _report(
            callback,
            PipelineStage.VISUAL_ANALYSIS,
            f"Analysing visual window {index}/{len(windows)}",
        )

        visual_analysis, _usage = analyse_visual_window(window)

        visual_timeline.append(
            {
                "start_time": window["start_time"],
                "end_time": window["end_time"],
                "strict_spoken_text": window["strict_spoken_text"],
                "context_spoken_text": window["context_spoken_text"],
                "visual_analysis": visual_analysis,
            }
        )

    save_json(_serialize_visual_timeline(visual_timeline), cache_path)
    return visual_timeline


def _get_video_context(
    transcription: dict,
    visual_timeline: list[dict],
    cache_path: Path,
) -> VideoContext:
    cached = load_json(cache_path)

    if cached is not None:
        return VideoContext(**cached)

    context, _usage = build_video_context(
        transcription=transcription,
        visual_timeline=visual_timeline,
    )

    save_json(context.model_dump(), cache_path)
    return context


def _save_caption_context(context: VideoContext, output_path: Path) -> dict:
    caption_context = {
        "topic": context.topic,
        "content_type": context.content_type,
        "multimodal_summary": context.multimodal_summary,
        "core_message": context.core_message,
    }

    save_json(caption_context, output_path)
    return caption_context


def run_pipeline(
    video_path: Path,
    creator_handle: Optional[str],
    platform: str,
    progress_callback: Optional[ProgressCallback] = None,
) -> PipelineResult:
    creator_handle = (creator_handle or "").strip()

    if platform not in SUPPORTED_PLATFORMS:
        raise PipelineError(
            f"Unsupported platform: {platform}. "
            f"Supported platforms: {', '.join(SUPPORTED_PLATFORMS)}"
        )

    video_path = Path(video_path)

    if not video_path.exists():
        raise PipelineError(f"Video not found: {video_path}")

    _report(progress_callback, PipelineStage.QUEUED, "Job queued")

    video_hash = hash_file(video_path)
    job_id = compute_job_id(video_hash, creator_handle, platform)
    paths = build_job_paths(job_id=job_id, video_hash=video_hash)

    logger.info("Starting pipeline for job_id=%s video_hash=%s", job_id, video_hash)

    _report(progress_callback, PipelineStage.VALIDATING, "Validating video")

    try:
        metadata = validate_video(str(video_path))
    except (ValueError, FileNotFoundError) as exc:
        raise PipelineError(str(exc)) from exc

    duration = metadata["duration"]

    _report(progress_callback, PipelineStage.EXTRACTING_AUDIO, "Extracting audio")
    audio_path = extract_audio(str(video_path), str(paths["audio"]))

    _report(
        progress_callback,
        PipelineStage.EXTRACTING_FRAMES,
        "Scanning frames locally",
    )
    candidates = extract_candidate_frames(
        str(video_path),
        str(paths["frames"]),
        scan_interval=1.0,
    )

    _report(progress_callback, PipelineStage.TRANSCRIBING, "Transcribing audio")
    transcription = _get_transcription(
        audio_path=Path(audio_path),
        cache_path=paths["transcription"],
    )

    _report(
        progress_callback,
        PipelineStage.TEMPORAL_ALIGNMENT,
        "Building temporal windows",
    )
    windows = build_temporal_windows(
        candidates=candidates,
        transcript_segments=transcription["segments"],
        video_duration=duration,
    )

    _report(
        progress_callback,
        PipelineStage.VISUAL_ANALYSIS,
        "Analysing visual timeline",
    )
    visual_timeline = _get_visual_timeline(
        windows=windows,
        cache_path=paths["visual_timeline"],
        callback=progress_callback,
    )

    _report(
        progress_callback,
        PipelineStage.CONTEXT_GENERATION,
        "Building canonical VideoContext",
    )
    context = _get_video_context(
        transcription=transcription,
        visual_timeline=visual_timeline,
        cache_path=paths["video_context"],
    )

    caption_context = _save_caption_context(
        context=context,
        output_path=paths["caption_context"],
    )

    _report(
        progress_callback,
        PipelineStage.WORLDWIDE_TRENDS,
        "Running worldwide trend analysis",
    )
    try:
        run_worldwide_analysis(
            context_path=paths["caption_context"],
            trends_path=paths["w_trends"],
            syntax_path=paths["w_syntax"],
            target_count=WORLDWIDE_TARGET_COUNT,
        )
    except (ValueError, RuntimeError) as exc:
        raise PipelineError(f"Worldwide trend analysis failed: {exc}") from exc

    has_creator_handle = bool(creator_handle)

    if has_creator_handle:
        _report(
            progress_callback,
            PipelineStage.CREATOR_TRENDS,
            f"Analysing creator trends for {creator_handle}",
        )
        try:
            run_creator_analysis(
                handle=creator_handle,
                trends_path=paths["yt_trends"],
                syntax_path=paths["yt_syntax"],
                target_count=CREATOR_TARGET_COUNT,
            )
        except (ValueError, RuntimeError) as exc:
            raise PipelineError(f"Creator trend analysis failed: {exc}") from exc
    else:
        _report(
            progress_callback,
            PipelineStage.CREATOR_TRENDS,
            "No creator handle provided, skipping creator trend analysis",
        )

    if platform == "youtube" and has_creator_handle:
        generation_syntax_path = paths["yt_syntax"]
    else:
        generation_syntax_path = paths["w_syntax"]

    _report(
        progress_callback,
        PipelineStage.CONTENT_GENERATION,
        "Generating titles, descriptions, and hashtags",
    )
    ai_audit: list[StageAiAudit] = []

    try:
        generated_content, content_generation_audit = generate_content(
            video_context_path=paths["caption_context"],
            syntax_path=generation_syntax_path,
        )
    except (ValueError, RuntimeError) as exc:
        raise PipelineError(f"Content generation failed: {exc}") from exc

    ai_audit.append(StageAiAudit(**content_generation_audit))

    save_generated_content(
        generated_content=generated_content,
        output_path=paths["generated_content"],
    )

    _report(
        progress_callback,
        PipelineStage.RANKING,
        "Ranking generated candidates",
    )
    try:
        rankings, discriminator_audit = run_discriminator(
            context_path=paths["video_context"],
            trends_path=paths["w_trends"],
            candidates_path=paths["generated_content"],
            output_path=paths["audit_report"],
        )
    except (ValueError, RuntimeError) as exc:
        raise PipelineError(f"Candidate ranking failed: {exc}") from exc

    ai_audit.append(StageAiAudit(**discriminator_audit))
    save_json([entry.model_dump() for entry in ai_audit], paths["ai_provider_audit"])

    _report(progress_callback, PipelineStage.COMPLETED, "Pipeline complete")

    return PipelineResult(
        job_id=job_id,
        video_context=VideoContextSummary(**caption_context),
        generated_content=generated_content,
        rankings=rankings,
        ai_audit=ai_audit,
    )
