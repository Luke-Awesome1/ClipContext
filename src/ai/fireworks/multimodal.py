import base64
import json
import time

from json_repair import repair_json
from openai import APIStatusError

from src.ai.fireworks.client import (
    MODEL_ID,
    get_fireworks_client,
)

from src.models.visual_window import (
    VisualWindowAnalysis,
)


MAX_OUTPUT_TOKENS = 500


def encode_image(
    image_path: str,
) -> str:
    with open(
        image_path,
        "rb",
    ) as image_file:
        encoded = base64.b64encode(
            image_file.read()
        ).decode("utf-8")

    return (
        "data:image/jpeg;base64,"
        + encoded
    )


def extract_json(
    raw_text: str,
) -> dict:
    text = raw_text.strip()

    if text.startswith("```"):
        lines = text.splitlines()

        if lines:
            lines = lines[1:]

        if (
            lines
            and lines[-1].strip() == "```"
        ):
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    start = text.find("{")
    end = text.rfind("}")

    if (
        start == -1
        or end == -1
        or end < start
    ):
        raise ValueError(
            "Kimi returned no JSON object.\n\n"
            f"RAW OUTPUT:\n{raw_text}"
        )

    json_text = text[start:end + 1]

    try:
        return json.loads(
            json_text
        )

    except json.JSONDecodeError as error:
        print(
            "\nKimi returned malformed JSON."
        )

        print(
            "Attempting local JSON repair..."
        )

        print(
            "Original JSON error: "
            f"{error}"
        )

        repaired = repair_json(
            json_text,
            return_objects=True,
        )

        if not isinstance(
            repaired,
            dict,
        ):
            raise ValueError(
                "JSON repair did not produce "
                "a JSON object.\n\n"
                f"RAW OUTPUT:\n{raw_text}"
            )

        print(
            "Local JSON repair successful."
        )

        return repaired
def build_visual_content(
    window: dict,
) -> list[dict]:
    content = []

    timestamps = [
        frame["timestamp"]
        for frame in window["frames"]
    ]

    prompt = f"""
Extract visual facts from the supplied video frames.

Window:
{window["start_time"]:.2f}s to {window["end_time"]:.2f}s

Frame timestamps:
{timestamps}

Images are chronological.

Rules:
- Describe only visible evidence.
- Do not infer speech.
- Do not infer intention.
- Do not identify people unless visibly established.
- Do not invent events between frames.
- Preserve clearly readable text exactly.
- Keep every field concise.
- Output JSON immediately.
- Do not explain your reasoning.
- Do not describe the task.
- Do not include Markdown.

Return exactly:

{{
  "description": "visible progression across frames",
  "subjects": ["visible focal subject"],
  "actions": ["visible action or scene change"],
  "objects": ["important visible object"],
  "visible_text": ["exact readable text"],
  "setting": "visible environment",
  "visual_mood": "mood supported by visual presentation"
}}
""".strip()

    content.append(
        {
            "type": "text",
            "text": prompt,
        }
    )

    for frame in window["frames"]:
        content.append(
            {
                "type": "text",
                "text": (
                    "Timestamp: "
                    f"{frame['timestamp']:.2f}s"
                ),
            }
        )

        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": encode_image(
                        frame["path"]
                    ),
                },
            }
        )

    return content


def analyse_visual_window(
    window: dict,
) -> tuple[
    VisualWindowAnalysis,
    dict,
]:
    if not window["frames"]:
        analysis = VisualWindowAnalysis(
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

        return analysis, {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "latency_seconds": 0.0,
        }

    client = get_fireworks_client()

    content = build_visual_content(
        window
    )

    start = time.perf_counter()

    try:
        response = client.chat.completions.create(
            model=MODEL_ID,
            messages=[
                {
                    "role": "user",
                    "content": content,
                }
            ],
            temperature=0.0,
            max_tokens=MAX_OUTPUT_TOKENS,
            reasoning_effort="none",
        )

    except APIStatusError as error:
        print(
            "\nFIREWORKS VISUAL REQUEST FAILED"
        )

        print(
            f"Status: {error.status_code}"
        )

        print(
            "Request ID: "
            f"{getattr(error, 'request_id', None)}"
        )

        print(
            "Window: "
            f"{window['start_time']:.2f}s - "
            f"{window['end_time']:.2f}s"
        )

        print(
            "Images: "
            f"{len(window['frames'])}"
        )

        raise

    latency = (
        time.perf_counter() - start
    )

    raw_output = (
        response.choices[0].message.content
        or ""
    )

    parsed = extract_json(
        raw_output
    )

    analysis = (
        VisualWindowAnalysis.model_validate(
            parsed
        )
    )

    usage = {
        "prompt_tokens": (
            response.usage.prompt_tokens
            if response.usage
            else 0
        ),
        "completion_tokens": (
            response.usage.completion_tokens
            if response.usage
            else 0
        ),
        "latency_seconds": latency,
    }

    return analysis, usage