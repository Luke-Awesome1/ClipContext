# ClipContext on AMD (ROCm + vLLM)

This directory is the AMD hackathon inference service for ClipContext's
lablab.ai AMD Developer Hackathon (ACT II, Track 3) submission. It is
**GPU compute for two specific pipeline stages**, not a hosting target for
the public application — see [Architecture](#architecture) for why.

## Architecture

```
Browser
  │
  ▼
Next.js frontend (Vercel or similar — see repo root README.md)
  │
  ▼
FastAPI backend (persistent container host — Railway/Fly/Render/Cloud Run)
  │
  ├─ Video pipeline (validation, ffmpeg, local Whisper transcription)
  ├─ Fireworks Kimi vision (visual timeline, VideoContext — untouched)
  ├─ YouTube Data API (trend analysis)
  │
  ├─ content_generation stage ──▶ src/ai/providers/orchestrator.py
  │                                        │
  ├─ discriminator stage ────────▶ (same orchestrator, different stage)
  │                                        │
  │                          CONTENT_GENERATION_PROVIDER /
  │                          DISCRIMINATOR_PROVIDER = amd_vllm
  │                                        │
  │                                        ▼
  │                          AMD vLLM OpenAI-compatible server  ◀── (this directory)
  │                                        │
  │                                        ▼
  │                                    PyTorch / ROCm / HIP
  │                                        │
  │                                        ▼
  │                                     AMD GPU
  │
  └─ Fireworks fallback (CONTENT_GENERATION_FALLBACK_PROVIDER /
     DISCRIMINATOR_FALLBACK_PROVIDER — default "fireworks")
```

**The browser never talks to the AMD endpoint.** Only the FastAPI backend
does, via `AMD_VLLM_BASE_URL` in its own environment. See
`src/ai/providers/amd_vllm.py`.

### Why only two stages run on AMD

`content_generation` (10 titles / 10 descriptions / 10 hashtag sets) and
`discriminator` (independent ranking of each pool) are the only two
ClipContext AI stages that are (a) text-only — no image input — and (b)
structured-JSON output validated against a Pydantic schema
(`src/models/generated_content.py`, `src/models/discriminator/schemas.py`).
Both already called Fireworks with an OpenAI-compatible client
(`src/ai/content_generator.py`, `src/models/discriminator/discriminator.py`)
before this integration, so pointing them at another OpenAI-compatible
server is a provider swap, not a pipeline rewrite.

Visual understanding (`src/ai/fireworks/multimodal.py`,
`src/ai/vision/gemma.py`) and `VideoContext` synthesis
(`src/ai/context_builder.py`) are **not** AMD-eligible: they require image
input, and the AMD notebook's vLLM instance serves one text model, not a
vision-language model.

### Why the AMD notebook is not the public hosting target

The AMD AI Notebook portal describes the GPU allocation as time-bound —
runtime-limited, not a permanent externally-reachable production service.
Building the public ClipContext deployment so it *requires* the notebook to
be running would make the hackathon demo fragile and would misrepresent the
notebook as production infrastructure it isn't. Instead:

- The public backend/frontend deploy independently (repo root `README.md`).
- `CONTENT_GENERATION_PROVIDER=amd_vllm` / `DISCRIMINATOR_PROVIDER=amd_vllm`
  are **only** set in the backend's environment while the notebook is up
  for a demo.
- If the AMD endpoint is unreachable, the pipeline falls back to Fireworks
  automatically and truthfully (see [Fallback and audit](#fallback-and-audit-truthfulness))
  — the app keeps working either way.

## Setup on the AMD AI Notebook

1. Open the AMD AI Notebooks portal, select **ROCm 7.2 + vLLM 0.16.0 +
   PyTorch 2.9**, click **Request Notebook**, and wait for Jupyter to
   launch.
2. Open a terminal inside the notebook (not a `.ipynb` cell — this
   directory is meant to run from a shell so it's reproducible outside
   Jupyter too).
3. Clone or pull this repository inside the notebook:
   ```bash
   git clone <this-repo-url> clipcontext
   cd clipcontext
   ```
4. Run the diagnostic script and confirm the GPU is actually visible:
   ```bash
   python amd/verify_rocm.py
   ```
   This must show a real GPU under `torch.cuda.get_device_name(0)` and a
   loaded `vllm` module before continuing. If it doesn't, stop and fix the
   notebook environment before starting the server — do not guess a model
   choice against an environment that can't see the GPU.
5. Only after real GPU/VRAM numbers are known: pick a model (see
   [Model selection](#model-selection)) and start the server:
   ```bash
   export AMD_VLLM_MODEL="<chosen-model-id>"
   export AMD_VLLM_API_KEY="<a-random-string-you-generate>"   # recommended
   bash amd/start_vllm.sh
   ```
6. From a machine that can reach the notebook (see
   [Network access](#network-access)), confirm it actually serves usable
   completions:
   ```bash
   AMD_VLLM_BASE_URL="http://<notebook-host>:8000/v1" \
   AMD_VLLM_MODEL="<chosen-model-id>" \
   AMD_VLLM_API_KEY="<same-key>" \
   python amd/smoke_test.py
   ```
7. Run the representative ClipContext benchmark (same code path the real
   pipeline uses):
   ```bash
   AMD_VLLM_BASE_URL="http://<notebook-host>:8000/v1" \
   AMD_VLLM_MODEL="<chosen-model-id>" \
   AMD_VLLM_API_KEY="<same-key>" \
   python amd/benchmark_amd.py
   ```
8. Point the real backend at it (repo root `.env`, **not** the notebook):
   ```
   AMD_VLLM_BASE_URL=http://<notebook-host-or-tunnel>:8000/v1
   AMD_VLLM_MODEL=<chosen-model-id>
   AMD_VLLM_API_KEY=<same-key>
   CONTENT_GENERATION_PROVIDER=amd_vllm
   CONTENT_GENERATION_FALLBACK_PROVIDER=fireworks
   DISCRIMINATOR_PROVIDER=amd_vllm
   DISCRIMINATOR_FALLBACK_PROVIDER=fireworks
   ```
9. Restart the backend, run a real video through the pipeline, and check
   `GET /api/providers/status` and the completed job's `ai_audit` field
   (`outputs/<job_id>/ai_provider_audit.json`) for `provider_used:
   "amd_vllm"` and `fallback_used: false` on both stages.

Do not run the Next.js frontend, Firebase, or the public FastAPI backend on
the notebook itself — it's inference compute only.

## Model selection

Not finalized in this repository revision — selecting a model **before**
seeing real `amd/verify_rocm.py` output (GPU model, VRAM, vLLM/ROCm/PyTorch
versions actually loaded) would be a guess, not an engineering decision.
Once that output is available, the choice is evaluated against:

- available VRAM vs. model parameter count/precision
- vLLM 0.16.0 + ROCm compatibility for that model architecture
- whether it's gated on Hugging Face (requires `HF_TOKEN`) or open
- structured-JSON-output reliability (matters for both AMD-eligible stages)
- context window vs. the longest real prompt (`discriminator` sends the
  full candidate pool + video context + trend benchmarks — larger than
  `content_generation`'s prompt)
- generation latency at the sparse candidate counts ClipContext needs (10 +
  10 + 10 items, or a ranking pass over 30 items)

If a gated model turns out to be the best fit, `amd/start_vllm.sh` reads
`HF_TOKEN` from the environment automatically (vLLM's own Hugging Face
download path does) — set it in the notebook's own environment, never in
this repository, and never paste the token value into chat.

## Network access

**Not yet verified against the real notebook.** Before pointing the
production backend at `AMD_VLLM_BASE_URL`, confirm from a terminal *outside*
the notebook whether the notebook's port is directly reachable:

```bash
curl -m 5 http://<notebook-host>:8000/v1/models
```

- If that succeeds, `AMD_VLLM_BASE_URL` can point directly at the notebook.
- If it doesn't (most managed notebook environments only expose a Jupyter
  proxy, not arbitrary TCP ports), the vLLM server needs a tunnel. Do not
  install a random tunneling tool unprompted — if a tunnel is required,
  the two reasonable options are:
  - **Cloudflare Tunnel** (`cloudflared`) — no account required for a
    temporary quick tunnel; ask before installing if you'd prefer a named,
    authenticated tunnel instead.
  - **ngrok** — requires an ngrok account/authtoken; only set this up if
    you tell me to and provide the authtoken via ngrok's own config, never
    pasted into chat.
- Whichever mechanism is used, set `AMD_VLLM_API_KEY` and keep
  `--api-key` set on the vLLM server (`amd/start_vllm.sh` already warns if
  it's unset) — an exposed, unauthenticated GPU inference endpoint is a
  cost and abuse risk. Never commit the tunnel URL or the API key.

## Fallback and audit truthfulness

`src/ai/providers/orchestrator.py` is the single place that decides which
provider actually handled a stage, and it is the only source of truth for
the `provider_used` field the frontend is allowed to read. If AMD vLLM is
unreachable (`ProviderUnavailableError`: connection refused, timeout, 5xx)
or returns output that never becomes schema-valid even after one repair
retry (`ProviderResponseError`), the stage falls back to the configured
fallback provider and the audit records:

```json
{
  "stage": "content_generation",
  "provider_requested": "amd_vllm",
  "provider_used": "fireworks",
  "fallback_used": true,
  "fallback_reason": "provider_unreachable"
}
```

The frontend (`frontend/components/AIUnderstandingCard.tsx`) only renders
an "AMD GPU inference" indicator when `provider_used === "amd_vllm"` for
that stage — never based on `provider_requested` alone, and never for a
stage that fell back.

## Files

| File | Purpose |
|---|---|
| `verify_rocm.py` | Run first, on the notebook. Confirms ROCm/PyTorch/vLLM see the GPU. |
| `start_vllm.sh` | Starts the OpenAI-compatible vLLM server with explicit, env-driven configuration. |
| `smoke_test.py` | Run from any machine that can reach the server. Confirms plain + structured-JSON completions work. |
| `benchmark_amd.py` | Runs the real `content_generation` prompt/schema against AMD directly; reports real latency/tokens, never fabricated. |

## Verifying AMD execution as a judge

```bash
curl https://<deployed-backend>/api/providers/status
```

Shows, per stage, which provider is configured and whether it's currently
reachable (no secrets, no endpoint URL). After running a real video through
the deployed app, the completed job's result includes `ai_audit`, an array
with one entry per AI-inference stage recording `provider_requested`,
`provider_used`, `model`, `hardware`, `latency_ms`, and `fallback_used` —
this is the authoritative record of whether that specific run actually
executed on the AMD GPU.
