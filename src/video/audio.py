import subprocess
from pathlib import Path


def extract_audio(
    video_path: str,
    output_path: str,
) -> str:
    output = Path(output_path)

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    command = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        str(output),
    ]

    subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True,
    )

    return str(output)