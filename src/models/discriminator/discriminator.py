import json
import os
from pathlib import Path
from typing import Any

from src.ai.fireworks.client import MINMAX_ID
from src.ai.providers.orchestrator import run_structured_stage
from src.models.discriminator.schemas import DiscriminatorResult


STAGE = "discriminator"

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
        # Deferred: pandas is only needed here, well after transcription —
        # importing it at module load would add it to every process's
        # boot-time memory footprint regardless of whether this stage is
        # ever reached. See docs/Deployment.md "the real memory constraint".
        import pandas as pd

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


def load_candidate_pools(
    candidates_path: Path,
) -> dict:
    with candidates_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        raw_data = json.load(file)

    return {
        "titles": [
            {"id": item["id"], "text": item["text"]}
            for item in raw_data.get("titles", [])
        ],
        "descriptions": [
            {"id": item["id"], "text": item["text"]}
            for item in raw_data.get("descriptions", [])
        ],
        "hashtags": [
            {"id": item["id"], "tags": item["tags"]}
            for item in raw_data.get("hashtags", [])
        ],
    }


def run_discriminator_audit(
    candidate_pools: dict,
    context_data: dict,
    benchmarks: dict,
) -> tuple[DiscriminatorResult, dict[str, Any]]:
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
        "candidate_pools": candidate_pools,
    }

    result, audit = run_structured_stage(
        stage=STAGE,
        system_prompt=load_system_instruction(),
        user_prompt=(
            "Independently rank each candidate pool below "
            "and return the structured audit matrix:\n\n"
            + json.dumps(evaluation_package, indent=2)
        ),
        schema_model=DiscriminatorResult,
        schema_name="DiscriminatorResult",
        model_by_provider={
            "fireworks": MINMAX_ID,
            "amd_vllm": os.getenv("AMD_VLLM_MODEL"),
        },
        temperature=0.1,
        max_tokens=8000,
        extra_params_by_provider={
            "fireworks": {"extra_body": {"reasoning_effort": "low"}},
        },
    )

    return result, audit


def run_discriminator(
    context_path: Path,
    trends_path: Path,
    candidates_path: Path,
    output_path: Path,
) -> tuple[DiscriminatorResult, dict[str, Any]]:
    context_data, benchmarks = (
        load_validation_payloads(
            context_path=context_path,
            trends_path=trends_path,
        )
    )

    candidate_pools = load_candidate_pools(
        candidates_path=candidates_path
    )

    result, audit = run_discriminator_audit(
        candidate_pools=candidate_pools,
        context_data=context_data,
        benchmarks=benchmarks,
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            result.model_dump(),
            file,
            indent=2,
            ensure_ascii=False,
        )

    print(
        "Discriminator audit created -> "
        f"{output_path}"
    )

    return result, audit
