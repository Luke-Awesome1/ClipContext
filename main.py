import hashlib
from multiprocessing import context
from multiprocessing import context
import os

from src.video.validator import (
    validate_video,
)
from src.video.audio import (
    extract_audio,
)
from src.video.frames import (
    extract_candidate_frames,
)

from src.ai.transcriber import (
    transcribe_audio,
)
from src.ai.temporal_alignment import (
    build_temporal_windows,
)
from src.ai.fireworks.multimodal import (
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

DATA_DIR = "data"
OUTPUT_DIR = "outputs"


def generate_video_id(
    video_path: str,
) -> str:
    hasher = hashlib.sha256()

    with open(
        video_path,
        "rb",
    ) as video_file:
        while True:
            chunk = video_file.read(
                1024 * 1024
            )

            if not chunk:
                break

            hasher.update(chunk)

    return hasher.hexdigest()[:16]


def build_video_paths(
    video_id: str,
) -> dict:
    video_output_dir = os.path.join(
        OUTPUT_DIR,
        video_id,
    )

    audio_dir = os.path.join(
        DATA_DIR,
        "audio",
        video_id,
    )

    frame_dir = os.path.join(
        DATA_DIR,
        "frames",
        video_id,
    )

    os.makedirs(
        video_output_dir,
        exist_ok=True,
    )

    os.makedirs(
        audio_dir,
        exist_ok=True,
    )

    os.makedirs(
        frame_dir,
        exist_ok=True,
    )
    

    return {
        "audio": os.path.join(
            audio_dir,
            "audio.wav",
        ),
        "frames": frame_dir,
        "transcription": os.path.join(
            video_output_dir,
            "transcription.json",
        ),
        "visual_timeline": os.path.join(
            video_output_dir,
            "visual_timeline.json",
        ),
        "video_context": os.path.join(
            video_output_dir,
            "video_context.json",
        ),
        "caption_context": os.path.join(
            video_output_dir,
            "caption_context.json",
        ),
    }


def get_transcription(
    audio_path: str,
    cache_path: str,
) -> dict:
    cached = load_json(
        cache_path
    )

    if cached is not None:
        print(
            "Using cached transcription."
        )

        return cached

    print(
        "Transcribing audio locally..."
    )

    transcription = transcribe_audio(
        audio_path
    )

    save_json(
        transcription,
        cache_path,
    )

    return transcription


def serialize_visual_timeline(
    visual_timeline: list[dict],
) -> list[dict]:
    output = []

    for event in visual_timeline:
        output.append(
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

    return output


def deserialize_visual_timeline(
    data: list[dict],
) -> list[dict]:
    output = []

    for event in data:
        output.append(
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

    return output


def get_visual_timeline(
    windows: list[dict],
    cache_path: str,
) -> tuple[
    list[dict],
    dict,
]:
    cached = load_json(
        cache_path
    )

    if cached is not None:
        print(
            "Using cached Kimi K2.6 visual timeline."
        )

        return (
            deserialize_visual_timeline(
                cached
            ),
            {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "latency_seconds": 0.0,
                "calls": 0,
            },
        )

    visual_timeline = []

    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_latency = 0.0
    calls = 0

    for index, window in enumerate(
        windows,
        start=1,
    ):
        print(
            "\nAnalysing visual window "
            f"{index}/{len(windows)} "
            "with Kimi K2.6..."
        )

        (
            visual_analysis,
            usage,
        ) = analyse_visual_window(
            window
        )

        total_prompt_tokens += (
            usage["prompt_tokens"]
        )

        total_completion_tokens += (
            usage["completion_tokens"]
        )

        total_latency += (
            usage["latency_seconds"]
        )

        calls += 1

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

        print(
            "Completed window "
            f"{index}/{len(windows)}"
        )

        print(
            "Prompt tokens: "
            f"{usage['prompt_tokens']:,}"
        )

        print(
            "Completion tokens: "
            f"{usage['completion_tokens']:,}"
        )

        print(
            "Latency: "
            f"{usage['latency_seconds']:.2f}s"
        )

    save_json(
        serialize_visual_timeline(
            visual_timeline
        ),
        cache_path,
    )

    return (
        visual_timeline,
        {
            "prompt_tokens": (
                total_prompt_tokens
            ),
            "completion_tokens": (
                total_completion_tokens
            ),
            "latency_seconds": (
                total_latency
            ),
            "calls": calls,
        },
    )


def get_video_context(
    transcription: dict,
    visual_timeline: list[dict],
    cache_path: str,
) -> tuple[
    VideoContext,
    dict,
]:
    cached = load_json(
        cache_path
    )

    if cached is not None:
        print(
            "Using cached Kimi K2.6 VideoContext."
        )

        return (
            VideoContext(**cached),
            {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "latency_seconds": 0.0,
                "calls": 0,
            },
        )

    print(
        "\nBuilding canonical VideoContext "
        "with Kimi K2.6..."
    )

    context, usage = build_video_context(
        transcription=transcription,
        visual_timeline=visual_timeline,
    )

    save_json(
        context.model_dump(),
        cache_path,
    )

    return (
        context,
        {
            **usage,
            "calls": 1,
        },
    )


def estimate_cost(
    prompt_tokens: int,
    completion_tokens: int,
) -> float:
    input_cost = (
        prompt_tokens
        / 1_000_000
        * 0.95
    )

    output_cost = (
        completion_tokens
        / 1_000_000
        * 4.00
    )

    return input_cost + output_cost
def save_caption_context(
    context: VideoContext,
    output_path: str,
) -> dict:
    caption_context = {
        "topic": context.topic,
        "content_type": context.content_type,
        "multimodal_summary": (
            context.multimodal_summary
        ),
        "core_message": context.core_message,
    }

    save_json(
        caption_context,
        output_path,
    )

    return caption_context

def main():
    print(
        "\n"
        + "=" * 60
    )

    print(
        "CLIPCONTEXT — KIMI K2.6 PIPELINE"
    )

    print(
        "=" * 60
    )

    print(
        "\n0. Identifying video..."
    )

    video_id = generate_video_id(
        VIDEO_PATH
    )

    paths = build_video_paths(
        video_id
    )

    print(
        f"Video ID: {video_id}"
    )

    print(
        "\n1. Validating video..."
    )

    metadata = validate_video(
        VIDEO_PATH
    )

    duration = metadata["duration"]

    print(
        f"Duration: {duration:.2f}s"
    )

    print(
        "\n2. Extracting audio..."
    )

    audio_path = extract_audio(
        VIDEO_PATH,
        paths["audio"],
    )

    print(
        "\n3. Scanning frames locally..."
    )

    candidates = extract_candidate_frames(
        VIDEO_PATH,
        paths["frames"],
        scan_interval=1.0,
    )

    print(
        "Candidate frames scanned: "
        f"{len(candidates)}"
    )

    print(
        "\n4. Loading transcription..."
    )

    transcription = get_transcription(
        audio_path=audio_path,
        cache_path=paths["transcription"],
    )

    print(
        "\n5. Building temporal windows..."
    )

    windows = build_temporal_windows(
        candidates=candidates,
        transcript_segments=(
            transcription["segments"]
        ),
        video_duration=duration,
    )

    selected_frame_count = sum(
        len(window["frames"])
        for window in windows
    )

    print(
        "Temporal windows: "
        f"{len(windows)}"
    )

    print(
        "Selected frames: "
        f"{selected_frame_count}"
    )

    print(
        "\n6. Building visual timeline..."
    )

    (
        visual_timeline,
        visual_usage,
    ) = get_visual_timeline(
        windows=windows,
        cache_path=(
            paths["visual_timeline"]
        ),
    )

    print(
        "\n7. Building VideoContext..."
    )

    (
        context,
        context_usage,
    ) = get_video_context(
        transcription=transcription,
        visual_timeline=visual_timeline,
        cache_path=(
            paths["video_context"]
        ),
    )
    print(
    "\n8. Extracting caption context..."
    )

    caption_context = save_caption_context(
        context=context,
        output_path=(
        paths["caption_context"]
    ),
    )   

    print(
        "Caption context saved to:"
    )

    print(
        paths["caption_context"]
    )

    total_prompt_tokens = (
        visual_usage["prompt_tokens"]
        + context_usage["prompt_tokens"]
    )

    total_completion_tokens = (
        visual_usage["completion_tokens"]
        + context_usage[
            "completion_tokens"
        ]
    )

    total_calls = (
        visual_usage["calls"]
        + context_usage["calls"]
    )

    total_latency = (
        visual_usage["latency_seconds"]
        + context_usage[
            "latency_seconds"
        ]
    )

    estimated_cost = estimate_cost(
        prompt_tokens=total_prompt_tokens,
        completion_tokens=(
            total_completion_tokens
        ),
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
        "INFERENCE METRICS"
    )

    print(
        "=" * 60
    )

    print(
        f"Video ID: {video_id}"
    )

    print(
        f"Fireworks calls: {total_calls}"
    )

    print(
        "Prompt tokens: "
        f"{total_prompt_tokens:,}"
    )

    print(
        "Completion tokens: "
        f"{total_completion_tokens:,}"
    )

    print(
        "Total model latency: "
        f"{total_latency:.2f}s"
    )

    print(
        "Estimated Kimi K2.6 cost: "
        f"${estimated_cost:.6f}"
    )

    print(
        "\n"
        + "=" * 60
    )

    print(
        "CLIPCONTEXT PIPELINE COMPLETE"
    )

    print(
        "=" * 60
    )


if __name__ == "__main__":
    main()