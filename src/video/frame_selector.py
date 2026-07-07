import cv2
import numpy as np


QUALITY_WEIGHT = 0.55
DIVERSITY_WEIGHT = 0.45


def load_gray_thumbnail(
    frame_path: str,
    size: tuple[int, int] = (32, 32),
):
    image = cv2.imread(frame_path)

    if image is None:
        raise ValueError(
            f"Could not read frame: {frame_path}"
        )

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY,
    )

    thumbnail = cv2.resize(
        gray,
        size,
        interpolation=cv2.INTER_AREA,
    )

    return thumbnail.astype(np.float32)


def calculate_visual_difference(
    frame_a: dict,
    frame_b: dict,
) -> float:
    image_a = load_gray_thumbnail(
        frame_a["path"]
    )

    image_b = load_gray_thumbnail(
        frame_b["path"]
    )

    difference = np.mean(
        np.abs(image_a - image_b)
    )

    normalized_difference = min(
        difference / 255.0,
        1.0,
    )

    return float(normalized_difference)


def calculate_diversity_score(
    candidate: dict,
    selected: list[dict],
) -> float:
    if not selected:
        return 1.0

    differences = [
        calculate_visual_difference(
            candidate,
            selected_frame,
        )
        for selected_frame in selected
    ]

    return min(differences)


def select_window_frames(
    candidates: list[dict],
    start_time: float,
    end_time: float,
    max_frames: int = 3,
) -> list[dict]:
    window_candidates = [
        frame
        for frame in candidates
        if (
            frame["timestamp"] >= start_time
            and frame["timestamp"] < end_time
        )
    ]

    if not window_candidates:
        return []

    remaining = window_candidates.copy()

    first_frame = max(
        remaining,
        key=lambda frame: frame["score"],
    )

    selected = [first_frame]

    remaining.remove(first_frame)

    while (
        len(selected) < max_frames
        and remaining
    ):
        best_candidate = None
        best_combined_score = -1.0

        for candidate in remaining:
            diversity_score = (
                calculate_diversity_score(
                    candidate,
                    selected,
                )
            )

            combined_score = (
                candidate["score"]
                * QUALITY_WEIGHT
                + diversity_score
                * DIVERSITY_WEIGHT
            )

            if (
                combined_score
                > best_combined_score
            ):
                best_combined_score = (
                    combined_score
                )

                best_candidate = candidate

        selected.append(best_candidate)

        remaining.remove(best_candidate)

    return sorted(
        selected,
        key=lambda frame: frame["timestamp"],
    )