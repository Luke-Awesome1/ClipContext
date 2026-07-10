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
   export AMD_VLLM_MODEL="Qwen/Qwen2.5-7B-Instruct"
   export MAX_MODEL_LEN=16384
   export GPU_MEMORY_UTILIZATION=0.88
   export AMD_VLLM_API_KEY="<a-random-string-you-generate>"   # recommended
   bash amd/start_vllm.sh
   ```
   If a `Qwen2.5-14B-Instruct` server is already running from an earlier
   step, stop it first (`Ctrl+C` in its session, or `tmux kill-session -t
   vllm`) — only one model can be loaded at a time on a single GPU. First
   start of a new model downloads from Hugging Face (~15 GiB for 7B) —
   watch for `Uvicorn running on http://0.0.0.0:8000` before moving on.
6. From the notebook's own terminal (a second one, since the first is
   running the server in the foreground), confirm it serves usable
   completions over localhost before worrying about external reachability:
   ```bash
   AMD_VLLM_BASE_URL="http://localhost:8000/v1" \
   AMD_VLLM_MODEL="Qwen/Qwen2.5-7B-Instruct" \
   AMD_VLLM_API_KEY="<same-key>" \
   /opt/venv/bin/python amd/smoke_test.py
   ```
7. Run the representative ClipContext benchmark (same code path the real
   pipeline uses), still over localhost:
   ```bash
   AMD_VLLM_BASE_URL="http://localhost:8000/v1" \
   AMD_VLLM_MODEL="Qwen/Qwen2.5-7B-Instruct" \
   AMD_VLLM_API_KEY="<same-key>" \
   /opt/venv/bin/python amd/benchmark_amd.py
   ```
