from src.video.frame_selector import (
    select_window_frames,
)


WINDOW_SIZE = 5.0


def get_overlapping_segments(
    start_time: float,
    end_time: float,
    transcript_segments: list[dict],
) -> list[dict]:
    return [
        segment
        for segment in transcript_segments
        if (
            segment["start"] < end_time
            and segment["end"] > start_time
        )
    ]


def get_strict_segments(
    start_time: float,
    end_time: float,
    transcript_segments: list[dict],
) -> list[dict]:
    strict = []

    for segment in transcript_segments:
        midpoint = (
            segment["start"]
            + segment["end"]
        ) / 2

        if (
            midpoint >= start_time
            and midpoint < end_time
        ):
            strict.append(segment)

    return strict


def build_temporal_windows(
    candidates: list[dict],
    transcript_segments: list[dict],
    video_duration: float,
) -> list[dict]:
    windows = []

    start_time = 0.0

    while start_time < video_duration:
        end_time = min(
            start_time + WINDOW_SIZE,
            video_duration,
        )

        selected_frames = select_window_frames(
            candidates=candidates,
            start_time=start_time,
            end_time=end_time,
            max_frames=3,
        )

        overlapping_segments = (
            get_overlapping_segments(
                start_time=start_time,
                end_time=end_time,
                transcript_segments=(
                    transcript_segments
                ),
            )
        )

        strict_segments = get_strict_segments(
            start_time=start_time,
            end_time=end_time,
            transcript_segments=(
                transcript_segments
            ),
        )

        context_spoken_text = " ".join(
            segment["text"]
            for segment in overlapping_segments
        )

        strict_spoken_text = " ".join(
            segment["text"]
            for segment in strict_segments
        )

        windows.append(
            {
                "start_time": round(
                    start_time,
                    2,
                ),
                "end_time": round(
                    end_time,
                    2,
                ),
                "frames": selected_frames,
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