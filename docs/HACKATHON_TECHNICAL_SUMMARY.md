# ClipContext — Technical Summary (lablab.ai AMD Developer Hackathon, ACT II, Track 3)

## What ClipContext does

ClipContext takes a short creator video (roughly 30 seconds to 2 minutes)
and produces platform-ready metadata: 10 candidate titles, 10 candidate
descriptions, and 10 candidate hashtag sets, each independently ranked, plus
an optional direct upload of the analyzed video to the creator's own
YouTube channel with the metadata they picked.

## The problem

Creators spend real time writing titles/descriptions/hashtags after editing
is done, usually without grounding that copy in what the video actually
shows and says, and without reference to what's currently working on the
platform. Naively sending a whole video to a multimodal model for this is
also expensive and slow — most frames in a short clip are temporally
redundant.

## The solution

A sparse, evidence-grounded pipeline:

1. **Local, free preprocessing** — video validation, audio extraction,
   1 FPS frame scan, local visual-quality scoring, perceptual-diversity
   frame selection, and 5-second temporal window construction all happen
   locally (OpenCV, ffmpeg, faster-whisper) before any paid inference call.
2. **Multimodal understanding** (Fireworks Kimi vision, Gemini fallback) —
   turns the sparse frame budget + transcript into a canonical
   `VideoContext`: topic, content type, core message, multimodal summary,
   key entities, visible on-screen text, captionable details, and explicit
   uncertainties (see `src/models/video_context.py`).
3. **Trend analysis** — worldwide YouTube trend clustering plus, if a
   creator handle is given, creator-specific trend analysis
   (`src/trends/`), producing a syntax blueprint (structural patterns), SEO
   vocabulary, and adjectives used as *stylistic* evidence in generation —
   never as a source of factual claims about the video.
4. **Content generation** — exactly 10 titles, 10 descriptions, 10 hashtag
   sets, grounded in `VideoContext` and shaped by the trend syntax
   (`src/ai/content_generator.py`, `src/prompts/content_generation.py`).
   Text-only, structured JSON output validated against a Pydantic schema
   that enforces exact counts and sequential ids
   (`src/models/generated_content.py`).
5. **Discriminator/ranking** — independently ranks each of the three
   candidate pools against the `VideoContext` and trend benchmarks
   (`src/models/discriminator/`), also text-only, structured JSON.

Stages 4 and 5 are the ones this hackathon submission moves onto AMD GPU
compute — see below.

## Why trend analysis and metadata generation are separated

Trend analysis produces *stylistic* evidence (how titles/descriptions/
hashtags on this platform tend to be structured, what vocabulary shows up).
`VideoContext` is the *only* source of factual claims. The content
generation system prompt (`src/prompts/content_generation.py`) explicitly
forbids inventing people, locations, events, or statistics not present in
`VideoContext`, and forbids inserting trend vocabulary that isn't
semantically relevant to the actual video — this is a hackathon-scale
guardrail against generic, ungrounded, hallucinated copy.

## How ranking works

The discriminator receives the full candidate pools plus a compact
"ground-truth video digest" (topic, core message, multimodal summary, key
entities, visible text) and historical performance benchmarks derived from
the top-viewed trend cluster, and returns an independent 1–10 ranking per
pool with a numeric score and a short reason per candidate
(`src/models/discriminator/schemas.py`). Titles, descriptions, and hashtags
are ranked independently — candidate id 3 in titles has no relationship to
id 3 in descriptions.

## How AMD compute is used

**Architecture:**

```
FastAPI backend
  │
  ▼
src/ai/providers/orchestrator.py   (run_structured_stage)
  │
  ├─ resolves provider via env: CONTENT_GENERATION_PROVIDER /
  │  DISCRIMINATOR_PROVIDER (default "fireworks")
  │
  ▼
src/ai/providers/amd_vllm.py  ──▶  AMD_VLLM_BASE_URL (OpenAI-compatible)
                                          │
                                          ▼
                                  vLLM 0.16.1.dev0 (ROCm721 build)
                                          │
                                          ▼
                                  PyTorch 2.9.1 / ROCm 7.2.53211 / HIP
                                          │
                                          ▼
                          AMD Radeon PRO W7900-class GPU (gfx1100, 48GB VRAM)
```

