"""Tests for the AI provider abstraction (src/ai/providers/).

All external HTTP is mocked — no real Fireworks or AMD vLLM network calls.
AMD hardware validation is a separate real smoke test (amd/smoke_test.py),
not part of this suite.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
import pytest
from openai import APIConnectionError, APIStatusError, APITimeoutError
from pydantic import BaseModel

from src.ai.providers.amd_vllm import AmdVllmProvider
from src.ai.providers.base import ProviderResponseError, ProviderUnavailableError
from src.ai.providers.fireworks_provider import FireworksProvider
from src.ai.providers.orchestrator import (
    StageExecutionError,
    run_structured_stage,
    strip_code_fences,
)
import src.ai.providers.registry as registry_module


class _Widget(BaseModel):
    name: str
    count: int


def _fake_completion(content: str, finish_reason: str = "stop", usage=None):
    message = SimpleNamespace(content=content)
    choice = SimpleNamespace(message=message, finish_reason=finish_reason)
    return SimpleNamespace(choices=[choice], usage=usage)


def _fake_request() -> httpx.Request:
    return httpx.Request("POST", "https://example.invalid/v1/chat/completions")


def _fake_status_error(status_code: int) -> APIStatusError:
    response = httpx.Response(status_code, request=_fake_request())
    return APIStatusError("boom", response=response, body=None)


# --- FireworksProvider -------------------------------------------------


def test_fireworks_provider_serializes_request_and_parses_response(monkeypatch):
    captured = {}

    def fake_create(**kwargs):
        captured.update(kwargs)
        return _fake_completion('{"name": "a", "count": 1}')

    fake_client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=fake_create))
    )
    monkeypatch.setattr(
        "src.ai.providers.fireworks_provider.get_fireworks_client",
        lambda: fake_client,
    )
    monkeypatch.setenv("FIREWORKS_API_KEY", "test-key")

    provider = FireworksProvider()
    result = provider.chat_completion(
        messages=[{"role": "user", "content": "hi"}],
        model="some-model",
        json_schema=_Widget.model_json_schema(),
        json_schema_name="Widget",
        temperature=0.5,
        max_tokens=100,
        extra_params={"reasoning_effort": "none"},
    )

    assert result.content == '{"name": "a", "count": 1}'
    assert result.provider == "fireworks"
    assert captured["model"] == "some-model"
    assert captured["reasoning_effort"] == "none"
    assert captured["response_format"]["json_schema"]["name"] == "Widget"


def test_fireworks_provider_raises_unavailable_on_connection_error(monkeypatch):
    def fake_create(**kwargs):
        raise APIConnectionError(request=_fake_request())

    fake_client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=fake_create))
    )
    monkeypatch.setattr(
        "src.ai.providers.fireworks_provider.get_fireworks_client",
        lambda: fake_client,
    )
    monkeypatch.setenv("FIREWORKS_API_KEY", "test-key")

    provider = FireworksProvider()

    with pytest.raises(ProviderUnavailableError):
        provider.chat_completion(messages=[], model="m")


def test_fireworks_provider_raises_unavailable_on_5xx(monkeypatch):
    def fake_create(**kwargs):
        raise _fake_status_error(503)

    fake_client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=fake_create))
    )
    monkeypatch.setattr(
        "src.ai.providers.fireworks_provider.get_fireworks_client",
        lambda: fake_client,
    )
    monkeypatch.setenv("FIREWORKS_API_KEY", "test-key")

    provider = FireworksProvider()

    with pytest.raises(ProviderUnavailableError):
        provider.chat_completion(messages=[], model="m")


def test_fireworks_provider_raises_response_error_on_empty_content(monkeypatch):
    fake_client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=lambda **kw: _fake_completion(""))
        )
    )
    monkeypatch.setattr(
        "src.ai.providers.fireworks_provider.get_fireworks_client",
        lambda: fake_client,
    )
    monkeypatch.setenv("FIREWORKS_API_KEY", "test-key")

    provider = FireworksProvider()

    with pytest.raises(ProviderResponseError):
        provider.chat_completion(messages=[], model="m")


def test_fireworks_provider_not_configured_raises_unavailable(monkeypatch):
    monkeypatch.delenv("FIREWORKS_API_KEY", raising=False)
    provider = FireworksProvider()

    with pytest.raises(ProviderUnavailableError):
        provider.chat_completion(messages=[], model="m")


# --- AmdVllmProvider -----------------------------------------------------


def _amd_provider(monkeypatch, base_url="http://amd-notebook:8000/v1", model="qwen-test"):
    monkeypatch.setenv("AMD_VLLM_BASE_URL", base_url)
    monkeypatch.setenv("AMD_VLLM_MODEL", model)
    return AmdVllmProvider()


def test_amd_provider_not_configured_when_env_unset(monkeypatch):
    monkeypatch.delenv("AMD_VLLM_BASE_URL", raising=False)
    monkeypatch.delenv("AMD_VLLM_MODEL", raising=False)

    provider = AmdVllmProvider()
    assert provider.is_configured() is False

    with pytest.raises(ProviderUnavailableError):
        provider.chat_completion(messages=[], model="m")


def test_amd_provider_successful_structured_response(monkeypatch):
    provider = _amd_provider(monkeypatch)

    fake_create = MagicMock(return_value=_fake_completion('{"name": "a", "count": 2}'))
    fake_client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=fake_create))
    )
    monkeypatch.setattr(provider, "_get_client", lambda: fake_client)

    result = provider.chat_completion(
        messages=[{"role": "user", "content": "hi"}],
        model="qwen-test",
        json_schema=_Widget.model_json_schema(),
        json_schema_name="Widget",
    )

    assert result.content == '{"name": "a", "count": 2}'
    assert result.provider == "amd_vllm"
    fake_create.assert_called_once()
    assert fake_create.call_args.kwargs["response_format"]["type"] == "json_schema"


def test_amd_provider_falls_back_to_json_object_on_400(monkeypatch):
    provider = _amd_provider(monkeypatch)

    calls = []

    def fake_create(**kwargs):
        calls.append(kwargs["response_format"]["type"])
        if kwargs["response_format"]["type"] == "json_schema":
            raise _fake_status_error(400)
        return _fake_completion('{"name": "a", "count": 3}')

    fake_client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=fake_create))
    )
    monkeypatch.setattr(provider, "_get_client", lambda: fake_client)

    result = provider.chat_completion(
        messages=[{"role": "user", "content": "hi"}],
        model="qwen-test",
        json_schema=_Widget.model_json_schema(),
        json_schema_name="Widget",
    )

    assert calls == ["json_schema", "json_object"]
    assert result.content == '{"name": "a", "count": 3}'


def test_amd_provider_raises_unavailable_on_timeout(monkeypatch):
    provider = _amd_provider(monkeypatch)

    def fake_create(**kwargs):
        raise APITimeoutError(request=_fake_request())

    fake_client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=fake_create))
    )
    monkeypatch.setattr(provider, "_get_client", lambda: fake_client)

    with pytest.raises(ProviderUnavailableError):
        provider.chat_completion(messages=[], model="qwen-test")


def test_amd_provider_raises_unavailable_on_connection_error(monkeypatch):
    provider = _amd_provider(monkeypatch)

    def fake_create(**kwargs):
        raise APIConnectionError(request=_fake_request())

    fake_client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=fake_create))
    )
    monkeypatch.setattr(provider, "_get_client", lambda: fake_client)

    with pytest.raises(ProviderUnavailableError):
        provider.chat_completion(messages=[], model="qwen-test")


def test_amd_provider_raises_unavailable_on_5xx(monkeypatch):
    provider = _amd_provider(monkeypatch)

    def fake_create(**kwargs):
        raise _fake_status_error(500)

    fake_client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=fake_create))
    )
    monkeypatch.setattr(provider, "_get_client", lambda: fake_client)

    with pytest.raises(ProviderUnavailableError):
        provider.chat_completion(messages=[], model="qwen-test")


def test_amd_provider_health_check_never_raises_when_unreachable(monkeypatch):
    provider = _amd_provider(monkeypatch)

    class ExplodingClient:
        def with_options(self, timeout):
            raise APIConnectionError(request=_fake_request())

    monkeypatch.setattr(provider, "_get_client", lambda: ExplodingClient())

    status = provider.health_check()
    assert status["configured"] is True
    assert status["reachable"] is False
    assert status["error_category"] == "connection_error"
    # never leaks the base URL or any secret
    assert "amd-notebook" not in str(status)


# --- strip_code_fences ---------------------------------------------------


@pytest.mark.parametrize(
    "raw,expected",
    [
        ('{"a": 1}', '{"a": 1}'),
        ('```json\n{"a": 1}\n```', '{"a": 1}'),
        ('```\n{"a": 1}\n```', '{"a": 1}'),
    ],
)
def test_strip_code_fences(raw, expected):
    assert strip_code_fences(raw) == expected


# --- run_structured_stage orchestration ----------------------------------


def _patch_provider(monkeypatch, name, fake_provider):
    monkeypatch.setitem(registry_module._providers, name, fake_provider)


class _FakeProvider:
    def __init__(self, responses, configured=True):
        self._responses = list(responses)
        self._configured = configured
        self.calls = 0

    def is_configured(self):
        return self._configured

    def chat_completion(self, **kwargs):
        self.calls += 1
        outcome = self._responses.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def test_run_structured_stage_uses_primary_provider_by_default(monkeypatch):
    monkeypatch.delenv("CONTENT_GENERATION_PROVIDER", raising=False)
    monkeypatch.delenv("CONTENT_GENERATION_FALLBACK_PROVIDER", raising=False)

    fireworks = _FakeProvider([_fake_result('{"name": "a", "count": 1}')])
    _patch_provider(monkeypatch, "fireworks", fireworks)

    parsed, audit = run_structured_stage(
        stage="content_generation",
        system_prompt="sys",
        user_prompt="user",
        schema_model=_Widget,
        schema_name="Widget",
        model_by_provider={"fireworks": "kimi", "amd_vllm": None},
    )

    assert parsed == _Widget(name="a", count=1)
    assert audit["provider_requested"] == "fireworks"
    assert audit["provider_used"] == "fireworks"
    assert audit["fallback_used"] is False


def test_run_structured_stage_falls_back_on_amd_unreachable(monkeypatch):
    monkeypatch.setenv("CONTENT_GENERATION_PROVIDER", "amd_vllm")
    monkeypatch.setenv("CONTENT_GENERATION_FALLBACK_PROVIDER", "fireworks")

    amd = _FakeProvider([ProviderUnavailableError("connection refused")])
    fireworks = _FakeProvider([_fake_result('{"name": "b", "count": 2}')])
    _patch_provider(monkeypatch, "amd_vllm", amd)
    _patch_provider(monkeypatch, "fireworks", fireworks)

    parsed, audit = run_structured_stage(
        stage="content_generation",
        system_prompt="sys",
        user_prompt="user",
        schema_model=_Widget,
        schema_name="Widget",
        model_by_provider={"fireworks": "kimi", "amd_vllm": "qwen"},
    )

    assert parsed == _Widget(name="b", count=2)
    assert audit["provider_requested"] == "amd_vllm"
    assert audit["provider_used"] == "fireworks"
    assert audit["fallback_used"] is True
    assert audit["fallback_reason"] == "provider_unreachable"


def test_run_structured_stage_never_falsely_claims_amd_on_fallback(monkeypatch):
    """The audit must never say provider_used=amd_vllm for a request that
    actually fell back to Fireworks — this is the core anti-fake-AMD
    invariant the whole audit system exists to guarantee.
    """
    monkeypatch.setenv("DISCRIMINATOR_PROVIDER", "amd_vllm")
    monkeypatch.setenv("DISCRIMINATOR_FALLBACK_PROVIDER", "fireworks")

    amd = _FakeProvider([ProviderResponseError("invalid json even after repair")])
    fireworks = _FakeProvider([_fake_result('{"name": "c", "count": 3}')])
    _patch_provider(monkeypatch, "amd_vllm", amd)
    _patch_provider(monkeypatch, "fireworks", fireworks)

    parsed, audit = run_structured_stage(
        stage="discriminator",
        system_prompt="sys",
        user_prompt="user",
        schema_model=_Widget,
        schema_name="Widget",
        model_by_provider={"fireworks": "minimax", "amd_vllm": "qwen"},
    )

    assert audit["provider_used"] != "amd_vllm"
    assert audit["provider_used"] == "fireworks"
    assert audit["fallback_used"] is True
    assert audit["fallback_reason"] == "invalid_structured_output"


def test_run_structured_stage_repairs_invalid_json_before_failing(monkeypatch):
    monkeypatch.setenv("CONTENT_GENERATION_PROVIDER", "fireworks")
    monkeypatch.delenv("CONTENT_GENERATION_FALLBACK_PROVIDER", raising=False)

    fireworks = _FakeProvider(
        [
            _fake_result("not json at all"),
            _fake_result('{"name": "repaired", "count": 9}'),
        ]
    )
    _patch_provider(monkeypatch, "fireworks", fireworks)

    parsed, audit = run_structured_stage(
        stage="content_generation",
        system_prompt="sys",
        user_prompt="user",
        schema_model=_Widget,
        schema_name="Widget",
        model_by_provider={"fireworks": "kimi", "amd_vllm": None},
    )

    assert parsed == _Widget(name="repaired", count=9)
    assert fireworks.calls == 2
    assert audit["fallback_used"] is False


def test_run_structured_stage_raises_when_all_providers_exhausted(monkeypatch):
    monkeypatch.setenv("CONTENT_GENERATION_PROVIDER", "amd_vllm")
    monkeypatch.setenv("CONTENT_GENERATION_FALLBACK_PROVIDER", "fireworks")

    amd = _FakeProvider([ProviderUnavailableError("down")])
    fireworks = _FakeProvider([ProviderUnavailableError("also down")])
    _patch_provider(monkeypatch, "amd_vllm", amd)
    _patch_provider(monkeypatch, "fireworks", fireworks)

    with pytest.raises(StageExecutionError):
        run_structured_stage(
            stage="content_generation",
            system_prompt="sys",
            user_prompt="user",
            schema_model=_Widget,
            schema_name="Widget",
            model_by_provider={"fireworks": "kimi", "amd_vllm": "qwen"},
        )


def _fake_result(content: str):
    from src.ai.providers.base import CompletionResult

    return CompletionResult(
        content=content, model="m", provider="p", latency_ms=1.0
    )
