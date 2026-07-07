from dataclasses import dataclass


KIMI_INPUT_COST_PER_MILLION = 0.60
KIMI_CACHED_INPUT_COST_PER_MILLION = 0.10
KIMI_OUTPUT_COST_PER_MILLION = 3.00


@dataclass
class InferenceUsage:
    prompt_tokens: int
    completion_tokens: int
    cached_tokens: int = 0

    @property
    def uncached_prompt_tokens(self) -> int:
        return max(
            self.prompt_tokens - self.cached_tokens,
            0,
        )

    @property
    def estimated_cost_usd(self) -> float:
        uncached_input_cost = (
            self.uncached_prompt_tokens
            / 1_000_000
            * KIMI_INPUT_COST_PER_MILLION
        )

        cached_input_cost = (
            self.cached_tokens
            / 1_000_000
            * KIMI_CACHED_INPUT_COST_PER_MILLION
        )

        output_cost = (
            self.completion_tokens
            / 1_000_000
            * KIMI_OUTPUT_COST_PER_MILLION
        )

        return (
            uncached_input_cost
            + cached_input_cost
            + output_cost
        )


def print_usage(
    usage: InferenceUsage,
    latency_seconds: float,
):
    print("\nFIREWORKS INFERENCE METRICS")
    print("-" * 40)

    print(
        f"Prompt tokens:     "
        f"{usage.prompt_tokens:,}"
    )

    print(
        f"Cached tokens:     "
        f"{usage.cached_tokens:,}"
    )

    print(
        f"Completion tokens: "
        f"{usage.completion_tokens:,}"
    )

    print(
        f"Latency:           "
        f"{latency_seconds:.2f}s"
    )

    print(
        f"Estimated cost:    "
        f"${usage.estimated_cost_usd:.6f}"
    )

    print("-" * 40)