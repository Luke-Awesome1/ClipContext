import json
from pathlib import Path
from typing import Any

from src.ai.fireworks.client import get_fireworks_client
from src.models.generated_content import GeneratedContent
from src.prompts.content_generation import (
    CONTENT_GENERATION_SYSTEM_PROMPT,
)


DEFAULT_MODEL = "accounts/fireworks/routers/kimi-k2p6-turbo"


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

Generate exactly:

- 10 titles
- 10 descriptions
- 10 hashtag sets

Produce the final candidates directly.

Return only the JSON object required by the schema.
""".strip()


def generate_content(
    video_context_path: Path,
    syntax_path: Path,
    model: str = DEFAULT_MODEL,
) -> GeneratedContent:
    video_context = load_json(
        video_context_path
    )

    platform_syntax = load_json(
        syntax_path
    )

    client = get_fireworks_client()

    json_schema = (
        GeneratedContent.model_json_schema()
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    CONTENT_GENERATION_SYSTEM_PROMPT
                ),
            },
            {
                "role": "user",
                "content": build_generation_prompt(
                    video_context=video_context,
                    platform_syntax=(
                        platform_syntax
                    ),
                ),
            },
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "GeneratedContent",
                "schema": json_schema,
            },
        },
        reasoning_effort="none",
        temperature=0.8,
        max_tokens=6000,
    )

    choice = response.choices[0]
    message = choice.message

    raw_content = message.content

    if not raw_content:
        reasoning_content = getattr(
            message,
            "reasoning_content",
            None,
        )

        print(
            "\n"
            "--- FIREWORKS EMPTY CONTENT DEBUG ---"
        )

        print(
            f"finish_reason: "
            f"{choice.finish_reason}"
        )

        print(
            f"reasoning_content: "
            f"{reasoning_content}"
        )

        print(
            "--- END DEBUG ---"
            "\n"
        )

        raise RuntimeError(
            "Fireworks returned empty content "
            "for content generation"
        )

    if choice.finish_reason == "length":
        print(
            "\n"
            "--- FIREWORKS TRUNCATED CONTENT ---"
        )

        print(
            raw_content
        )

        print(
            "--- END TRUNCATED CONTENT ---"
            "\n"
        )

        raise RuntimeError(
            "Fireworks content generation "
            "response was truncated."
        )

    try:
        generated_content = (
            GeneratedContent.model_validate_json(
                raw_content
            )
        )

    except Exception as exc:
        print(
            "\n"
            "--- FIREWORKS RAW CONTENT START ---"
        )

        print(
            raw_content
        )

        print(
            "--- FIREWORKS RAW CONTENT END ---"
            "\n"
        )

        reasoning_content = getattr(
            message,
            "reasoning_content",
            None,
        )

        if reasoning_content:
            print(
                "\n"
                "--- FIREWORKS REASONING START ---"
            )

            print(
                reasoning_content
            )

            print(
                "--- FIREWORKS REASONING END ---"
                "\n"
            )

        raise RuntimeError(
            "Fireworks returned content that "
            "could not be validated as "
            "GeneratedContent"
        ) from exc

    return generated_content


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