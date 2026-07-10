"""Project-root-safe path management for the ClipContext pipeline.

Every path is derived from this file's location, never from the process's
current working directory, so the pipeline behaves the same whether it is
invoked via the CLI or the API server from any directory.

Two tiers of runtime artifacts exist:

- Video-level cache (keyed by a hash of the video's bytes): transcription,
  visual timeline, video context, and caption context do not depend on the
  requesting creator/platform, so they are cached per video content and
  reused across jobs that upload the same video again.
- Job-level output (keyed by job_id, which folds in creator handle and
  platform): trends, syntax, generated content, and the discriminator audit
  report depend on creator/platform and are recomputed per job.
"""

import hashlib
import re
from pathlib import Path


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


PROJECT_ROOT = get_project_root()
DATA_DIR = PROJECT_ROOT / "data"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
UPLOADS_DIR = DATA_DIR / "videos" / "uploads"
CACHE_ROOT = OUTPUTS_DIR / "_cache"

ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm"}


def hash_file(path: Path) -> str:
    hasher = hashlib.sha256()

    with path.open("rb") as file:
        while True:
            chunk = file.read(1024 * 1024)
            if not chunk:
                break
            hasher.update(chunk)

    return hasher.hexdigest()[:16]


def normalize_creator_handle(handle: str) -> str:
    handle = handle.strip().lstrip("@").lower()
    handle = re.sub(r"[^a-z0-9_.-]", "", handle)
    return handle


def compute_job_id(video_hash: str, creator_handle: str, platform: str) -> str:
    normalized_handle = normalize_creator_handle(creator_handle)
    key = f"{video_hash}:{platform}:{normalized_handle}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def safe_upload_filename(job_id: str, original_filename: str) -> str:
    extension = Path(original_filename).suffix.lower()

    if extension not in ALLOWED_VIDEO_EXTENSIONS:
        extension = ".mp4"

    return f"{job_id}{extension}"


def upload_path(job_id: str, original_filename: str) -> Path:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    return UPLOADS_DIR / safe_upload_filename(job_id, original_filename)


def resolve_upload_video_path(job_id: str) -> Path | None:
    """Locate the original uploaded video for a job already known to exist.

    Callers must validate the job_id against the job registry first — this
    only globs the uploads directory, it does not itself authenticate the
    job_id. Uploaded files are always named "<job_id><extension>" (see
    safe_upload_filename), so this never traverses outside UPLOADS_DIR.
    """
    if not UPLOADS_DIR.exists():
        return None

    for candidate in sorted(UPLOADS_DIR.glob(f"{job_id}.*")):
        if candidate.suffix.lower() in ALLOWED_VIDEO_EXTENSIONS:
            return candidate

    return None


def cache_dir(video_hash: str) -> Path:
    path = CACHE_ROOT / video_hash
    path.mkdir(parents=True, exist_ok=True)
    return path


def audio_dir(video_hash: str) -> Path:
    path = DATA_DIR / "audio" / video_hash
    path.mkdir(parents=True, exist_ok=True)
    return path


def frames_dir(video_hash: str) -> Path:
    path = DATA_DIR / "frames" / video_hash
    path.mkdir(parents=True, exist_ok=True)
    return path


def job_output_dir(job_id: str) -> Path:
    path = OUTPUTS_DIR / job_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def build_job_paths(job_id: str, video_hash: str) -> dict:
    video_cache_dir = cache_dir(video_hash)
    output_dir = job_output_dir(job_id)
    trends_directory = output_dir / "trends"
    syntax_directory = output_dir / "syntax"

    trends_directory.mkdir(parents=True, exist_ok=True)
    syntax_directory.mkdir(parents=True, exist_ok=True)

    return {
        "output_dir": output_dir,
        "audio": audio_dir(video_hash) / "audio.wav",
        "frames": frames_dir(video_hash),
        "transcription": video_cache_dir / "transcription.json",
        "visual_timeline": video_cache_dir / "visual_timeline.json",
        "video_context": video_cache_dir / "video_context.json",
        "caption_context": video_cache_dir / "caption_context.json",
        "w_trends": trends_directory / "w_trends.json",
        "yt_trends": trends_directory / "yt_trends.json",
        "w_syntax": syntax_directory / "w_syntax.json",
        "yt_syntax": syntax_directory / "yt_syntax.json",
        "generated_content": output_dir / "generated_content.json",
        "audit_report": output_dir / "audit_report.json",
        "ai_provider_audit": output_dir / "ai_provider_audit.json",
    }
