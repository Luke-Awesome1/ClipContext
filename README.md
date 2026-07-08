# ClipContext

AI-powered video understanding and metadata generation. Upload a short
video; ClipContext analyzes its speech and visual content, cross-references
current YouTube trends and (optionally) a creator's own channel patterns,
and generates ranked candidate titles, descriptions, and hashtag sets.

Built for the lablab.ai AMD Developer Hackathon (ACT II, Track 3).

## Architecture

```
Frontend (Next.js)
      │  multipart upload: video + creator handle + platform
      ▼
POST /api/jobs  ──▶  job_id (background thread starts immediately)
      │
GET /api/jobs/{id}  (poll every ~1.5s)
      ▼
FastAPI backend (src/api/)
      │
      ▼
Pipeline service (src/pipeline/runner.py) — the SAME function the CLI calls
      │
      ├─ validate ─▶ extract audio ─▶ scan frames ─▶ transcribe (local Whisper)
      ├─ temporal alignment ─▶ visual analysis (Fireworks Kimi vision)
      ├─ VideoContext generation (Fireworks Kimi)
      ├─ worldwide trend analysis (YouTube Data API + Fireworks MiniMax)
      ├─ creator trend analysis (optional — skipped if no handle given)
      ├─ content generation: 10 titles / 10 descriptions / 10 hashtag sets
      └─ discriminator: independently ranks each of the three pools
      ▼
PipelineResult persisted to outputs/<job_id>/ and outputs/_cache/<video_hash>/
      ▼
Results page renders ranked candidates; user picks title/description/
hashtags independently of one another.
```

Key design points:

- **CLI and API share one pipeline.** `main.py` and `src/api/jobs.py` both
  call `run_pipeline()` in `src/pipeline/runner.py`. There is no duplicated
  business logic.
- **Two-tier caching.** Transcription, visual timeline, and VideoContext are
  cached by a hash of the video's bytes under `outputs/_cache/<video_hash>/`
  — re-uploading the same video is free. Trends/syntax/generated
  content/rankings depend on creator handle + platform, so they live under
  `outputs/<job_id>/`, where `job_id` is a deterministic hash of
  `(video_hash, platform, creator_handle)`.
- **Independent candidate pools.** Titles, descriptions, and hashtag sets
  are ranked independently by the discriminator (`src/models/discriminator/`).
  Candidate id 3 in titles has no relationship to id 3 in descriptions.
