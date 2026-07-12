# ClipContext — Hackathon Submission

**lablab.ai AMD Developer Hackathon, ACT II — Track 3 (Unicorn / Open Innovation)**

## Problem

Creators spend real time after editing is done writing titles,
descriptions, and hashtags — usually without grounding that copy in what
the video actually shows and says, and without reference to what's
currently working on the platform. Naively sending a whole video to a
multimodal model for this is also expensive and slow: most frames in a
short clip are temporally redundant, and a single "best guess" output
gives a creator nothing to choose between.

## Solution

ClipContext is a sparse, evidence-grounded pipeline: local preprocessing
(free) → multimodal understanding (one paid call) → trend analysis
(worldwide, swapped for the creator's own channel if a handle is given) →
10 independently-generated and independently-ranked candidates each for
titles, descriptions, and hashtags → optional direct YouTube upload with
the creator's picks. Full pipeline detail: [AI-Pipeline.md](AI-Pipeline.md).

The core technical bet: everything that *can* run locally and free does —
video validation, audio extraction, a 1 FPS frame scan, local
visual-quality scoring, perceptual-diversity frame selection, and 5-second
temporal window construction (OpenCV, ffmpeg, faster-whisper) — before any
paid inference call happens. Only the genuinely-necessary AI calls (visual
understanding, semantic fusion, trend-syntax extraction, content
generation, ranking) are paid, and content generation/ranking are the two
that can run on AMD GPU compute instead of Fireworks.

## Innovation

- **Evidence-grounded generation, not free-association.** The content
  generation system prompt is built from a canonical `VideoContext`
  (topic, core message, multimodal summary, key entities, visible text,
  captionable details, explicit uncertainties) and explicitly forbids
  inventing people, locations, events, or statistics not present in it.
  Trend data supplies *style*, never facts. See
  [PROMPT_ENGINEERING.md](PROMPT_ENGINEERING.md) for the full prompt-design
  rationale, including the fixed-strategy-per-candidate technique used to
  force genuine diversity across the 10 titles/descriptions/hashtag sets
  instead of ten reworded variants of one idea.
- **Independent, audited AI provider routing.** `content_generation` and
  `discriminator` can each independently route to Fireworks or an AMD
  vLLM server via environment variables, with automatic, truthful fallback
  and a per-stage audit trail — not a hardcoded provider choice. See
  [AMD.md](AMD.md).
- **A ranking stage, not just a generation stage.** Rather than trusting
  one model's single output, a second discriminator model independently
  scores and ranks each of the three candidate pools against the video's
  ground truth and real trend benchmarks — the product surfaces *why* a
  candidate ranked where it did, not just a black-box pick.
- **Real trend data, from the right source.** Worldwide trend analysis
  always runs — it queries the YouTube Data API for real high-performing
  videos in the video's own niche, clusters them by performance, and
  extracts a style profile (structure, SEO vocabulary, tone) from the
  best-performing cluster. If the creator provides their own channel
  handle, ClipContext instead pulls *that creator's* own top-performing
  videos and extracts the same kind of profile from them — a straight
  swap, not a blend — so a channel with an established voice gets styled
  to match it instead of a generic trending template. Either way, the
  discriminator still benchmarks every candidate against real worldwide
  performance data. See [AI-Pipeline.md § Stage 8-9](AI-Pipeline.md).

## AMD usage

Two AI stages — **content generation** (10 titles/descriptions/hashtag
sets) and the **discriminator** (ranking them) — run on an AMD GPU via
ROCm + vLLM, exposed through an OpenAI-compatible server, routed to from
the exact same code path that already called Fireworks. This is a real
integration, not a cosmetic one:

- The backend is the only thing that ever talks to the AMD endpoint —
  never the browser, and never as an unauthenticated public endpoint.
- Model selection (`Qwen/Qwen2.5-7B-Instruct`) was based on real measured
  VRAM and throughput on the actual allocated GPU — see the benchmark
  numbers in [AMD.md § Model selection](AMD.md#model-selection-and-benchmark-numbers) —
  not guessed or assumed.
- Every completed job records a truthful per-stage audit
  (`provider_requested`, `provider_used`, `model`, `hardware`,
  `latency_ms`, `fallback_used`, `fallback_reason`) — the frontend's "AMD
  GPU inference" badge only appears when a stage actually ran on AMD in
  that specific run, never based on configuration alone.

Full technical writeup: [AMD.md](AMD.md). Hands-on notebook setup log with
real hardware diagnostics: [`amd/README.md`](../amd/README.md).

## Architecture

See [Architecture.md](Architecture.md) for the full system diagram set.
One-line summary: Next.js frontend (Vercel) → FastAPI backend (persistent
container) → local video/audio/frame processing → Fireworks/AMD vLLM for
AI stages → optional Firebase (accounts) and YouTube Data API (trends +
upload).

## Judging criteria mapping

| Criterion | Where it's demonstrated |
|---|---|
| **Real, non-cosmetic AMD integration** | [AMD.md](AMD.md) — provider abstraction, real benchmark-driven model choice, truthful per-stage audit trail, `GET /api/providers/status` |
| **Technical depth** | Sparse multimodal pipeline ([AI-Pipeline.md](AI-Pipeline.md)), independent generation+ranking architecture, provider fallback with schema-repair retry ([Backend.md](Backend.md)) |
| **Product completeness** | Full auth (optional accounts), YouTube OAuth + real upload, saved artifacts, production deployment — not a notebook demo ([Deployment.md](Deployment.md)) |
| **Honesty about tradeoffs** | Known limitations documented plainly, not hidden — in-memory job state, Railway memory constraint, OAuth Testing-mode restriction ([Deployment.md](Deployment.md), [Troubleshooting.md](Troubleshooting.md)) |
| **Code quality / maintainability** | Typed schemas end-to-end (Pydantic ↔ TypeScript), mocked test suite covering the provider abstraction and every auth boundary, documented architecture ([DeveloperGuide.md](DeveloperGuide.md)) |
| **Usability** | Live deployed app, demo mode requiring no backend, clear processing/results UI ([Frontend.md](Frontend.md)) |

## Demo walkthrough

See [DEMO_SCRIPT.md](DEMO_SCRIPT.md) for the timed 3-minute live-demo
script, and [DEMO_CHECKLIST.md](DEMO_CHECKLIST.md) for the pre-flight
operational checklist (AMD notebook/tunnel state, OAuth test users, etc.)
to run through before presenting.

## Known limitations (stated plainly)

This is a hackathon-scope submission, not a hardened production system.
The full list, with rationale for each: [Deployment.md § the real memory
constraint](Deployment.md#the-real-memory-constraint) and
[Backend.md](Backend.md) for the in-memory state constraints. Short
version: job/session state is in-memory and single-instance by design; a
small-plan cloud host can OOM on longer videos (mitigations documented,
not hidden); the AMD notebook allocation is time-bound, not permanent
infrastructure, with automatic Fireworks fallback when it isn't running.
