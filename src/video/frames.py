import cv2

from pathlib import Path


MAX_FRAME_WIDTH = 768


def resize_frame(frame):
    height, width = frame.shape[:2]

    if width <= MAX_FRAME_WIDTH:
        return frame

    scale = MAX_FRAME_WIDTH / width

    new_width = int(width * scale)
    new_height = int(height * scale)

    resized = cv2.resize(
        frame,
        (new_width, new_height),
        interpolation=cv2.INTER_AREA,
    )

    return resized


def extract_frames(
    video_path: str,
    output_dir: str,
    interval_seconds: int = 5,
) -> list[dict]:
    output = Path(output_dir)

    output.mkdir(
        parents=True,
        exist_ok=True,
    )

    video = cv2.VideoCapture(video_path)

    if not video.isOpened():
        raise ValueError(
            f"Could not open video: {video_path}"
        )

    fps = video.get(cv2.CAP_PROP_FPS)

    total_frames = video.get(
        cv2.CAP_PROP_FRAME_COUNT
    )

    duration = total_frames / fps

    extracted_frames = []

    timestamp = 0.0
    frame_number = 0

    while timestamp < duration:
        video.set(
            cv2.CAP_PROP_POS_MSEC,
            timestamp * 1000,
        )

        success, frame = video.read()

        if not success:
            break

        frame = resize_frame(frame)

        filename = (
            f"frame_{frame_number:03d}_"
            f"{timestamp:.1f}s.jpg"
        )

        frame_path = output / filename

        cv2.imwrite(
            str(frame_path),
            frame,
            [
                cv2.IMWRITE_JPEG_QUALITY,
                85,
            ],
        )

        extracted_frames.append(
            {
                "frame_number": frame_number,
                "timestamp": round(timestamp, 2),
                "path": str(frame_path),
            }
        )

        timestamp += interval_seconds
        frame_number += 1

    video.release()

    return extracted_frames