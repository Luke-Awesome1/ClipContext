import json

from pathlib import Path


BUDGET_FILE = Path(
    "outputs/fireworks_budget.json"
)

DEVELOPMENT_BUDGET_USD = 10.0


def load_spend() -> float:
    if not BUDGET_FILE.exists():
        return 0.0

    with open(
        BUDGET_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    return float(
        data.get(
            "estimated_spend_usd",
            0.0,
        )
    )


def record_spend(
    cost_usd: float,
):
    current_spend = load_spend()

    new_spend = (
        current_spend + cost_usd
    )

    BUDGET_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        BUDGET_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            {
                "estimated_spend_usd": (
                    new_spend
                ),
            },
            file,
            indent=2,
        )

    print(
        f"\nEstimated development spend: "
        f"${new_spend:.6f}"
    )

    print(
        f"Development budget remaining: "
        f"${max(DEVELOPMENT_BUDGET_USD - new_spend, 0):.6f}"
    )


def assert_budget_available():
    current_spend = load_spend()

    if (
        current_spend
        >= DEVELOPMENT_BUDGET_USD
    ):
        raise RuntimeError(
            "ClipContext development budget guard "
            "has blocked this Fireworks request. "
            f"Estimated tracked spend: "
            f"${current_spend:.4f}"
        )