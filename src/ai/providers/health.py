"""Safe-to-expose AI provider status.

Backs GET /api/providers/status. Never includes API keys, tokens, base
URLs, or raw exception text — only provider name, configured/reachable
booleans, model id, and a coarse error category. Kept separate from
GET /health (which hosting platforms poll frequently for liveness) because
checking AMD vLLM reachability makes a live network call.
"""

from typing import Any

from src.ai.providers.registry import get_provider, get_stage_providers

STAGES = ("content_generation", "discriminator")


def get_ai_provider_status() -> dict[str, Any]:
    stages: dict[str, Any] = {}
    provider_health: dict[str, Any] = {}
    seen: set[str] = set()

    for stage in STAGES:
        primary, fallback = get_stage_providers(stage)
        stage_providers = [primary] + ([fallback] if fallback else [])

        for name in stage_providers:
            if name in seen:
                continue

            seen.add(name)

            try:
                provider = get_provider(name)
                provider_health[name] = provider.health_check()
            except ValueError:
                provider_health[name] = {"configured": False, "reachable": False}

        stages[stage] = {
            "provider_requested": primary,
            "fallback_provider": fallback,
        }

    return {"stages": stages, "providers": provider_health}
