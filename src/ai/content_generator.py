import json
import os
from pathlib import Path
from typing import Any

from src.ai.providers.orchestrator import run_structured_stage
from src.models.generated_content import GeneratedContent
from src.prompts.content_generation import (
    CONTENT_GENERATION_SYSTEM_PROMPT,
)


DEFAULT_MODEL = "accounts/fireworks/routers/kimi-k2p6-turbo"

STAGE = "content_generation"


def load_json(path: Path) -> dict[str, Any]:
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def build_generation_prompt(
    video_context: dict[str, Any],
    platform_syntax: dict[str, Any],
) -> str:
    return f"""
VIDEO_CONTEXT

{json.dumps(
    video_context,
    indent=2,
    ensure_ascii=False,
)}

PLATFORM_SYNTAX

{json.dumps(
    platform_syntax,
    indent=2,
    ensure_ascii=False,
)}

Generate the full candidate set now: 10 titles (one per strategic lane, in
lane order 1-10), 10 descriptions (one per format, in format order 1-10),
and 10 hashtag sets (one per strategy, in strategy order 1-10).

Ground every candidate in the VIDEO_CONTEXT fields above — use
key_moments, visible_text, key_entities, and target_audience_signals
wherever they add real specificity, not just topic and core_message.

Return only the JSON object required by the schema. No markdown fences, no
preamble, no explanation.
""".strip()


def generate_content(
    video_context_path: Path,
    syntax_path: Path,
    model: str = DEFAULT_MODEL,
) -> tuple[GeneratedContent, dict[str, Any]]:
    """Returns (GeneratedContent, stage_audit_dict).

    stage_audit_dict records which AI provider actually handled this call
    (see src/ai/providers/orchestrator.py) — fireworks by default, or
    amd_vllm when CONTENT_GENERATION_PROVIDER=amd_vllm is configured, with
    truthful fallback if the configured provider is unreachable or returns
    unusable output.
    """
    video_context = load_json(
        video_context_path
    )

    platform_syntax = load_json(
        syntax_path
    )

    generated_content, audit = run_structured_stage(
        stage=STAGE,
        system_prompt=CONTENT_GENERATION_SYSTEM_PROMPT,
        user_prompt=build_generation_prompt(
            video_context=video_context,
            platform_syntax=platform_syntax,
        ),
        schema_model=GeneratedContent,
        schema_name="GeneratedContent",
        model_by_provider={
            "fireworks": model,
            "amd_vllm": os.getenv("AMD_VLLM_MODEL"),
        },
        temperature=0.8,
        max_tokens=6000,
        extra_params_by_provider={
            "fireworks": {"reasoning_effort": "none"},
        },
    )

    return generated_content, audit


def save_generated_content(
    generated_content: GeneratedContent,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            generated_content.model_dump(),
            file,
            indent=2,
            ensure_ascii=False,
        )