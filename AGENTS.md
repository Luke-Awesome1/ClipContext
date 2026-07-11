# ClipContext — Agent Instructions

This file orients an AI coding agent (or a new human contributor) working
in this repository. It reflects the actual current state of the codebase —
if anything here looks wrong, trust the code and fix this file, not the
other way around.

## What ClipContext is

A web app for short-form video creators: upload a 30s–2min video, and
ClipContext analyzes its speech and visual content, cross-references
current YouTube trends (and optionally a creator's own channel patterns),
and generates 10 candidate titles, 10 descriptions, and 10 hashtag sets,
independently ranked by an AI discriminator, surfacing the top 5 of each
pool to the creator. Built for the lablab.ai AMD
Developer Hackathon (ACT II, Track 3) — two of the AI stages can run on an
AMD GPU via ROCm/vLLM instead of Fireworks.

Full architecture: [docs/Architecture.md](docs/Architecture.md). Pipeline
stage-by-stage: [docs/AI-Pipeline.md](docs/AI-Pipeline.md).

## Before making changes

1. Read [docs/Architecture.md](docs/Architecture.md) for the system shape.
2. Read the specific module(s) you're about to touch and their existing
   tests in `tests/`.
3. Do not redesign a working module unless the task explicitly requires it
   — this codebase has already been through several correctness passes
   (provider fallback, auth boundaries, session handling); a "simpler"
   rewrite is often removing a deliberate safeguard, not dead weight.
4. Do not make paid AI inference calls (Fireworks, AMD vLLM, Gemini) as
   part of exploration — mock them in tests, and only run a real job when
   explicitly asked to validate end-to-end behavior.
5. Preserve Pydantic model contracts in `src/models/` and
   `src/pipeline/schemas.py` unless a schema migration is explicitly
   discussed — the frontend's `frontend/types/*.ts` are hand-kept in sync
   with these, not generated.
6. Never commit secrets. `.env`, `frontend/.env.local`, and any
   `*firebase-adminsdk*.json` / `serviceAccountKey.json` file are
   gitignored — keep it that way. See [docs/Environment.md](docs/Environment.md).

## Non-negotiable invariants

These are safety/trust properties the codebase deliberately maintains —
do not casually remove them while "cleaning up" or "simplifying":

- **The browser never talks to the AMD vLLM endpoint directly.** Only the
  FastAPI backend does, via `AMD_VLLM_BASE_URL` in its own environment.
- **AMD usage is never faked.** `ai_audit` / `provider_used` on a
  `PipelineResult` reflects which provider *actually* handled that stage;
  the frontend's AMD badge (`AIUnderstandingCard.tsx`) only lights up when
  `provider_used === "amd_vllm"` for that specific stage, never on
  `provider_requested` alone. See [docs/AMD.md](docs/AMD.md).
- **ClipContext account login and "Connect with YouTube" are separate
  identity systems** (Firebase UID vs. a `cc_session` cookie tied to
  stored Google OAuth credentials). Never assume they're the same user.
  See [docs/Firebase.md](docs/Firebase.md) and [docs/YouTube.md](docs/YouTube.md).
- **`src/api/jobs.py`'s job registry, and the YouTube session/state/token
  stores in `src/youtube/`, are in-memory by design** — this is why
  `railway.toml` pins `numReplicas = 1`. Do not scale this backend
  horizontally without first adding shared state (Redis, a DB) for both.
- **The YouTube upload video path is always resolved server-side from
  `job_id`**, never accepted as a client-supplied path.
- Anonymous use must keep working with zero optional config: no
  `FIREBASE_PROJECT_ID`, no `GOOGLE_CLIENT_ID`, no AMD vars — upload,
  process, and results must all still work.

## Project layout

See [docs/Architecture.md](docs/Architecture.md) for the full breakdown
with diagrams, and the "Repository structure" section of
[README.md](README.md) for a quick-reference tree.

## Testing

`make test` runs the full pytest suite — all external HTTP calls
(Fireworks, AMD vLLM, YouTube Data API, Firebase Admin) are mocked. No
real network calls, GPU usage, uploads, or Firestore writes happen in
tests. Run it after any change to `src/`.

## Hackathon context

lablab.ai AMD Developer Hackathon, ACT II, Track 3. See
[docs/Hackathon.md](docs/Hackathon.md) for the submission narrative and
judging-criteria mapping. Do not make unverified claims about which
accelerator handled a specific request — the truthful per-stage audit
trail (`ai_audit`) exists precisely so nothing has to be asserted without
evidence.
