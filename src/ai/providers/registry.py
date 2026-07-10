"""Provider lookup and per-stage provider selection.

Selection is environment-driven so a stage can be pointed at AMD vLLM
without any code change:

    CONTENT_GENERATION_PROVIDER=amd_vllm
    CONTENT_GENERATION_FALLBACK_PROVIDER=fireworks
    DISCRIMINATOR_PROVIDER=amd_vllm
    DISCRIMINATOR_FALLBACK_PROVIDER=fireworks

Both default to "fireworks" (the existing, already-validated provider) with
no fallback, so unset environment reproduces today's behavior exactly.
"""

import os

from src.ai.providers.amd_vllm import AmdVllmProvider
from src.ai.providers.base import AIProvider
from src.ai.providers.fireworks_provider import FireworksProvider

_STAGE_ENV_PREFIX = {
    "content_generation": "CONTENT_GENERATION",
    "discriminator": "DISCRIMINATOR",
}

_providers: dict[str, AIProvider] = {}


def get_provider(name: str) -> AIProvider:
    key = name.strip().lower()

    if key not in _providers:
        if key == "fireworks":
            _providers[key] = FireworksProvider()
        elif key == "amd_vllm":
            _providers[key] = AmdVllmProvider()
        else:
            raise ValueError(f"Unknown AI provider: {name}")

    return _providers[key]


def get_stage_providers(stage: str) -> tuple[str, str | None]:
    """Returns (primary_provider_name, fallback_provider_name_or_None)."""
    prefix = _STAGE_ENV_PREFIX.get(stage)

    if prefix is None:
        raise ValueError(f"Unknown AI stage: {stage}")

    primary = os.getenv(f"{prefix}_PROVIDER", "fireworks").strip().lower()
    fallback_default = "fireworks" if primary != "fireworks" else ""
    fallback = os.getenv(f"{prefix}_FALLBACK_PROVIDER", fallback_default).strip().lower()

    return primary, (fallback or None)
