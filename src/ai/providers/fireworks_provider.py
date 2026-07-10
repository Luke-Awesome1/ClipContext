"""Fireworks AI provider — wraps the existing OpenAI-compatible client.

This preserves the exact request shapes already validated against the
Fireworks account (see src/ai/content_generator.py and
src/models/discriminator/discriminator.py history in AGENT.md): callers pass
provider-specific parameters (e.g. reasoning_effort) through `extra_params`
rather than this module guessing at them.
"""

import os
import time
from typing import Any, Optional

from openai import APIConnectionError, APIStatusError, APITimeoutError

from src.ai.fireworks.client import get_fireworks_client
from src.ai.providers.base import (
    AIProvider,
    CompletionResult,
    ProviderResponseError,
    ProviderUnavailableError,
)


class FireworksProvider(AIProvider):
    name = "fireworks"

    def is_configured(self) -> bool:
        return bool(os.getenv("FIREWORKS_API_KEY"))

    def chat_completion(
        self,
        *,
        messages: list[dict[str, Any]],
        model: str,
        json_schema: Optional[dict[str, Any]] = None,
        json_schema_name: str = "Response",
        temperature: float = 0.7,
        max_tokens: int = 4000,
        extra_params: Optional[dict[str, Any]] = None,
    ) -> CompletionResult:
        if not self.is_configured():
            raise ProviderUnavailableError("FIREWORKS_API_KEY is not set")

        client = get_fireworks_client()

        call_kwargs: dict[str, Any] = dict(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        if json_schema is not None:
            call_kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": json_schema_name, "schema": json_schema},
            }

        if extra_params:
            call_kwargs.update(extra_params)

        start = time.monotonic()

        try:
            response = client.chat.completions.create(**call_kwargs)
        except (APIConnectionError, APITimeoutError) as exc:
            raise ProviderUnavailableError(f"Fireworks unreachable: {exc}") from exc
        except APIStatusError as exc:
            if exc.status_code >= 500:
                raise ProviderUnavailableError(
                    f"Fireworks server error {exc.status_code}"
                ) from exc
            raise ProviderResponseError(
                f"Fireworks request error {exc.status_code}: {exc}"
            ) from exc

        latency_ms = (time.monotonic() - start) * 1000

        if not response.choices:
            raise ProviderResponseError("Fireworks returned no choices")

        choice = response.choices[0]
        content = choice.message.content

        if not content:
            raise ProviderResponseError("Fireworks returned empty content")

        if choice.finish_reason == "length":
            raise ProviderResponseError("Fireworks response was truncated")

        usage = getattr(response, "usage", None)

        return CompletionResult(
            content=content,
            model=model,
            provider=self.name,
            latency_ms=latency_ms,
            prompt_tokens=getattr(usage, "prompt_tokens", None) if usage else None,
            completion_tokens=getattr(usage, "completion_tokens", None)
            if usage
            else None,
        )

    def health_check(self, timeout: float = 5.0) -> dict[str, Any]:
        return {"configured": self.is_configured(), "reachable": None}
