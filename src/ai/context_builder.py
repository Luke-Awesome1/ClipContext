import json
from secrets import choice
import time

from json_repair import repair_json

from openai import APIStatusError

from src.ai.fireworks.client import (
    MODEL_ID,
    get_fireworks_client,
)

from src.models.video_context import (
    VideoContext,
)


MAX_OUTPUT_TOKENS = 3000


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

def format_transcript(
    transcription: dict,
) -> str:
    lines = []

    for segment in transcription["segments"]:
        lines.append(
            (
                f"[{segment['start']:.2f}s - "
                f"{segment['end']:.2f}s] "
                f"{segment['text']}"
            )
        )

    return "\n".join(lines)


def format_visual_timeline(
    visual_timeline: list[dict],
) -> str:
    sections = []

    for event in visual_timeline:
        visual = event["visual_analysis"]

        section = f"""
TIME WINDOW:
{event["start_time"]:.2f}s -
{event["end_time"]:.2f}s

STRICT SPEECH:
{event["strict_spoken_text"] or "[NO SPEECH]"}

CONTEXT SPEECH:
{event["context_spoken_text"] or "[NO SPEECH]"}

VISUAL DESCRIPTION:
{visual.description}

SUBJECTS:
{visual.subjects}

ACTIONS:
{visual.actions}

OBJECTS:
{visual.objects}

VISIBLE TEXT:
{visual.visible_text}

SETTING:
{visual.setting}

VISUAL MOOD:
{visual.visual_mood}
""".strip()

        sections.append(section)

    return "\n\n---\n\n".join(
        sections
    )


def build_video_context(
    transcription: dict,
    visual_timeline: list[dict],
) -> tuple[
    VideoContext,
    dict,
]:
    client = get_fireworks_client()

    transcript = format_transcript(
        transcription
    )

    visual_timeline_text = (
        format_visual_timeline(
            visual_timeline
        )
    )

    prompt = f"""
You are the semantic fusion layer of ClipContext.

ClipContext analyses short-form creator videos.

You receive:

1. A timestamped speech transcript.
2. Timestamped visual observations.

Build one canonical semantic representation of the video.

You are NOT writing a caption yet.

EVIDENCE RULES:

- Speech is evidence of what is said.
- Visual observations are evidence of what is shown.
- Use timestamps to align speech and visuals.
- Do not identify people unless identity is established.
- Do not invent causal relationships.
- Do not convert visual symbolism into literal fact.
- Do not claim an outcome occurred unless shown or stated.
- Preserve important readable on-screen text exactly.
- Put plausible but unestablished interpretations in
  uncertainties.
- Prefer concrete details over generic abstractions.

DOWNSTREAM USE:

This representation is the only evidence a copywriter will see
when later writing titles, descriptions, and hashtags — they
will not re-read the transcript or re-watch the video. Any
specific, vivid, or hook-worthy detail you leave out is
permanently unavailable to them. Any vague summary you write
instead of a specific one directly produces vague, generic
titles downstream.

CAPTIONABLE DETAILS:

These are specific evidence-grounded details a downstream
caption writer can use directly as a hook. Prioritize details
that are concrete, unexpected, numeric, or emotionally charged
over ones that merely restate the topic. Aim for at least
3-5 entries when the evidence supports it — a copywriter needs
raw material to choose from, not one polished summary.

Good:
"The speech says a dream remains possible while the visuals
move from distressed indoor scenes to an open mountain
landscape."

Bad:
"The video is inspirational."

Good:
"On-screen text reads 'this is my ultimate dream' followed
by 'I believe it's yours too'."

Bad:
"The video contains motivational text."

TARGET AUDIENCE SIGNALS:

Name the audience as specifically as the evidence allows (e.g.
"beginner home cooks on a budget", not "general viewers").
Base this only on tone, vocabulary, technical depth, and
subject matter actually present in the transcript or visuals —
never guess demographics with no evidentiary basis.

EMOTIONAL ARC:

Describe a specific progression across the video, not a single
static mood (e.g. "curiosity, then mounting tension, then
relief" rather than just "emotional"). If the evidence only
supports a single flat tone, say so plainly instead of
inventing movement that isn't there.

TECHNICAL LEVEL:

Use exactly one of:

- non-technical
- beginner
- intermediate
- advanced

TRANSCRIPT:

{transcript}

VISUAL TIMELINE:

{visual_timeline_text}

Return JSON only.

Return exactly this structure:

{{
  "topic": "concise primary topic",
  "content_type": "concise content category",
  "core_message": "central message supported by evidence",
  "transcript_summary": "summary of spoken content",
  "visual_summary": "summary of visual content",
  "multimodal_summary": "how speech and visuals work together",
  "key_moments": [
    {{
      "start_time": 0.0,
      "end_time": 5.0,
      "spoken_content": "relevant speech or empty string",
      "visual_content": "specific visual evidence",
      "significance": "why this moment matters"
    }}
  ],
  "key_entities": [
    "important evidenced subject or concept"
  ],
  "visible_text": [
    "exact important readable text"
  ],
  "emotional_arc": "specific progression, e.g. curiosity -> tension -> relief",
  "visual_style": "specific visual presentation style",
  "technical_level": "non-technical",
  "target_audience_signals": [
    "specific content-supported audience, not a generic label"
  ],
  "captionable_details": [
    "specific, vivid, evidence-grounded detail a copywriter can use as a hook"
  ],
  "uncertainties": [
    "plausible interpretation not established"
  ]
}}
""".strip()

    start = time.perf_counter()

    try:
        response = client.chat.completions.create(
            model=MODEL_ID,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        temperature=0.0,
        max_tokens=MAX_OUTPUT_TOKENS,
        reasoning_effort="none",
    )

    except APIStatusError as error:
        print(
            "\nFIREWORKS CONTEXT REQUEST FAILED"
        )

        print(
            f"Status: {error.status_code}"
        )

        print(
            "Request ID: "
            f"{getattr(error, 'request_id', None)}"
        )

        raise

    latency = (
        time.perf_counter() - start
    )

    choice = response.choices[0]

    raw_output = (
    choice.message.content
    or ""
)

    if choice.finish_reason == "length":
        raise RuntimeError(
        "Kimi context output was truncated "
        "because max_tokens was reached. "
        f"Current limit: {MAX_OUTPUT_TOKENS}. "
        "Increase MAX_OUTPUT_TOKENS."
    )

    parsed = extract_json(
        raw_output
    )

    context = VideoContext.model_validate(
        parsed
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

    return context, usage