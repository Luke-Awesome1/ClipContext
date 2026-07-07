import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.models.visual_window import (
    VisualWindowAnalysis,
)


load_dotenv()


MODEL_ID = "gemini-2.5-flash"


_client = None


def get_gemini_client() -> genai.Client:
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
You are a conservative visual timeline observation system.

You are analysing sampled frames from a video window
covering {window["start_time"]:.2f} to
{window["end_time"]:.2f} seconds.

The supplied images are in chronological order.

Their timestamps are:

{timestamps}

Each image corresponds to the timestamp at the same
position in this list.

Your task is to describe what the sampled visual evidence
shows during this short video window.

You may compare frames to identify visible change.

For example:
- a subject appears in one frame and not another
- the camera view changes
- a person changes visible posture
- displayed text changes
- the setting changes

Do NOT claim a continuous action unless the sampled frames
support that interpretation.

Do NOT infer:
- spoken dialogue
- creator intention
- overall video message
- motivation or symbolism
- events outside this window
- a person's identity unless visibly written

Return a factual visual observation.

description:
Summarise the visible progression across the sampled frames.
Distinguish direct evidence from apparent visual change.

subjects:
List important visible people, animals, or focal subjects.

actions:
List actions or visible changes supported by the sequence.
Avoid inventing motion from one static frame.

objects:
List visually important objects.

visible_text:
Copy only clearly readable text.
Do not guess partial text.

setting:
Describe the visible physical or digital environment.

visual_mood:
Describe only mood suggested by lighting, composition,
facial expression, and presentation.

Be specific and conservative.
""".strip()


def build_image_parts(
    window: dict,
) -> list:
    parts = []

    for frame in window["frames"]:
        timestamp = frame["timestamp"]

        parts.append(
            types.Part.from_text(
                text=(
                    f"FRAME TIMESTAMP: "
                    f"{timestamp:.2f} seconds"
                )
            )
        )

        with open(
            frame["path"],
            "rb",
        ) as image_file:
            image_bytes = image_file.read()

        parts.append(
            types.Part.from_bytes(
                data=image_bytes,
                mime_type="image/jpeg",
            )
        )

    return parts


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

    client = get_gemini_client()

    prompt = build_visual_prompt(window)

    contents = [
        prompt,
        *build_image_parts(window),
    ]

    response = client.models.generate_content(
        model=MODEL_ID,
        contents=contents,
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

    return VisualWindowAnalysis.model_validate_json(
        response.text
    )