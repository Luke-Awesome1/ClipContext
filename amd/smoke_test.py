"""Smoke test for the AMD vLLM OpenAI-compatible server: confirms a plain
chat completion AND a ClipContext-shaped structured JSON request both work,
before pointing the real backend at it.

Run from the repo's normal Python environment (the same one that runs the
FastAPI backend) — it does not need to run on the AMD notebook itself, only
reach it over the network:

    AMD_VLLM_BASE_URL=http://<notebook-host>:8000/v1 \\
    AMD_VLLM_MODEL=<model-id> \\
    python amd/smoke_test.py
"""

import json
import os
import sys
import time

from openai import OpenAI

_WIDGET_SCHEMA = {
    "type": "object",
    "properties": {
        "greeting": {"type": "string"},
        "count": {"type": "integer"},
    },
    "required": ["greeting", "count"],
}


def main() -> None:
    base_url = os.getenv("AMD_VLLM_BASE_URL")
    model = os.getenv("AMD_VLLM_MODEL")
    api_key = os.getenv("AMD_VLLM_API_KEY") or "unset"

    if not base_url or not model:
        print(
            "Set AMD_VLLM_BASE_URL and AMD_VLLM_MODEL before running this script.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    client = OpenAI(api_key=api_key, base_url=base_url, timeout=60.0, max_retries=0)

    print(f"Target: {base_url}  model={model}")

    print("\n--- 1. Plain chat completion ---")
    start = time.monotonic()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Reply with exactly the word: pong"}],
        max_tokens=16,
        temperature=0,
    )
    latency_ms = (time.monotonic() - start) * 1000
    content = response.choices[0].message.content
    print(f"latency_ms={latency_ms:.1f} content={content!r}")

    if not content:
        print("FAILED: empty response from AMD vLLM", file=sys.stderr)
        raise SystemExit(1)

    print("\n--- 2. Structured JSON completion ---")
    start = time.monotonic()
    response_format_used = "json_schema"

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Return JSON matching this schema exactly: "
                        f"{json.dumps(_WIDGET_SCHEMA)}. "
                        'Use greeting="hello" and count=3.'
                    ),
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "Widget", "schema": _WIDGET_SCHEMA},
            },
            max_tokens=64,
            temperature=0,
        )
    except Exception as exc:
        print(f"json_schema response_format rejected ({exc}); retrying with json_object")
        response_format_used = "json_object"
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Return ONLY JSON, no prose, matching this shape: "
                        f"{json.dumps(_WIDGET_SCHEMA)}. "
                        'Use greeting="hello" and count=3.'
                    ),
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=64,
            temperature=0,
        )

    latency_ms = (time.monotonic() - start) * 1000
    content = response.choices[0].message.content
    print(f"response_format={response_format_used} latency_ms={latency_ms:.1f} content={content!r}")

    parsed = json.loads(content)

    if "greeting" not in parsed or "count" not in parsed:
        print(f"FAILED: unexpected JSON shape: {parsed}", file=sys.stderr)
        raise SystemExit(1)

    print(
        "\nSMOKE TEST PASSED — AMD vLLM is reachable and returns usable "
        f"structured output via response_format={response_format_used}."
    )
    print(
        "Record this response_format value: src/ai/providers/amd_vllm.py "
        "already tries json_schema first and falls back automatically, but "
        "knowing which one this model/vLLM build actually supports is "
        "useful for the technical writeup."
    )


if __name__ == "__main__":
    main()
