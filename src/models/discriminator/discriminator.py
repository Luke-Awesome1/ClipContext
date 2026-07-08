import json
from pathlib import Path

import pandas as pd

from src.ai.fireworks.client import (
    MINMAX_ID,
    get_fireworks_client,
)


CURRENT_DIR = Path(__file__).resolve().parent

PROMPT_PATH = (
    CURRENT_DIR
    / "d_prompt.txt"
)


def load_system_instruction() -> str:
    with PROMPT_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return file.read().strip()


def load_validation_payloads(
    context_path: Path,
    trends_path: Path,
) -> tuple[dict, dict]:
    with context_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        context_data = json.load(file)

    try:
        trends_df = pd.read_json(
            trends_path
        )

        top_cluster_id = (
            trends_df
            .groupby("cluster_id")["views"]
            .mean()
            .idxmax()
        )

        top_cluster = trends_df[
            trends_df["cluster_id"]
            == top_cluster_id
        ]

        sample_tags = []

        for tags in top_cluster[
            "extracted_hashtags"
        ].head(3):
            sample_tags.extend(
                tags
            )

        benchmarks = {
            "avg_views": float(
                top_cluster["views"].mean()
            ),
            "target_like_ratio": float(
                top_cluster[
                    "like_ratio"
                ].mean()
            ),
            "sample_titles": (
                top_cluster[
                    "clean_title"
                ]
                .head(3)
                .tolist()
            ),
            "sample_tags": list(
                set(sample_tags)
            ),
        }

    except Exception as exc:
        print(
            "Performance metrics reference "
            f"error ({exc}). "
            "Using fallback benchmarks."
        )

        benchmarks = {
            "avg_views": 500000,
            "target_like_ratio": 0.05,
            "sample_titles": [
                "Trending Reference Title"
            ],
            "sample_tags": [
                "#shorts",
                "#trending",
            ],
        }

    return (
        context_data,
        benchmarks,
    )


def load_generator_candidates(
    candidates_path: Path,
) -> list:
    with candidates_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        raw_data = json.load(file)

    titles = {
        item["id"]: item["text"]
        for item in raw_data.get(
            "titles",
            [],
        )
    }

    descriptions = {
        item["id"]: item["text"]
        for item in raw_data.get(
            "descriptions",
            [],
        )
    }

    hashtags = {
        item["id"]: item["tags"]
        for item in raw_data.get(
            "hashtags",
            [],
        )
    }

    all_ids = (
        set(titles)
        | set(descriptions)
        | set(hashtags)
    )

    candidates = []

    for candidate_id in sorted(
        all_ids
    ):
        candidates.append(
            {
                "candidate_id": candidate_id,
                "title": titles.get(
                    candidate_id,
                    "",
                ),
                "description": (
                    descriptions.get(
                        candidate_id,
                        "",
                    )
                ),
                "hashtags": hashtags.get(
                    candidate_id,
                    [],
                ),
            }
        )

    return candidates


def run_discriminator_audit(
    candidates_list: list,
    context_data: dict,
    benchmarks: dict,
) -> str:
    client = get_fireworks_client()

    video_truth_digest = {
        "topic": context_data.get(
            "topic",
            "",
        ),
        "core_message": context_data.get(
            "core_message",
            "",
        ),
        "multimodal_summary": context_data.get(
            "multimodal_summary",
            "",
        ),
        "key_entities": context_data.get(
            "key_entities",
            [],
        ),
        "visible_text": context_data.get(
            "visible_text",
            [],
        ),
    }

    evaluation_package = {
        "ground_truth_video_context": (
            video_truth_digest
        ),
        "historical_performance_benchmarks": (
            benchmarks
        ),
        "candidates_to_evaluate": (
            candidates_list
        ),
    }

    response = client.chat.completions.create(
        model=MINMAX_ID,
        messages=[
            {
                "role": "system",
                "content": (
                    load_system_instruction()
                ),
            },
            {
                "role": "user",
                "content": (
                    "Analyze this payload and return "
                    "the structured audit matrix:\n\n"
                    + json.dumps(
                        evaluation_package,
                        indent=2,
                    )
                ),
            },
        ],
        temperature=0.1,
        response_format={
            "type": "json_object"
        },
        extra_body={
            "reasoning_effort": "low"
        },
    )

    if not response.choices:
        raise RuntimeError(
            "Discriminator returned no choices"
        )

    raw_content = (
        response
        .choices[0]
        .message
        .content
    )

    if not raw_content:
        raise RuntimeError(
            "Discriminator returned empty content"
        )

    return raw_content


def run_discriminator(
    context_path: Path,
    trends_path: Path,
    candidates_path: Path,
    output_path: Path,
) -> dict:
    context_data, benchmarks = (
        load_validation_payloads(
            context_path=context_path,
            trends_path=trends_path,
        )
    )

    candidates = load_generator_candidates(
        candidates_path=candidates_path
    )

    raw_report = run_discriminator_audit(
        candidates_list=candidates,
        context_data=context_data,
        benchmarks=benchmarks,
    )

    try:
        audit_report = json.loads(
            raw_report
        )

    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Discriminator returned invalid JSON"
        ) from exc

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            audit_report,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print(
        "Discriminator audit created -> "
        f"{output_path}"
    )

    return audit_report