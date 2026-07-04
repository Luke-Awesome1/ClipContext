def get_overlapping_segments(
    start_time: float,
    end_time: float,
    transcript_segments: list[dict],
) -> list[dict]:
    overlapping = []

    for segment in transcript_segments:
        segment_start = segment["start"]
        segment_end = segment["end"]

        overlaps = (
            segment_start < end_time
            and segment_end > start_time
        )

        if overlaps:
            overlapping.append(segment)

    return overlapping


def build_temporal_windows(
    frames: list[dict],
    transcript_segments: list[dict],
    video_duration: float,
) -> list[dict]:
    windows = []

    for index, frame in enumerate(frames):
        start_time = frame["timestamp"]

        if index + 1 < len(frames):
            end_time = frames[index + 1]["timestamp"]
        else:
            end_time = video_duration

        segments = get_overlapping_segments(
            start_time=start_time,
            end_time=end_time,
            transcript_segments=transcript_segments,
        )

        spoken_text = " ".join(
            segment["text"]
            for segment in segments
        )

        windows.append(
            {
                "start_time": round(start_time, 2),
                "end_time": round(end_time, 2),
                "frame_path": frame["path"],
                "spoken_text": spoken_text,
                "transcript_segments": segments,
            }
        )

    return windows