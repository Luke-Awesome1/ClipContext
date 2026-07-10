"""Confirms content_generator.py and discriminator.py are wired to the
provider orchestrator with the right stage name, schema, and models —
without exercising the orchestrator's own retry/fallback logic again (see
test_ai_providers.py for that).
"""

import json

import src.ai.content_generator as content_generator_module
import src.models.discriminator.discriminator as discriminator_module
from src.models.discriminator.schemas import DiscriminatorResult
from src.models.generated_content import GeneratedContent


def _generated_content_payload():
    return GeneratedContent(
        titles=[{"id": i, "text": f"title {i}"} for i in range(1, 11)],
        descriptions=[{"id": i, "text": f"description {i}"} for i in range(1, 11)],
        hashtags=[{"id": i, "tags": [f"#tag{i}"]} for i in range(1, 11)],
    )


def _discriminator_payload():
    ranked = [
        {"id": i, "rank": i, "score": 100 - i, "reason": "because"}
        for i in range(1, 11)
    ]
    return DiscriminatorResult(titles=ranked, descriptions=ranked, hashtags=ranked)


def test_generate_content_calls_orchestrator_with_content_generation_stage(
    monkeypatch, tmp_path
):
    captured = {}

    def fake_run_structured_stage(**kwargs):
        captured.update(kwargs)
        return _generated_content_payload(), {
            "stage": "content_generation",
            "provider_requested": "fireworks",
            "provider_used": "fireworks",
            "model": "kimi",
            "hardware": "Fireworks-hosted inference",
            "latency_ms": 12.3,
            "fallback_used": False,
            "fallback_reason": None,
        }

    monkeypatch.setattr(
        content_generator_module, "run_structured_stage", fake_run_structured_stage
    )

    context_path = tmp_path / "caption_context.json"
    syntax_path = tmp_path / "w_syntax.json"
    context_path.write_text(json.dumps({"topic": "t"}))
    syntax_path.write_text(json.dumps({"syntax_blueprint": {}}))

    content, audit = content_generator_module.generate_content(
        video_context_path=context_path, syntax_path=syntax_path
    )

    assert isinstance(content, GeneratedContent)
    assert audit["provider_used"] == "fireworks"
    assert captured["stage"] == "content_generation"
    assert captured["schema_model"] is GeneratedContent
    assert "fireworks" in captured["model_by_provider"]
    assert "amd_vllm" in captured["model_by_provider"]
    assert captured["extra_params_by_provider"]["fireworks"] == {
        "reasoning_effort": "none"
    }


def test_run_discriminator_audit_calls_orchestrator_with_discriminator_stage(
    monkeypatch,
):
    captured = {}

    def fake_run_structured_stage(**kwargs):
        captured.update(kwargs)
        return _discriminator_payload(), {
            "stage": "discriminator",
            "provider_requested": "amd_vllm",
            "provider_used": "amd_vllm",
            "model": "qwen",
            "hardware": "AMD GPU via ROCm/vLLM",
            "latency_ms": 45.6,
            "fallback_used": False,
            "fallback_reason": None,
        }

    monkeypatch.setattr(
        discriminator_module, "run_structured_stage", fake_run_structured_stage
    )

    result, audit = discriminator_module.run_discriminator_audit(
        candidate_pools={"titles": [], "descriptions": [], "hashtags": []},
        context_data={"topic": "t"},
        benchmarks={"avg_views": 1000},
    )

    assert isinstance(result, DiscriminatorResult)
    assert audit["provider_used"] == "amd_vllm"
    assert captured["stage"] == "discriminator"
    assert captured["schema_model"] is DiscriminatorResult
    assert "fireworks" in captured["model_by_provider"]
    assert "amd_vllm" in captured["model_by_provider"]
