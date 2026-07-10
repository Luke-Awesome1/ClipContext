"""Minimal AI provider interface.

ClipContext needs exactly one capability from a text-inference provider:
send a chat-style prompt, optionally constrained to a JSON schema, and get
back the raw text content plus enough metadata (model, latency, token
counts) to build a truthful execution audit. This is intentionally not a
general-purpose LLM SDK — see AGENT.md / README for why.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


class ProviderError(RuntimeError):
    """Base class for AI provider failures."""


class ProviderUnavailableError(ProviderError):
    """The provider could not be reached at all: connection refused, DNS
    failure, timeout, or an HTTP 5xx from the inference server itself. This
    is the category that should trigger fallback to another provider.
    """


class ProviderResponseError(ProviderError):
    """The provider responded, but the response is unusable: empty content,
    a non-retryable 4xx, or content that never became valid JSON even after
    a bounded repair retry. This also triggers fallback (a provider that
    cannot produce valid structured output for a stage is not usable for
    that stage), but is a distinct failure category for the audit trail.
    """


@dataclass
class CompletionResult:
    content: str
    model: str
    provider: str
    latency_ms: float
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None


class AIProvider(ABC):
    name: str

    @abstractmethod
    def is_configured(self) -> bool:
        """Whether this provider has the environment configuration it needs
        to be attempted at all (API key / base URL / model)."""

    @abstractmethod
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
        """Run one chat completion.

        Raises ProviderUnavailableError or ProviderResponseError on failure;
        never returns a partially-usable result.
        """

    def health_check(self, timeout: float = 5.0) -> dict[str, Any]:
        """Best-effort reachability probe for a status/health endpoint.

        Must never raise and must never include secrets (keys, tokens,
        full stack traces) — the return value is safe to expose over HTTP.
        """
        return {"configured": self.is_configured(), "reachable": None}
