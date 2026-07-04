import base64
import json
import os

from openai import OpenAI
from dotenv import load_dotenv

from src.models.visual_analysis import (
    VisualAnalysis,
)


load_dotenv()


VISION_MODEL = (
    "accounts/fireworks/models/"
    "qwen2p5-vl-32b-instruct"
)


def get_fireworks_client() -> OpenAI:
    api_key = os.getenv(
        "FIREWORKS_API_KEY"
    )

    if not api_key:
        raise ValueError(
            "FIREWORKS_API_KEY is not set."
        )

    return OpenAI(
        api_key=api_key,
        base_url=(
            "https://api.fireworks.ai/"
            "inference/v1"
        ),
    )


def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        encoded = base64.b64encode(
            image_file.read()
        ).decode("utf-8")

    return (
        f"data:image/jpeg;base64,{encoded}"
    )


def build_vision_content(
    frames: list[dict],
) -> list[dict]:
    content = [
        {
            "type": "text",
            "text": (
                "You are analysing frames sampled "
                "from a video in chronological order.\n\n"
                "The frames are provided with explicit "
                "timestamps.\n\n"
                "Reconstruct the visual timeline of the "
                "video using only visible evidence.\n\n"
                "Important rules:\n"
                "- Do not infer spoken dialogue.\n"
                "- Do not invent actions between frames.\n"
                "- Treat timestamps as chronological.\n"
                "- Extract important visible on-screen text.\n"
                "- Identify changes in setting, subject, "
                "screen content, objects, and actions.\n"
                "- Merge adjacent frames into coherent "
                "visual events when justified.\n"
                "- Be concrete and specific.\n"
            ),
        }
    ]

    for frame in frames:
        timestamp = frame["timestamp"]

        content.append(
            {
                "type": "text",
                "text": (
                    f"\nFRAME TIMESTAMP: "
                    f"{timestamp:.2f} seconds"
                ),
            }
        )

        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": encode_image(
                        frame["path"]
                    )
                },
            }
        )

    return content


def analyse_visual_timeline(
    frames: list[dict],
) -> VisualAnalysis:
    client = get_fireworks_client()

    content = build_vision_content(frames)

    schema = VisualAnalysis.model_json_schema()

    response = client.chat.completions.create(
        model=VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": content,
            }
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "visual_analysis",
                "schema": schema,
            },
        },
        temperature=0.1,
        max_tokens=2000,
    )

    raw_content = (
        response
        .choices[0]
        .message
        .content
    )

    parsed = json.loads(raw_content)

    return VisualAnalysis.model_validate(
        parsed
    )