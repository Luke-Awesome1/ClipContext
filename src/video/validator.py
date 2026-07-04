import subprocess
import json
from pathlib import Path


MIN_DURATION = 5
MAX_DURATION = 120


def get_video_metadata(video_path: str) -> dict:
    path = Path(video_path)

    if not path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    command = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True,
    )

    metadata = json.loads(result.stdout)

    return metadata


def validate_video(video_path: str) -> dict:
    metadata = get_video_metadata(video_path)

    duration = float(metadata["format"]["duration"])

    if duration < MIN_DURATION:
        raise ValueError(
            f"Video is too short: {duration:.2f}s. "
            f"Minimum duration is {MIN_DURATION}s."
        )

    if duration > MAX_DURATION:
        raise ValueError(
            f"Video is too long: {duration:.2f}s. "
            f"Maximum duration is {MAX_DURATION}s."
        )

    video_stream = next(
        (
            stream
            for stream in metadata["streams"]
            if stream["codec_type"] == "video"
        ),
        None,
    )

    if video_stream is None:
        raise ValueError("No video stream found.")

    return {
        "duration": duration,
        "width": video_stream.get("width"),
        "height": video_stream.get("height"),
        "codec": video_stream.get("codec_name"),
    }