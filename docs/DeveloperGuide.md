# Developer Guide

Everything needed to go from `git clone` to a running app with no
questions asked. For the one-page version, see [QUICKSTART.md](../QUICKSTART.md).

## Prerequisites

- Python 3.13 (tested; 3.12 should also work — some scientific/ML
  dependencies lag on 3.14 wheel support).
- Node.js 20+ (tested with Node 25 / npm 11).
- FFmpeg (`ffmpeg` and `ffprobe` on `PATH`) — required for audio
  extraction and video validation. `brew install ffmpeg` on macOS,
  `apt install ffmpeg` on Debian/Ubuntu.
- API keys: Fireworks AI, YouTube Data API v3, Google Gemini. See
  [Environment.md](Environment.md) for where to get each one.

No AMD hardware, Firebase project, or Google OAuth client is required to
run ClipContext locally — those are optional feature areas covered in
[AMD.md](AMD.md), [Firebase.md](Firebase.md), and [YouTube.md](YouTube.md).

## Setup

```bash
git clone <your-fork-or-this-repo-url>
cd act2-captioner
make setup
```

`make setup` creates `.venv`, installs Python dependencies from
`requirements.txt`, runs `npm ci` in `frontend/`, and copies `.env.example`
→ `.env` and `frontend/.env.local.example` → `frontend/.env.local` if they
don't already exist. It does **not** fill in any secrets — open `.env` and
set at minimum:

```
FIREWORKS_API_KEY=...
YOUTUBE_API_KEY=...
GEMINI_API_KEY=...
```

See [Environment.md](Environment.md) for the full variable reference and
what every optional feature needs.

## Running locally

```bash
# terminal 1
make backend     # uvicorn src.api.app:app --reload --port 8000

# terminal 2
make frontend    # next dev, http://localhost:3000
```

Visit `http://localhost:3000`, upload a 30s–2min video, optionally provide
a YouTube channel URL for creator-specific personalization, and follow the
upload → processing → results flow.

### Or: Docker Compose

```bash
docker compose up --build
```

Runs both services with hot-reload: the backend bind-mounts `src/` (edits
take effect via uvicorn's `--reload`), and the frontend bind-mounts the
whole `frontend/` directory (Next.js dev server hot-reloads as usual). Fill
in `.env` and `frontend/.env.local` first, same as the non-Docker path.

### Or: the standalone CLI

For iterating on the pipeline itself without running the API server:

```bash
.venv/bin/python main.py path/to/video.mp4 --creator @somecreator --platform youtube
# --creator is optional; omitting it skips creator trend analysis and
# content generation falls back to worldwide trend syntax instead.
```

This calls the exact same `run_pipeline()` the API uses — useful for fast
iteration on pipeline stages without round-tripping through HTTP/the
frontend. Output goes to `outputs/<job_id>/` and prints the final
`VideoContext` to stdout.

## Testing

```bash
make test
```

Runs the full pytest suite (`tests/`) — paths, job registry, API
validation, schemas, the YouTube OAuth/session/upload suite, the Firebase
auth/artifact suite, and the AI provider abstraction (fallback, audit,
schema-repair-retry). **All external calls are mocked** — Fireworks, AMD
vLLM, the YouTube Data API, and Firebase Admin. No API keys, GPU, real
uploads, or Firestore writes happen when you run tests.

Frontend:

```bash
cd frontend
npm run lint       # eslint (eslint-config-next)
npx tsc --noEmit   # typecheck
npm run build      # also runs typecheck + lint as part of the Next.js build
```

## Linting

```bash
make lint         # frontend eslint
ruff check src main.py   # backend — unused imports, undefined names, syntax errors
```

`ruff` is a dev-only dependency (not in `requirements.txt`, which is the
production install list) — install it with `pip install ruff` if you don't
already have it. Config is in `pyproject.toml`: only correctness rules are
enabled, not formatting — the codebase uses an unusually vertical,
one-argument-per-line style throughout, and running a formatter over it
would produce a huge, low-value diff. Match the surrounding file's style
by hand instead.

## Working on the pipeline

- `src/pipeline/runner.py` is the single source of truth for stage order —
  read it before assuming how something flows.
- Transcription, visual timeline, and `VideoContext` are cached under
  `outputs/_cache/<video_hash>/` — re-processing the same video file
  during development doesn't re-spend AI credits on those stages. Delete
  the relevant cache directory to force a fresh run.
- If you add a new pipeline stage, add it to the `PipelineStage` enum in
  `src/pipeline/schemas.py`, call `_report(progress_callback, ...)` at the
  right point in `run_pipeline()`, and add a matching entry to the
  frontend's stage icon/label mapping in `ProcessingPanel.tsx`.

## Working on AI prompts

Every prompt in the repo is inventoried in
[PROMPT_ENGINEERING.md](PROMPT_ENGINEERING.md), along with the rationale
for its current wording. Read that before changing
`src/prompts/content_generation.py`, `src/models/discriminator/d_prompt.txt`,
or any inline prompt in `src/ai/`. If your change is a deliberate
improvement (not a typo fix), add an entry to that doc explaining what
changed and why — it's the project's running record of prompt-engineering
decisions, not just a one-time audit.

## Working on the AI provider abstraction

`src/ai/providers/` is the one place that knows how to call Fireworks or
AMD vLLM. If you add a third provider, implement the `AIProvider` interface
in `base.py`, register it in `registry.py`, and it becomes available to
any stage via `CONTENT_GENERATION_PROVIDER` / `DISCRIMINATOR_PROVIDER`
with zero changes to `content_generator.py` or `discriminator.py`. See
[AI-Pipeline.md](AI-Pipeline.md) for how the existing two providers plug
in.

## Keeping frontend types in sync

`frontend/types/*.ts` are hand-written to match the backend's Pydantic
models in `src/models/` and `src/pipeline/schemas.py` — there is no code
generation step. If you change a backend schema, update the matching
TypeScript type in the same PR.

## Code conventions

- No speculative abstraction — a bug fix doesn't need a refactor, a
  one-shot script doesn't need a plugin system. See `AGENTS.md` for the
  full list of things not to "clean up" because they're deliberate.
- Comments explain *why*, not *what*. If a comment just restates the code
  above it, it doesn't belong.
- Don't add error handling for scenarios that can't happen — validate at
  system boundaries (user input, external API responses), trust internal
  code.

## Common gotchas while developing

See [Troubleshooting.md](Troubleshooting.md) for the full list — the
short version: forgetting to redeploy after changing a
`NEXT_PUBLIC_*` var (they're baked in at build time), and forgetting FFmpeg
is on `PATH`, are the two most common local-dev snags.
