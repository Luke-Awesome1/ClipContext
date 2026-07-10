"""Representative ClipContext AMD benchmark.

Not a synthetic throughput benchmark: this runs the actual content-
generation stage's system prompt, prompt builder, and Pydantic schema
(src/ai/content_generator.py, src/models/generated_content.py) against
AMD_VLLM_BASE_URL directly, using a small fixture VideoContext + syntax
blueprint in place of a real pipeline run, and reports real latency/token/
validation numbers. Token-per-second is only reported when the vLLM server
actually returns usage metadata — never fabricated.

Usage:
    AMD_VLLM_BASE_URL=http://<notebook-host>:8000/v1 \\
    AMD_VLLM_MODEL=<model-id> \\
    python amd/benchmark_amd.py
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ai.content_generator import build_generation_prompt  # noqa: E402
from src.ai.providers.amd_vllm import AmdVllmProvider  # noqa: E402
from src.models.generated_content import GeneratedContent  # noqa: E402
from src.prompts.content_generation import (  # noqa: E402
    CONTENT_GENERATION_SYSTEM_PROMPT,
)

FIXTURE_VIDEO_CONTEXT = {
    "topic": "AMD hackathon team demoing a video-analysis product",
    "content_type": "tech demo",
    "multimodal_summary": (
        "Two developers point a laptop camera at objects — a chessboard, a "
        "flag, a wall clock — while narrating a live test of their video "
        "understanding pipeline."
    ),
    "core_message": (
        "The team is stress-testing their own AI pipeline on camera, "
        "including its failure modes."
    ),
}

FIXTURE_SYNTAX = {
    "syntax_blueprint": {
        "titles": ["question-based hook", "specific-object callout"],
        "descriptions": ["direct summary + call to action"],
        "hashtags": ["broad + niche mix"],
    },
    "seo_vocabulary": ["AI", "hackathon", "demo", "computer vision"],
    "adjectives": ["real-time", "live"],
}


def main() -> None:
    provider = AmdVllmProvider()

    if not provider.is_configured():
        print(
            "AMD_VLLM_BASE_URL and/or AMD_VLLM_MODEL are not set — nothing to "
            "benchmark. This script does not fabricate a result.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    model = provider.model()
    prompt = build_generation_prompt(
        video_context=FIXTURE_VIDEO_CONTEXT, platform_syntax=FIXTURE_SYNTAX
    )
    schema = GeneratedContent.model_json_schema()

    print(f"Benchmarking AMD vLLM: model={model}")
    print(
        "Prompt length (chars): "
        f"system={len(CONTENT_GENERATION_SYSTEM_PROMPT)} user={len(prompt)}"
    )

    success = False
    validation_ok = False
    prompt_tokens = None
    completion_tokens = None
    error = None

    start = time.monotonic()

    try:
        result = provider.chat_completion(
            messages=[
                {"role": "system", "content": CONTENT_GENERATION_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            model=model,
            json_schema=schema,
            json_schema_name="GeneratedContent",
            temperature=0.8,
            max_tokens=6000,
        )
        success = True
        prompt_tokens = result.prompt_tokens
        completion_tokens = result.completion_tokens

        try:
            GeneratedContent.model_validate_json(result.content)
            validation_ok = True
        except Exception as exc:  # noqa: BLE001 - reported in the report, not raised
            error = f"schema validation failed: {exc}"
    except Exception as exc:  # noqa: BLE001 - reported in the report, not raised
        error = str(exc)

    latency_ms = (time.monotonic() - start) * 1000

    tokens_per_second = None
    if success and completion_tokens and latency_ms > 0:
        tokens_per_second = round(completion_tokens / (latency_ms / 1000), 1)

    report = {
        "provider": "amd_vllm",
        "model": model,
        "stage": "content_generation (representative fixture)",
        "success": success,
        "structured_output_valid": validation_ok,
        "latency_ms": round(latency_ms, 1),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "tokens_per_second": tokens_per_second,
        "error": error,
    }

    print("\n" + json.dumps(report, indent=2))

    if not success or not validation_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
