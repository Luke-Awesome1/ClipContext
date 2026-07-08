import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from src.config import validate_environment
from src.pipeline.runner import PipelineError, run_pipeline
from src.pipeline.schemas import PipelineStage


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the ClipContext video analysis pipeline"
    )

    parser.add_argument(
        "video",
        type=Path,
        help="Path to the input video",
    )

    parser.add_argument(
        "--creator",
        type=str,
        default=None,
        help=(
            "YouTube creator handle used for creator-specific trend "
            "analysis. If omitted, creator trend analysis is skipped and "
            "generation falls back to worldwide syntax."
        ),
    )

    parser.add_argument(
        "--platform",
        choices=["youtube", "web"],
        default="youtube",
    )

    return parser.parse_args()


def print_progress(stage: PipelineStage, progress: int, message: str) -> None:
    print(f"[{progress:3d}%] {stage.value}: {message}")


def main() -> None:
    validate_environment()

    args = parse_arguments()

    video_path = args.video.expanduser().resolve()

    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    print("=" * 60)
    print("CLIPCONTEXT PIPELINE")
    print("=" * 60)

    try:
        result = run_pipeline(
            video_path=video_path,
            creator_handle=args.creator,
            platform=args.platform,
            progress_callback=print_progress,
        )
    except PipelineError as error:
        print(f"\nPipeline failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error

    print("\n" + "=" * 60)
    print("FINAL VIDEO CONTEXT")
    print("=" * 60 + "\n")
    print(json.dumps(result.video_context.model_dump(), indent=2))

    print("\n" + "=" * 60)
    print("CLIPCONTEXT PIPELINE COMPLETE")
    print(f"Job ID: {result.job_id}")
    print("=" * 60)


if __name__ == "__main__":
    main()