8. Point the real backend at it (repo root `.env`, **not** the notebook —
   see [Network access](#network-access) for how `<notebook-host-or-tunnel>`
   gets resolved, since this notebook's port is not necessarily reachable
   from outside as-is). Only `content_generation` defaults to AMD for the
   demo — see [AMD stage scope for the demo](#amd-stage-scope-for-the-demo):
   ```
   AMD_VLLM_BASE_URL=http://<notebook-host-or-tunnel>:8000/v1
   AMD_VLLM_MODEL=Qwen/Qwen2.5-7B-Instruct
   AMD_VLLM_API_KEY=<same-key>
   CONTENT_GENERATION_PROVIDER=amd_vllm
   CONTENT_GENERATION_FALLBACK_PROVIDER=fireworks
   # DISCRIMINATOR_PROVIDER left unset -> defaults to fireworks; set to
   # amd_vllm too only for an extended non-timed technical walkthrough.
   ```
9. Restart the backend, run a real video through the pipeline, and check
   `GET /api/providers/status` and the completed job's `ai_audit` field
   (`outputs/<job_id>/ai_provider_audit.json`) for `provider_used:
   "amd_vllm"` and `fallback_used: false` on the `content_generation` stage.

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

**Chosen model: `Qwen/Qwen2.5-7B-Instruct`** (revised down from 14B after a
real benchmark — see [Why 7B, not 14B](#why-7b-not-14b) below).

- **Ungated** — no Hugging Face access request, no `HF_TOKEN` needed.
  (Gemma was considered and rejected: Gemma models are gated on Hugging
  Face, requiring a license click-through and a granted `HF_TOKEN` before
  anything downloads — extra setup for no proven speed or JSON-reliability
  win over a family already validated end-to-end on this exact stack.)
- **`Qwen2ForCausalLM` is a long-supported vLLM architecture**, including
  on ROCm, and was already proven working (download, load, inference,
  native structured JSON) at 14B on this exact notebook/vLLM build before
  being resized down — lower risk than switching model families under time
  pressure.
- **Strong structured-JSON instruction-following**, which both
  AMD-eligible stages depend on (`GeneratedContent`'s exact 10/10/10 +
  sequential-id schema, `DiscriminatorResult`'s ranking schema) — confirmed
  directly: the 14B variant produced valid `GeneratedContent` JSON via
  native `response_format: json_schema` on the first real request, no
  fallback or repair retry needed.
- **Context window**: native 32K, far more than either stage's real prompt
  needs. `MAX_MODEL_LEN=16384` caps KV cache allocation to what's actually
  used.

```bash
export AMD_VLLM_MODEL="Qwen/Qwen2.5-7B-Instruct"
export MAX_MODEL_LEN=16384
export GPU_MEMORY_UTILIZATION=0.88
```

### Why 7B, not 14B

A real `amd/benchmark_amd.py` run against `Qwen2.5-14B-Instruct` on this
notebook measured **72.2s latency, 978 completion tokens, 13.5 tok/s**. The
vLLM startup log showed why: CUDA graphs captured successfully
(`enforce_eager=False`, graph capture finished cleanly in 18s) — the
bottleneck is `Using Triton Attention backend`, vLLM's portable-but-generic
attention kernel. vLLM's most optimized ROCm attention kernels target the
CDNA datacenter cards (MI200/MI300); on this card's `gfx1100` (RDNA3)
architecture, Triton is the auto-selected fallback. Back-of-envelope: a 14B
bf16 model reads ~28 GiB of weights per decode step at batch size 1, which
against this card's memory bandwidth puts a rough single-stream ceiling
around 25–30 tok/s even in ideal conditions — 13.5 tok/s is in a plausible
range for that ceiling with a non-fused attention kernel, not evidence of a
misconfiguration to keep chasing.

At 72s per call, running both AMD-eligible stages live would add roughly
2.5–4 minutes to a 2–5 minute demo. **Confirmed by a real
`amd/benchmark_amd.py` run against `Qwen2.5-7B-Instruct`: 38.5s latency,
1219 completion tokens, 31.6 tok/s** — 2.3x the 14B throughput, close to
the back-of-envelope memory-bandwidth prediction. Still real GPU inference
on a non-trivial 7B model, sized for a live demo instead of offline batch
quality.

An AWQ/GPTQ int4-quantized 14B build was considered and set aside for now:
it could plausibly claim back more throughput than resizing to 7B, but
needs a compatible pre-quantized checkpoint and unproven quantized-kernel
support on `gfx1100` — real risk to take on this close to a demo, versus
resizing within an already-proven model family.

### AMD stage scope for the demo

Only `CONTENT_GENERATION_PROVIDER=amd_vllm` is set by default — the
judge-visible "10 titles / 10 descriptions / 10 hashtag sets" stage runs on
AMD. `DISCRIMINATOR_PROVIDER` is left unset (defaults to `fireworks`),
keeping the discriminator on the already-fast, already-validated Fireworks
path rather than adding a second AMD wait (its `max_tokens` ceiling is
higher, so its worst-case latency is worse than `content_generation`'s) to
the demo's critical path. Both stages remain fully code-supported on AMD —
set `DISCRIMINATOR_PROVIDER=amd_vllm` too for an extended technical
walkthrough or Q&A outside the timed demo.

RDNA3 note: if the server hangs or errors during CUDA-graph capture at
startup on a future run, add `--enforce-eager` to `amd/start_vllm.sh`'s
`ARGS` (eager mode trades some throughput for skipping graph capture) —
not needed for the run recorded above, capture succeeded cleanly.

## Network access

**Confirmed on the allocated notebook: no direct public port.** The
notebook sits behind an isolated internal proxy
(`radeon-global.anruicloud.com`) with no raw external IP/hostname mapped to
port 8000 or any other arbitrary TCP port — only Jupyter's own HTTP(S)
proxy is exposed. `AMD_VLLM_BASE_URL` cannot point directly at the
notebook; a tunnel is required for the deployed backend to reach it.

**Chosen mechanism: Cloudflare Tunnel, quick-tunnel mode.** No Cloudflare
account required — appropriate for a time-boxed hackathon demo rather than
long-lived infrastructure, which matches what this actually is.

On the notebook, in a new terminal/tmux session (separate from the one
running vLLM):

```bash
tmux new -s tunnel
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
chmod +x cloudflared
./cloudflared tunnel --url http://localhost:8000
```

`cloudflared` prints a line like:

```
https://random-two-words.trycloudflare.com
```

That URL is a plain HTTPS reverse proxy to `localhost:8000` on the
notebook — it does not add its own authentication layer, which is exactly
why `AMD_VLLM_API_KEY` / `--api-key` on the vLLM server (already set in
step 5 above) is the thing actually protecting this endpoint from
unauthenticated use. Verify from *outside* the notebook (your own laptop,
or the Railway backend once deployed) before wiring it in:

```bash
curl -m 5 https://random-two-words.trycloudflare.com/v1/models \
  -H "Authorization: Bearer <AMD_VLLM_API_KEY>"
```

Then set on the backend (Railway, once deployed — see root `README.md`):

```
AMD_VLLM_BASE_URL=https://random-two-words.trycloudflare.com/v1
AMD_VLLM_API_KEY=<same key the vLLM server was started with>
AMD_VLLM_MODEL=Qwen/Qwen2.5-7B-Instruct
CONTENT_GENERATION_PROVIDER=amd_vllm
CONTENT_GENERATION_FALLBACK_PROVIDER=fireworks
```

**Known tradeoffs of quick-tunnel mode**, both acceptable for a demo and
worth knowing about:

- The URL is ephemeral — it changes every time `cloudflared` restarts.
  Start it well before the demo, keep that tmux session alive, and re-check
  `GET /api/providers/status` on the deployed backend shortly before
  presenting rather than assuming a URL set hours earlier is still live.
- No SLA/uptime guarantee on a quick tunnel. If it drops mid-demo, that's
  exactly the scenario `CONTENT_GENERATION_FALLBACK_PROVIDER=fireworks`
  exists for — the pipeline keeps working, `provider_used` in `ai_audit`
  just becomes `"fireworks"` for that run instead of `"amd_vllm"`, honestly.
- Never commit the tunnel URL or `AMD_VLLM_API_KEY` to the repository —
  both belong only in the backend host's environment-variable manager.

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
