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
4. Run the diagnostic script and confirm the GPU is actually visible.
   **Use the venv that actually has torch/vllm installed** — on the
   allocated notebook this was `/opt/venv` (system `python`/`python3` on
   `PATH` does not have them; check with `python3 -c "import vllm"` first
   if you're on a different notebook instance):
   ```bash
   /opt/venv/bin/python amd/verify_rocm.py
   ```
   This must show a real GPU under `torch.cuda.get_device_name(0)` and a
   loaded `vllm` module before continuing. If it doesn't, stop and fix the
   notebook environment before starting the server — do not guess a model
   choice against an environment that can't see the GPU.
5. Start the server with the model already selected in
   [Model selection](#model-selection):
   ```bash
   source /opt/venv/bin/activate
   export AMD_VLLM_MODEL="Qwen/Qwen2.5-14B-Instruct"
   export MAX_MODEL_LEN=16384
   export GPU_MEMORY_UTILIZATION=0.88
   export AMD_VLLM_API_KEY="<a-random-string-you-generate>"   # recommended
   bash amd/start_vllm.sh
   ```
   First start downloads ~29 GiB from Hugging Face — expect several minutes
   depending on the notebook's outbound bandwidth. Watch for `Uvicorn
   running on http://0.0.0.0:8000` before moving on.
6. From the notebook's own terminal (a second one, since the first is
   running the server in the foreground), confirm it serves usable
   completions over localhost before worrying about external reachability:
   ```bash
   AMD_VLLM_BASE_URL="http://localhost:8000/v1" \
   AMD_VLLM_MODEL="Qwen/Qwen2.5-14B-Instruct" \
   AMD_VLLM_API_KEY="<same-key>" \
   /opt/venv/bin/python amd/smoke_test.py
   ```
7. Run the representative ClipContext benchmark (same code path the real
   pipeline uses), still over localhost:
   ```bash
   AMD_VLLM_BASE_URL="http://localhost:8000/v1" \
   AMD_VLLM_MODEL="Qwen/Qwen2.5-14B-Instruct" \
   AMD_VLLM_API_KEY="<same-key>" \
   /opt/venv/bin/python amd/benchmark_amd.py
   ```
8. Point the real backend at it (repo root `.env`, **not** the notebook —
   see [Network access](#network-access) for how `<notebook-host-or-tunnel>`
   gets resolved, since this notebook's port is not necessarily reachable
   from outside as-is):
   ```
   AMD_VLLM_BASE_URL=http://<notebook-host-or-tunnel>:8000/v1
   AMD_VLLM_MODEL=Qwen/Qwen2.5-14B-Instruct
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

**Finalized against real hardware diagnostics** from the allocated
notebook (`amd/verify_rocm.py`):

| | |
|---|---|
| GPU | AMD Radeon PRO W7900-class, `gfx1100` (RDNA3), single card |
| VRAM | 48 GiB (`torch.cuda.get_device_properties(0).total_memory`) |
| ROCm / HIP | 7.2.53211 |
| PyTorch | 2.9.1 (ROCm build) |
| vLLM | 0.16.1.dev0 (ROCm721 build), installed at `/opt/venv` |
| Free disk | ~93 GiB under `/workspace` |
| RAM | 503 GiB (485 GiB free) |

**Chosen model: `Qwen/Qwen2.5-14B-Instruct`.**

- **Ungated** — no Hugging Face access request, no `HF_TOKEN` needed.
  Simpler hackathon setup, and there was no quality reason to pay the
  gated-model tax here.
- **Fits VRAM with real headroom**: ~29 GiB weights in bf16 against 48 GiB
  VRAM leaves ~19 GiB for KV cache — generous for ClipContext's prompt
  sizes (see `MAX_MODEL_LEN` below).
- **Fits the 93 GiB disk budget with margin.** A 30B+ model in bf16 (~60+
  GiB steady state, and roughly double that at download peak while the
  temp file and the final cached copy briefly coexist) would have been too
  close to the disk ceiling for a live-demo-critical download. 14B leaves
  headroom.
- **`Qwen2ForCausalLM` is a long-supported vLLM architecture**, including
  on ROCm — lower integration risk than a newer/less-tested architecture on
  RDNA3, where vLLM's ROCm attention-kernel support is less mature than on
  the CDNA datacenter cards (MI200/MI300).
- **Strong structured-JSON instruction-following** at 14B, which both
  AMD-eligible stages depend on (`GeneratedContent`'s exact 10/10/10 +
  sequential-id schema, `DiscriminatorResult`'s ranking schema).
- **Context window**: native 32K (Qwen2.5's default), far more than either
  stage's real prompt needs — `discriminator` sends the largest prompt
  (full 30-candidate pool + video digest + trend benchmarks), still well
  under 8K tokens in practice. `MAX_MODEL_LEN=16384` (set below) caps KV
  cache allocation to what's actually needed rather than reserving VRAM for
  32K of context nothing here uses.

```bash
export AMD_VLLM_MODEL="Qwen/Qwen2.5-14B-Instruct"
export MAX_MODEL_LEN=16384
export GPU_MEMORY_UTILIZATION=0.88
```

RDNA3 note: if the server hangs or errors during CUDA-graph capture at
startup, add `--enforce-eager` to `amd/start_vllm.sh`'s `ARGS` (eager mode
trades some throughput for skipping graph capture, which is the first
thing to try on `gfx1100` if the default path misbehaves) rather than
switching models.

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
