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

    return cv2.resize(
        frame,
        (new_width, new_height),
        interpolation=cv2.INTER_AREA,
    )


def calculate_frame_score(frame) -> float:
    gray = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2GRAY,
    )

    mean_brightness = gray.mean()

    brightness_score = min(
        mean_brightness / 80.0,
        1.0,
    )

    edges = cv2.Canny(
        gray,
        100,
        200,
    )

    edge_density = (
        edges > 0
    ).mean()

    edge_score = min(
        edge_density / 0.10,
        1.0,
    )

    contrast = gray.std()

    contrast_score = min(
        contrast / 64.0,
        1.0,
    )

    score = (
        brightness_score * 0.30
        + edge_score * 0.35
        + contrast_score * 0.35
    )

    return float(score)


def read_frame_at_timestamp(
    video,
    timestamp: float,
):
    video.set(
        cv2.CAP_PROP_POS_MSEC,
        timestamp * 1000,
    )

    success, frame = video.read()

    if not success:
        return None

    return frame


def extract_candidate_frames(
    video_path: str,
    output_dir: str,
    scan_interval: float = 1.0,
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

    fps = video.get(
        cv2.CAP_PROP_FPS
    )

    total_frames = video.get(
        cv2.CAP_PROP_FRAME_COUNT
    )

    duration = total_frames / fps

    candidates = []

    timestamp = 0.0
    frame_number = 0

    while timestamp < duration:
        frame = read_frame_at_timestamp(
            video,
            timestamp,
        )

        if frame is None:
            timestamp += scan_interval
            continue

        frame = resize_frame(frame)

        score = calculate_frame_score(frame)

        filename = (
            f"candidate_{frame_number:03d}_"
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

        candidates.append(
            {
                "timestamp": round(
                    timestamp,
                    2,
                ),
                "path": str(frame_path),
                "score": round(score, 4),
            }
        )

        timestamp += scan_interval
        frame_number += 1

    video.release()

    return candidates