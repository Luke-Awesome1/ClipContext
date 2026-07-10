"""AMD GPU inference provider — an OpenAI-compatible vLLM server running on
ROCm (see amd/README.md for how that server is started).

Architecture: ClipContext backend -> AMD_VLLM_BASE_URL -> vLLM -> PyTorch/HIP
-> AMD GPU. The browser never talks to this endpoint directly; only this
backend process does, via server-side environment configuration.

vLLM's OpenAI-compatible server does not universally guarantee constrained
JSON-schema decoding depends on the installed guided-decoding backend and
model). This provider tries `response_format: json_schema` first and falls
back to plain `json_object` mode within the same attempt if the server
rejects the schema request with a 4xx — the orchestrator's schema-validation
retry loop (src/ai/providers/orchestrator.py) is the actual correctness
backstop either way.
"""

import os
import time
from typing import Any, Optional

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI

from src.ai.providers.base import (
    AIProvider,
    CompletionResult,
    ProviderResponseError,
    ProviderUnavailableError,
)


def _categorize_exception(exc: Exception) -> str:
    if isinstance(exc, (APIConnectionError, APITimeoutError)):
        return "connection_error"
    if isinstance(exc, APIStatusError):
        return "http_error"
    return "unknown_error"


class AmdVllmProvider(AIProvider):
    name = "amd_vllm"

    def __init__(self) -> None:
        self._client: Optional[OpenAI] = None
        self._client_base_url: Optional[str] = None

    def base_url(self) -> Optional[str]:
        raw = os.getenv("AMD_VLLM_BASE_URL")
        return raw.rstrip("/") if raw else None

    def model(self) -> Optional[str]:
        return os.getenv("AMD_VLLM_MODEL") or None

    def _api_key(self) -> str:
        # vLLM's OpenAI-compatible server only enforces a bearer key if
        # started with --api-key; the openai client requires a non-empty
        # string regardless, so default to a placeholder when unset.
        return os.getenv("AMD_VLLM_API_KEY") or "unset"

    def is_configured(self) -> bool:
        return bool(self.base_url() and self.model())

    def _get_client(self) -> OpenAI:
        base_url = self.base_url()

        if not base_url:
            raise ProviderUnavailableError("AMD_VLLM_BASE_URL is not set")

        if self._client is None or self._client_base_url != base_url:
            timeout_seconds = float(os.getenv("AMD_VLLM_TIMEOUT_SECONDS", "60"))
            self._client = OpenAI(
                api_key=self._api_key(),
                base_url=base_url,
                timeout=timeout_seconds,
                max_retries=0,
            )
            self._client_base_url = base_url

        return self._client

    def health_check(self, timeout: float = 5.0) -> dict[str, Any]:
        model = self.model()

        if not self.is_configured():
            return {
                "configured": False,
                "reachable": False,
                "model": model,
            }

        try:
            client = self._get_client()
            models_response = client.with_options(timeout=timeout).models.list()
            available_ids = [item.id for item in getattr(models_response, "data", [])]

            return {
                "configured": True,
                "reachable": True,
                "model": model,
                "model_loaded": (model in available_ids) if available_ids else None,
            }
        except Exception as exc:  # noqa: BLE001 - health check must never raise
            return {
                "configured": True,
                "reachable": False,
                "model": model,
                "error_category": _categorize_exception(exc),
            }

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
            raise ProviderUnavailableError(
                "AMD vLLM provider is not configured "
                "(AMD_VLLM_BASE_URL / AMD_VLLM_MODEL unset)"
            )

        client = self._get_client()

        base_kwargs: dict[str, Any] = dict(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        if extra_params:
            base_kwargs.update(extra_params)

        response_format_attempts: list[Optional[dict[str, Any]]]

        if json_schema is not None:
            response_format_attempts = [
                {
                    "type": "json_schema",
                    "json_schema": {"name": json_schema_name, "schema": json_schema},
                },
                {"type": "json_object"},
            ]
        else:
            response_format_attempts = [None]

        last_status_error: Optional[APIStatusError] = None

        for response_format in response_format_attempts:
            call_kwargs = dict(base_kwargs)

            if response_format is not None:
                call_kwargs["response_format"] = response_format

            start = time.monotonic()

            try:
                response = client.chat.completions.create(**call_kwargs)
            except (APIConnectionError, APITimeoutError) as exc:
                raise ProviderUnavailableError(f"AMD vLLM unreachable: {exc}") from exc
            except APIStatusError as exc:
                if exc.status_code >= 500:
                    raise ProviderUnavailableError(
                        f"AMD vLLM server error {exc.status_code}"
                    ) from exc

                # A 4xx here most likely means this vLLM build/model doesn't
                # support the requested response_format shape — try the next
                # (looser) shape before giving up on the provider entirely.
                last_status_error = exc
                continue

            latency_ms = (time.monotonic() - start) * 1000

            if not response.choices:
                raise ProviderResponseError("AMD vLLM returned no choices")

            content = response.choices[0].message.content

            if not content:
                raise ProviderResponseError("AMD vLLM returned empty content")

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

        raise ProviderResponseError(
            "AMD vLLM rejected every supported response_format for this "
            f"request: {last_status_error}"
        )
