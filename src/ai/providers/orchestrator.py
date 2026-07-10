"""Runs one structured-output AI stage against its configured provider(s),
with a bounded repair retry for invalid JSON and truthful fallback + audit
metadata.

This is the one place that knows how to turn (system prompt, user prompt,
Pydantic schema) into a validated model instance, regardless of whether the
provider is Fireworks or AMD vLLM. src/ai/content_generator.py and
src/models/discriminator/discriminator.py both call run_structured_stage()
instead of talking to an OpenAI-compatible client directly.
"""

import logging
import re
from dataclasses import asdict, dataclass
from typing import Any, Optional, TypeVar

from pydantic import BaseModel, ValidationError

from src.ai.providers.base import (
    CompletionResult,
    ProviderResponseError,
    ProviderUnavailableError,
)
from src.ai.providers.registry import get_provider, get_stage_providers

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```\s*$", re.MULTILINE)

_HARDWARE_LABEL = {
    "amd_vllm": "AMD GPU via ROCm/vLLM",
    "fireworks": "Fireworks-hosted inference",
}

MAX_REPAIR_ATTEMPTS = 1


class StageExecutionError(RuntimeError):
    """Raised when every configured provider failed for a stage."""


def strip_code_fences(text: str) -> str:
    """Bounded, deterministic normalization only — never parses prose as
    JSON. Some OpenAI-compatible servers (including some vLLM/model
    combinations) wrap structured output in a ```json fence despite
    response_format instructions.
    """
    stripped = text.strip()

    if stripped.startswith("```"):
        stripped = _CODE_FENCE_RE.sub("", stripped).strip()

    return stripped


@dataclass
class StageAudit:
    stage: str
    provider_requested: str
    provider_used: Optional[str]
    model: Optional[str]
    hardware: Optional[str]
    latency_ms: Optional[float]
    fallback_used: bool
    fallback_reason: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _attempt_provider(
    provider_name: str,
    *,
    messages: list[dict[str, Any]],
    model: str,
    schema_model: type[T],
    schema_name: str,
    temperature: float,
    max_tokens: int,
    extra_params: Optional[dict[str, Any]],
) -> tuple[T, CompletionResult]:
    provider = get_provider(provider_name)
    json_schema = schema_model.model_json_schema()
    current_messages = list(messages)
    last_error: Exception = ProviderResponseError("no attempt made")

    for attempt in range(MAX_REPAIR_ATTEMPTS + 1):
        result = provider.chat_completion(
            messages=current_messages,
            model=model,
            json_schema=json_schema,
            json_schema_name=schema_name,
            temperature=temperature,
            max_tokens=max_tokens,
            extra_params=extra_params,
        )

        cleaned = strip_code_fences(result.content)

        try:
            parsed = schema_model.model_validate_json(cleaned)
            return parsed, result
        except ValidationError as exc:
            last_error = exc
            logger.warning(
                "%s: %s produced schema-invalid %s on attempt %d/%d: %s",
                provider_name,
                schema_name,
                schema_name,
                attempt + 1,
                MAX_REPAIR_ATTEMPTS + 1,
                exc,
            )

            if attempt >= MAX_REPAIR_ATTEMPTS:
                break

            current_messages = messages + [
                {"role": "assistant", "content": result.content},
                {
                    "role": "user",
                    "content": (
                        "Your previous response did not match the required "
                        f"JSON schema. Validation errors:\n{exc}\n\n"
                        "Return ONLY the corrected JSON object — no prose, "
                        "no markdown code fences."
                    ),
                },
            ]

    raise ProviderResponseError(
        f"{provider_name} failed to produce schema-valid {schema_name} after "
        f"{MAX_REPAIR_ATTEMPTS + 1} attempt(s): {last_error}"
    )


def run_structured_stage(
    *,
    stage: str,
    system_prompt: str,
    user_prompt: str,
    schema_model: type[T],
    schema_name: str,
    model_by_provider: dict[str, Optional[str]],
    temperature: float = 0.7,
    max_tokens: int = 4000,
    extra_params_by_provider: Optional[dict[str, dict[str, Any]]] = None,
) -> tuple[T, dict[str, Any]]:
    primary_name, fallback_name = get_stage_providers(stage)
    extra_params_by_provider = extra_params_by_provider or {}

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    provider_order = [primary_name]

    if fallback_name and fallback_name != primary_name:
        provider_order.append(fallback_name)

    last_error: Optional[Exception] = None
    fallback_reason: Optional[str] = None

    for index, provider_name in enumerate(provider_order):
        is_fallback = index > 0

        try:
            provider = get_provider(provider_name)
        except ValueError as exc:
            last_error = exc
            fallback_reason = "unknown_provider"
            logger.warning("%s stage: unknown provider %r", stage, provider_name)
            continue

        model = model_by_provider.get(provider_name)

        if not model or not provider.is_configured():
            last_error = ProviderUnavailableError(
                f"{provider_name} is not configured for stage {stage}"
            )
            fallback_reason = "provider_not_configured"
            logger.warning(
                "%s stage: %s not configured, trying next provider",
                stage,
                provider_name,
            )
            continue

        try:
            parsed, result = _attempt_provider(
                provider_name,
                messages=messages,
                model=model,
                schema_model=schema_model,
                schema_name=schema_name,
                temperature=temperature,
                max_tokens=max_tokens,
                extra_params=extra_params_by_provider.get(provider_name),
            )

            audit = StageAudit(
                stage=stage,
                provider_requested=primary_name,
                provider_used=provider_name,
                model=model,
                hardware=_HARDWARE_LABEL.get(provider_name, provider_name),
                latency_ms=round(result.latency_ms, 1),
                fallback_used=is_fallback,
                fallback_reason=fallback_reason if is_fallback else None,
            )

            return parsed, audit.to_dict()

        except ProviderUnavailableError as exc:
            last_error = exc
            fallback_reason = "provider_unreachable"
            logger.warning("%s stage: %s unreachable: %s", stage, provider_name, exc)
        except ProviderResponseError as exc:
            last_error = exc
            fallback_reason = "invalid_structured_output"
            logger.warning(
                "%s stage: %s returned unusable output: %s", stage, provider_name, exc
            )

    raise StageExecutionError(
        f"{stage} failed on all configured providers "
        f"({', '.join(provider_order)}): {last_error}"
    )