**Stages that run on AMD:** `content_generation` and `discriminator` — see
[Why these two stages](#why-these-two-stages-and-not-vision).

**Real hardware, confirmed via `amd/verify_rocm.py` on the allocated
notebook:** AMD Radeon PRO W7900-class GPU, `gfx1100` (RDNA3), 48 GiB VRAM,
single card; ROCm/HIP 7.2.53211; PyTorch 2.9.1 (ROCm build); vLLM
0.16.1.dev0 (ROCm721 build); ~93 GiB free disk; 503 GiB RAM.

**The exact model running on AMD: `Qwen/Qwen2.5-14B-Instruct`.** Selected
against the real numbers above, not guessed beforehand — see
`amd/README.md`'s [Model selection](../amd/README.md#model-selection) for
the full reasoning: ungated (no `HF_TOKEN`), ~29 GiB bf16 weights fit 48 GiB
VRAM with ~19 GiB headroom for KV cache, fits the 93 GiB disk budget with
margin (a 30B+ model's download-time peak usage would not have), a
long-validated vLLM architecture on ROCm, strong structured-JSON
instruction-following, and a 32K native context window far exceeding
either stage's real prompt size (`MAX_MODEL_LEN=16384` caps KV cache
allocation to what's actually used). Real benchmark numbers from
`amd/benchmark_amd.py` will be added here once a full run against the live
server completes.

**Why these two stages, and not vision:** `content_generation` and
`discriminator` are ClipContext's only text-only, structured-JSON AI
stages. Both already called an OpenAI-compatible client
(`src/ai/fireworks/client.py`) before this integration, so pointing them at
another OpenAI-compatible endpoint is a provider swap behind an existing
interface, not a pipeline rewrite. Visual understanding
(`src/ai/fireworks/multimodal.py`, `src/ai/vision/gemma.py`) takes image
input and stays on Fireworks Kimi / Gemini — the AMD notebook serves one
text model, not a vision-language model, and swapping a working vision
pipeline for a text-only model would degrade the product's core multimodal
grounding, which the hackathon instructions for this integration explicitly
rule out.

**How ROCm is involved:** ROCm is AMD's GPU compute stack — the HIP runtime
PyTorch/vLLM use to execute tensor operations on the AMD GPU, in the same
architectural position CUDA occupies for NVIDIA GPUs. `amd/verify_rocm.py`
checks `torch.version.hip`, `torch.cuda.is_available()` (HIP-backed under
ROCm), and `torch.cuda.get_device_name(0)` before any inference is
attempted.

**How vLLM is involved:** vLLM serves the selected model behind an
OpenAI-compatible HTTP API (`amd/start_vllm.sh` starts
`vllm.entrypoints.openai.api_server`) so the existing OpenAI Python client
already used for Fireworks (`openai` in `requirements.txt`) works against
it unchanged — `src/ai/providers/amd_vllm.py` just points that same client
at a different `base_url`.

## Fallback and truthfulness

`src/ai/providers/orchestrator.py` tries the configured primary provider,
retries once with a schema-repair prompt if the JSON fails Pydantic
validation, and falls back to the configured fallback provider
(`ProviderUnavailableError` for connection/timeout/5xx,
`ProviderResponseError` for unusable/invalid output even after repair). The
result is a `StageAudit` recording `provider_requested`, `provider_used`,
`model`, `hardware`, `latency_ms`, `fallback_used`, `fallback_reason` — this
is attached to every `PipelineResult` as `ai_audit` and persisted to
`outputs/<job_id>/ai_provider_audit.json`. The frontend only displays an
"AMD GPU inference" indicator when `provider_used == "amd_vllm"` for that
specific stage in that specific run — never for a fallback, and never
speculatively.

## What was benchmarked

`amd/benchmark_amd.py` runs the actual `content_generation` system prompt,
prompt builder, and Pydantic schema validation
(`src/ai/content_generator.py`, `src/models/generated_content.py`) against
a fixture `VideoContext` + trend syntax, directly through
`AmdVllmProvider` (no Fireworks fallback in the benchmark path), and
reports real latency, prompt/completion token counts (only when the vLLM
server returns `usage` metadata — never fabricated), tokens/second derived
from those real numbers, and whether the response actually validated
against `GeneratedContent`'s schema (exact 10/10/10 counts, sequential ids).
Real numbers from an actual run against the AMD notebook will be recorded
here once the notebook is available — this document does not claim a
throughput number that hasn't been measured.

## Deployed architecture

See the root [`README.md`](../README.md) for full deployment instructions.
Summary: Next.js frontend and FastAPI backend deploy independently and
permanently; `AMD_VLLM_BASE_URL` is only set in the backend's environment
while the AMD notebook is up for a demo, with automatic Fireworks fallback
otherwise.

## Known limitations

- The AMD notebook allocation is runtime-limited — not permanent public
  infrastructure. See [`amd/README.md`](../amd/README.md) for the
  fallback strategy.
- vLLM's structured-JSON-output support depends on the installed
  guided-decoding backend and the chosen model; `AmdVllmProvider` tries
  `response_format: json_schema` first and falls back to `json_object`
  within the same request if the server rejects the schema shape — the
  orchestrator's Pydantic-validation repair retry is the actual
  correctness backstop either way, not an assumption that any given model
  perfectly follows JSON-schema constrained decoding.
- Job state and YouTube session state remain in-memory (unchanged from the
  pre-AMD architecture) — see the root README's "Known limitations"
  section.