- **In-memory job registry.** `src/api/jobs.py` keeps job state in a
  lock-guarded dict, not a database. See [Known limitations](#known-limitations).

## Repository structure

```
main.py                    Thin CLI wrapper over the pipeline service
requirements.txt           Backend Python dependencies
Dockerfile                 Backend container image

src/
  api/                     FastAPI app, routes, job registry, API schemas
  pipeline/                Reusable pipeline service (paths, schemas, runner)
  video/                   Local video validation, audio/frame extraction
  ai/                      Transcription, temporal alignment, context
                           building, content generation, Fireworks client
  models/                  Pydantic schemas (VideoContext, GeneratedContent,
                           discriminator ranking)
  trends/                  Worldwide + creator YouTube trend analysis
  prompts/                 Content generation system prompt

frontend/
  app/                     Next.js App Router pages (/, /process, /results)
  components/              UI components
  context/                 VideoSessionContext (job id, session recovery)
  lib/                     api.ts (backend client), useJobPolling hook
  types/                   TypeScript types matching backend schemas

tests/                     pytest suite (mocked external calls)
data/                      Runtime video/audio/frame artifacts (gitignored)
outputs/                   Runtime pipeline output (gitignored)
```

## Prerequisites

- Python 3.13 (tested; 3.12 should also work). Python 3.14 is not
  recommended — some scientific/ML dependencies lag behind on wheel support.
- Node.js 20+ (tested with Node 25 / npm 11).
- FFmpeg (`ffmpeg` and `ffprobe` on `PATH`) — required for audio extraction
  and video validation.
- API keys: Fireworks AI, YouTube Data API v3, Google Gemini (see below).

## Environment variables

Copy `.env.example` to `.env` at the repo root and fill in the required
keys. See that file for the full list; the required ones are:

| Variable | Service | Notes |
|---|---|---|
| `FIREWORKS_API_KEY` | Fireworks AI | Kimi (vision + context + generation), MiniMax (trend syntax + discriminator) |
| `YOUTUBE_API_KEY` | YouTube Data API v3 | Trend/creator video lookup |
| `GEMINI_API_KEY` | Google AI Studio | Reserved for the Gemini vision fallback path (`src/ai/vision/gemma.py`) |

Optional (sane defaults applied if unset): `ALLOWED_ORIGINS`,
`MAX_UPLOAD_SIZE_MB`, `PORT`.

The frontend needs its own `frontend/.env.local` (copy from
`frontend/.env.local.example`) with `NEXT_PUBLIC_API_BASE_URL`.

## Local setup

```bash
git clone <repo>
cd act2-captioner

python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env            # then fill in the three API keys
cd frontend && npm ci && cd ..
cp frontend/.env.local.example frontend/.env.local
```

Or simply `make setup` (does the same, minus filling in secrets).

## Running locally

```bash
# terminal 1
make backend        # uvicorn src.api.app:app --reload --port 8000

# terminal 2
make frontend        # next dev, http://localhost:3000
```

Visit `http://localhost:3000`, upload a 30s–2min video, optionally provide
a YouTube channel URL for creator-specific personalization, and follow the
upload → processing → results flow.

## CLI usage

```bash
.venv/bin/python main.py path/to/video.mp4 --creator @somecreator --platform youtube
# --creator is optional; omitting it skips creator trend analysis and
# generation falls back to worldwide syntax.
```

## API endpoints

- `GET /health` — liveness check.
- `POST /api/jobs` — multipart form: `video` (file), `creator_handle`
  (optional string), `platform` (`youtube` | `web`, default `youtube`).
  Returns `{ job_id, status }` immediately; processing runs in a background
  thread.
- `GET /api/jobs/{job_id}` — current status. While processing:
  `{ job_id, status, stage, progress, message, result: null, error: null }`.
  On completion, `result` holds the full `PipelineResult` (VideoContext
  summary, generated content, independent rankings). On failure, `error`
  holds a sanitized, user-safe message (raw exceptions are logged
  server-side only, never returned to the client).

## Testing

```bash
make test    # pytest tests/ — paths, job registry, API validation, schemas
             # all external AI/YouTube calls are mocked
```

The frontend build (`npm run build`) runs type-checking and linting as part
of the Next.js build step.

## Docker deployment (backend)

```bash
docker build -t clipcontext-backend .
docker run -p 8000:8000 --env-file .env clipcontext-backend
```

The image installs `ffmpeg`, binds to `0.0.0.0`, and honors `$PORT` if the
host injects one (Cloud Run, Railway, Fly.io, etc.). No secrets are baked
into the image — pass them at runtime via environment variables.

Because the pipeline does real filesystem work (ffmpeg subprocess calls,
job artifact storage) and runs long background jobs in-process, deploy it
to a **persistent container host**, not a short-lived serverless function.

## Frontend deployment

`npm run build` in `frontend/` produces a standard Next.js production
build, deployable to Vercel or any Node host. Set
`NEXT_PUBLIC_API_BASE_URL` to the deployed backend's URL, and set the
backend's `ALLOWED_ORIGINS` to include the deployed frontend's origin.

## Known limitations (hackathon scope)

- **Job state is in-memory only.** A backend restart loses in-flight job
  tracking (queued/processing jobs disappear from `GET /api/jobs/{id}`,
  returning 404). Completed job *artifacts* are unaffected — they're on
  disk under `outputs/<job_id>/`, just not re-discoverable via the API
  without re-running the pipeline through `main.py` or re-uploading.
- **No per-job cancellation.** Once started, a background job runs to
  completion or failure; there's no cancel endpoint.
- **No incremental caching within visual analysis.** If the pipeline fails
  partway through the multi-window visual analysis stage, the
  already-completed windows are not cached — a retry re-analyzes all
  windows (and re-spends Fireworks credits on that stage).
- **Creator handle changes don't invalidate video-level cache** but do
  produce a different `job_id` (since job_id folds in the handle), so
  re-running the same video with a different creator handle correctly
  triggers fresh trend/generation/ranking work while reusing the free,
  cached transcription/visual/context artifacts.
- **Uploaded video files are not automatically cleaned up.** They persist
  under `data/videos/uploads/` indefinitely; add a retention job before
  any real deployment with meaningful traffic.
- Two Fireworks model families are referenced with slightly different
  MiniMax model IDs across `src/trends/worldwide_analyzer.py` (its own
  local constant) and `src/trends/trend_analyzer.py` /
  `src/models/discriminator/discriminator.py` (via `src/ai/fireworks/client.py`).
  Both were left as-is (each presumably already validated against
  Fireworks) rather than guessed into alignment — verify against your
  Fireworks account before changing either.

## Troubleshooting

- **`FIREWORKS_API_KEY is not set`** — copy `.env.example` to `.env` and
  fill in the key; restart the backend.
- **`ffprobe`/`ffmpeg: command not found`** — install FFmpeg
  (`brew install ffmpeg` on macOS) and ensure it's on `PATH`.
- **CORS errors in the browser console** — set `ALLOWED_ORIGINS` in the
  backend `.env` to include the frontend's origin, then restart the
  backend.
- **YouTube quota/HTTP errors** — the trend analyzers surface a sanitized
  `RuntimeError` describing the HTTP status; check your `YOUTUBE_API_KEY`
  quota in Google Cloud Console.
- **"Kimi returned no JSON object"** — the vision model occasionally emits
  a very long `visible_text` list (e.g. a poster full of text) that
  overruns `MAX_OUTPUT_TOKENS` in `src/ai/fireworks/multimodal.py`,
  truncating the JSON response mid-object. Increase that constant if you
  see this on real footage.
