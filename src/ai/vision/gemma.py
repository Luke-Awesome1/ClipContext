import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.models.visual_window import (
    VisualWindowAnalysis,
)


load_dotenv()


MODEL_ID = "gemini-3.1-flash-lite"


_client = None


def get_gemma_client() -> genai.Client:
    global _client

    if _client is None:
        api_key = os.getenv(
            "GEMINI_API_KEY"
        )

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set."
            )

        _client = genai.Client(
            api_key=api_key
        )

    return _client


def build_visual_prompt(
    window: dict,
) -> str:
    timestamps = [
        frame["timestamp"]
        for frame in window["frames"]
    ]

    return f"""
You are the visual observation layer of ClipContext.

You are analysing representative frames selected from a
short video window.

WINDOW:
{window["start_time"]:.2f}s to
{window["end_time"]:.2f}s

FRAME TIMESTAMPS:
{timestamps}

The supplied images are in chronological order.

Each image corresponds to the timestamp at the same
position in the timestamp list.

Your task is to describe only the visual evidence contained
in this short temporal window.

You may compare frames to identify visible change.

Examples of supported observations:

- a subject appears or disappears
- visible posture changes
- the camera view changes
- the setting changes
- readable text changes
- an object becomes visible
- the scene transitions

Do not use the video transcript.

Do not infer spoken dialogue.

Do not infer creator intention.

Do not infer the video's overall message.

Do not identify people unless their identity is visibly
established.

Do not convert visual symbolism into literal fact.

Do not claim continuous movement from a single frame.

When multiple frames support an apparent visual change,
describe the change conservatively.

This observation will later be handed to a copywriter who never
sees the actual frames. A specific, concrete detail here becomes
usable material for a hook; a generic label ("a person", "a
room") is information the copywriter permanently loses. When the
frames support one, prefer the specific version: a precise facial
expression or reaction, a striking prop or composition, readable
on-screen text with real impact — not just that a person or scene
is present.

Return a factual visual observation.

The output must contain:

description:
A concise summary of visible progression across the frames.

subjects:
Important visible people, animals, or focal subjects.

actions:
Visible actions or changes supported by the sampled sequence.

objects:
Visually important objects.

visible_text:
Only clearly readable text. Preserve exact wording.

setting:
The visible physical or digital environment.

visual_mood:
Mood suggested only by lighting, composition, facial
expression, and presentation.

Prefer specific observations over generic descriptions.
""".strip()


def build_contents(
    window: dict,
) -> list:
    contents = [
        build_visual_prompt(window)
    ]

    for frame in window["frames"]:
        contents.append(
            types.Part.from_text(
                text=(
                    "FRAME TIMESTAMP: "
                    f"{frame['timestamp']:.2f} seconds"
                )
            )
        )

        with open(
            frame["path"],
            "rb",
        ) as image_file:
            image_bytes = image_file.read()

        contents.append(
            types.Part.from_bytes(
                data=image_bytes,
                mime_type="image/jpeg",
            )
        )

    return contents


def analyse_visual_window(
    window: dict,
) -> VisualWindowAnalysis:
    if not window["frames"]:
        return VisualWindowAnalysis(
            description=(
                "No sampled visual frames available."
            ),
            subjects=[],
            actions=[],
            objects=[],
            visible_text=[],
            setting="Unknown",
            visual_mood="Unknown",
        )

    client = get_gemma_client()

    response = client.models.generate_content(
        model=MODEL_ID,
        contents=build_contents(window),
        config=types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type=(
                "application/json"
            ),
            response_schema=(
                VisualWindowAnalysis
            ),
        ),
    )

    if response.parsed is not None:
        return response.parsed

    return (
        VisualWindowAnalysis.model_validate_json(
            response.text
        )
    )