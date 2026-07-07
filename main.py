from src.video.validator import validate_video
from src.video.audio import extract_audio
from src.video.frames import extract_candidate_frames

from src.ai.transcriber import transcribe_audio
from src.ai.temporal_alignment import (
    build_temporal_windows,
)
from src.ai.gemini_vision import (
    analyse_visual_window,
)
from src.ai.context_builder import (
    build_video_context,
)

from src.models.visual_window import (
    VisualWindowAnalysis,
)
from src.models.video_context import (
    VideoContext,
)

from src.utils import (
    save_json,
    load_json,
)


VIDEO_PATH = "data/videos/test.mp4"
AUDIO_PATH = "data/audio/test.wav"
FRAME_DIR = "data/frames/test"

TRANSCRIPTION_CACHE = (
    "outputs/test_transcription.json"
)

VISUAL_CACHE = (
    "outputs/test_visual_timeline.json"
)

CONTEXT_CACHE = (
    "outputs/test_video_context.json"
)


def get_transcription(
    audio_path: str,
) -> dict:
    cached = load_json(
        TRANSCRIPTION_CACHE
    )

    if cached is not None:
        print(
            "Using cached transcription."
        )

        return cached

    print(
        "Transcribing audio..."
    )

    transcription = transcribe_audio(
        audio_path
    )

    save_json(
        transcription,
        TRANSCRIPTION_CACHE,
    )

    return transcription


def get_visual_timeline(
    windows: list[dict],
) -> list[dict]:
    cached = load_json(
        VISUAL_CACHE
    )

    if cached is not None:
        print(
            "Using cached visual timeline."
        )

        timeline = []

        for event in cached:
            timeline.append(
                {
                    "start_time": (
                        event["start_time"]
                    ),
                    "end_time": (
                        event["end_time"]
                    ),
                    "strict_spoken_text": (
                        event[
                            "strict_spoken_text"
                        ]
                    ),
                    "context_spoken_text": (
                        event[
                            "context_spoken_text"
                        ]
                    ),
                    "visual_analysis": (
                        VisualWindowAnalysis(
                            **event[
                                "visual_analysis"
                            ]
                        )
                    ),
                }
            )

        return timeline

    visual_timeline = []

    for index, window in enumerate(
        windows,
        start=1,
    ):
        print(
            f"Analysing visual window "
            f"{index}/{len(windows)}..."
        )

        visual_analysis = (
            analyse_visual_window(window)
        )

        visual_timeline.append(
            {
                "start_time": (
                    window["start_time"]
                ),
                "end_time": (
                    window["end_time"]
                ),
                "strict_spoken_text": (
                    window[
                        "strict_spoken_text"
                    ]
                ),
                "context_spoken_text": (
                    window[
                        "context_spoken_text"
                    ]
                ),
                "visual_analysis": (
                    visual_analysis
                ),
            }
        )

    serializable = []

    for event in visual_timeline:
        serializable.append(
            {
                "start_time": (
                    event["start_time"]
                ),
                "end_time": (
                    event["end_time"]
                ),
                "strict_spoken_text": (
                    event[
                        "strict_spoken_text"
                    ]
                ),
                "context_spoken_text": (
                    event[
                        "context_spoken_text"
                    ]
                ),
                "visual_analysis": (
                    event[
                        "visual_analysis"
                    ].model_dump()
                ),
            }
        )

    save_json(
        serializable,
        VISUAL_CACHE,
    )

    return visual_timeline


def get_video_context(
    transcription: dict,
    visual_timeline: list[dict],
) -> VideoContext:
    cached = load_json(
        CONTEXT_CACHE
    )

    if cached is not None:
        print(
            "Using cached VideoContext."
        )

        return VideoContext(
            **cached
        )

    print(
        "Building multimodal VideoContext..."
    )

    context = build_video_context(
        transcription=transcription,
        visual_timeline=visual_timeline,
    )

    save_json(
        context.model_dump(),
        CONTEXT_CACHE,
    )

    return context


def main():
    print(
        "\n1. Validating video..."
    )

    metadata = validate_video(
        VIDEO_PATH
    )

    print(
        f"Duration: "
        f"{metadata['duration']:.2f}s"
    )

    print(
        "\n2. Extracting audio..."
    )

    audio_path = extract_audio(
        VIDEO_PATH,
        AUDIO_PATH,
    )

    print(
        "\n3. Extracting candidate frames..."
    )

    candidates = extract_candidate_frames(
        VIDEO_PATH,
        FRAME_DIR,
        scan_interval=1.0,
    )

    print(
        f"Candidate frames: "
        f"{len(candidates)}"
    )

    print(
        "\n4. Loading transcription..."
    )

    transcription = get_transcription(
        audio_path
    )

    print(
        "\n5. Building temporal windows..."
    )

    windows = build_temporal_windows(
        candidates=candidates,
        transcript_segments=(
            transcription["segments"]
        ),
        video_duration=(
            metadata["duration"]
        ),
    )

    print(
        f"Temporal windows: "
        f"{len(windows)}"
    )

    print(
        "\n6. Loading visual timeline..."
    )

    visual_timeline = get_visual_timeline(
        windows
    )

    print(
        "\n7. Building VideoContext..."
    )

    context = get_video_context(
        transcription=transcription,
        visual_timeline=visual_timeline,
    )

    print(
        "\n"
        + "=" * 60
    )

    print(
        "FINAL VIDEO CONTEXT"
    )

    print(
        "=" * 60
        + "\n"
    )

    print(
        context.model_dump_json(
            indent=2
        )
    )

    print(
        "\n"
        + "=" * 60
    )

    print(
        "Pipeline completed successfully."
    )


if __name__ == "__main__":
    main()