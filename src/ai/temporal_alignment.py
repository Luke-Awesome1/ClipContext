from src.video.frame_selector import (
    select_window_frames,
)


WINDOW_SIZE_SECONDS = 5.0

MAX_FRAMES_PER_WINDOW = 3


def get_strict_spoken_text(
    transcript_segments: list[dict],
    start_time: float,
    end_time: float,
) -> str:
    texts = []

    for segment in transcript_segments:
        midpoint = (
            segment["start"]
            + segment["end"]
        ) / 2

        if (
            midpoint >= start_time
            and midpoint < end_time
        ):
            text = segment["text"].strip()

            if text:
                texts.append(text)

    return " ".join(texts)


def get_context_spoken_text(
    transcript_segments: list[dict],
    start_time: float,
    end_time: float,
) -> str:
    texts = []

    for segment in transcript_segments:
        overlaps = (
            segment["start"] < end_time
            and segment["end"] > start_time
        )

        if overlaps:
            text = segment["text"].strip()

            if text:
                texts.append(text)

    return " ".join(texts)


def build_temporal_windows(
    candidates: list[dict],
    transcript_segments: list[dict],
    video_duration: float,
) -> list[dict]:
    windows = []

    start_time = 0.0

    while start_time < video_duration:
        end_time = min(
            start_time + WINDOW_SIZE_SECONDS,
            video_duration,
        )

        frames = select_window_frames(
            candidates=candidates,
            start_time=start_time,
            end_time=end_time,
            max_frames=MAX_FRAMES_PER_WINDOW,
        )

        strict_spoken_text = (
            get_strict_spoken_text(
                transcript_segments=(
                    transcript_segments
                ),
                start_time=start_time,
                end_time=end_time,
            )
        )

        context_spoken_text = (
            get_context_spoken_text(
                transcript_segments=(
                    transcript_segments
                ),
                start_time=start_time,
                end_time=end_time,
            )
        )

        windows.append(
            {
                "start_time": start_time,
                "end_time": end_time,
                "frames": frames,
                "strict_spoken_text": (
                    strict_spoken_text
                ),
                "context_spoken_text": (
                    context_spoken_text
                ),
            }
        )

        start_time = end_time

    return windows