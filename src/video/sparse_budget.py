MAX_VLM_FRAMES = 12


def calculate_window_priority(
    window: dict,
) -> float:
    score = 0.0

    if window["strict_spoken_text"]:
        score += 1.0

    if window["context_spoken_text"]:
        score += 0.25

    frames = window["frames"]

    if len(frames) >= 2:
        score_difference = abs(
            frames[0]["score"]
            - frames[-1]["score"]
        )

        score += min(
            score_difference,
            1.0,
        )

    return score


def apply_sparse_frame_budget(
    windows: list[dict],
    max_frames: int = MAX_VLM_FRAMES,
) -> list[dict]:
    total_frames = sum(
        len(window["frames"])
        for window in windows
    )

    if total_frames <= max_frames:
        return windows

    budgeted_windows = []

    for window in windows:
        budgeted_windows.append(
            {
                **window,
                "frames": [],
            }
        )

    frame_budget = max_frames

    # Pass 1:
    # Give every window one representative frame.
    for index, window in enumerate(windows):
        if (
            frame_budget <= 0
            or not window["frames"]
        ):
            continue

        budgeted_windows[index]["frames"].append(
            window["frames"][0]
        )

        frame_budget -= 1

    if frame_budget <= 0:
        return budgeted_windows

    # Pass 2:
    # Give additional frames to high-priority windows.
    priorities = sorted(
        range(len(windows)),
        key=lambda index: calculate_window_priority(
            windows[index]
        ),
        reverse=True,
    )

    for index in priorities:
        if frame_budget <= 0:
            break

        original_frames = windows[index]["frames"]

        if len(original_frames) < 2:
            continue

        second_frame = original_frames[1]

        budgeted_windows[index]["frames"].append(
            second_frame
        )

        frame_budget -= 1

    return budgeted_windows