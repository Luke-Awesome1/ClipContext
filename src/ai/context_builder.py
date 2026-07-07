import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.models.video_context import (
    VideoContext,
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


def format_transcript(
    transcription: dict,
) -> str:
    lines = []

    for segment in transcription["segments"]:
        lines.append(
            (
                f"[{segment['start']:.2f}s"
                f" - "
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

ACTIONS OR VISIBLE CHANGES:
{visual.actions}

IMPORTANT OBJECTS:
{visual.objects}

VISIBLE TEXT:
{visual.visible_text}

SETTING:
{visual.setting}

VISUAL MOOD:
{visual.visual_mood}
""".strip()

        sections.append(section)

    return "\n\n---\n\n".join(sections)


def build_context_prompt(
    transcription: dict,
    visual_timeline: list[dict],
) -> str:
    transcript = format_transcript(
        transcription
    )

    timeline = format_visual_timeline(
        visual_timeline
    )

    return f"""
You are a multimodal video understanding system.

Your task is to build one canonical semantic
representation of a short-form video.

You are given:

1. A timestamped speech transcript.
2. A timestamped visual observation timeline.

The transcript and visual timeline were produced
independently.

You must fuse them carefully.

IMPORTANT EVIDENCE RULES:

- Spoken claims are evidence of what is said.
- Visual observations are evidence of what is shown.
- Do not treat visual mood as proof of creator intent.
- Do not identify people unless identity is explicitly
  established by the supplied evidence.
- Do not invent causal relationships between scenes.
- Do not claim an action happened if the visual evidence
  only suggests it.
- If an interpretation is plausible but not established,
  place it in uncertainties.
- Preserve exact important on-screen text.
- Prefer concrete details over generic abstractions.

TEMPORAL REASONING:

Use timestamps to understand what visual material appears
while particular speech is occurring.

STRICT SPEECH is temporally central to a window.

CONTEXT SPEECH may overlap the window boundary and is
provided only for continuity.

CONTENT TYPE:

Choose a concise category such as:
- motivational edit
- tutorial
- commentary
- comedy
- vlog
- product demonstration
- educational explainer
- gaming clip
- interview
- promotional content

TECHNICAL LEVEL:

Use exactly one of:
- non-technical
- beginner
- intermediate
- advanced

CAPTIONABLE DETAILS:

Extract highly specific details that a strong caption writer
could reference.

Good captionable detail:
"The speech says a dream remains possible while the visuals
shift from distressed indoor scenes to an open mountain
landscape."

Bad captionable detail:
"The video is inspiring."

Good captionable detail:
"On-screen text reads 'this is my ultimate dream' followed
by 'I believe it's yours too'."

Bad captionable detail:
"There is text on screen."

KEY MOMENTS:

Include only moments that materially contribute to the
video's meaning, narrative, humour, demonstration, or
emotional progression.

For significance, explain why the combination of speech
and visuals matters.

TARGET AUDIENCE SIGNALS:

Infer only audience signals supported by content,
terminology, visual style, or presentation.

Do not invent demographic attributes.

TRANSCRIPT:

{transcript}

VISUAL TIMELINE:

{timeline}

Build the canonical VideoContext now.
""".strip()


def build_video_context(
    transcription: dict,
    visual_timeline: list[dict],
) -> VideoContext:
    client = get_gemini_client()

    prompt = build_context_prompt(
        transcription=transcription,
        visual_timeline=visual_timeline,
    )

    response = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type=(
                "application/json"
            ),
            response_schema=VideoContext,
        ),
    )

    if response.parsed is not None:
        return response.parsed

    return VideoContext.model_validate_json(
        response.text
    )