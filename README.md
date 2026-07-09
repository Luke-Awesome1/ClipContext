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
  api/                     FastAPI app, routes, job registry, API schemas,
                           youtube_routes.py (Connect/Upload to YouTube),
                           artifact_routes.py (Save/My Artifacts),
                           auth_dependencies.py (ClipContext login)
  pipeline/                Reusable pipeline service (paths, schemas, runner)
  video/                   Local video validation, audio/frame extraction
  ai/                      Transcription, temporal alignment, context
                           building, content generation, Fireworks client
  models/                  Pydantic schemas (VideoContext, GeneratedContent,
                           discriminator ranking)
  trends/                  Worldwide + creator YouTube trend analysis
  youtube/                 YouTube OAuth + upload: session, state store,
                           token store, oauth flow, metadata, upload worker
  firebase/                Firebase Admin init, ID token verification, user
                           profile upsert — ClipContext account auth only
  artifacts/               Saved-artifact schemas + Firestore repository
  prompts/                 Content generation system prompt

frontend/
  app/                     Next.js App Router pages (/, /process, /results,
                           /artifacts, /artifacts/[artifactId])
  components/              UI components, incl. YouTubeUploadPanel.tsx,
                           SaveArtifactPanel.tsx, AccountControl.tsx,
                           AuthPromptModal.tsx
  context/                 VideoSessionContext (job id, session recovery),
                           AuthContext (Firebase login state)
  lib/                     api.ts (backend client), firebase.ts (client
                           init), useJobPolling, useYouTubeUploadPolling
  types/                   TypeScript types matching backend schemas,
                           incl. types/youtube.ts, types/artifact.ts

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

YouTube OAuth and upload endpoints are documented separately in
[Connect with YouTube / Upload to YouTube](#connect-with-youtube--upload-to-youtube).

## Connect with YouTube / Upload to YouTube

Once a job's results are ready, a user can connect their own YouTube
account and upload the original analyzed video straight to their channel,
using their selected title/description/hashtag candidates.

### Architecture

```
Results page                                FastAPI backend (src/api/youtube_routes.py)
  │  GET /api/youtube/status  ───────────────▶  looks up credentials for the
  │  ◀─────────────────────── {connected, channel...}   ClipContext session cookie
  │
  │  <a href="…/api/youtube/connect">  ──────▶  creates session (if needed) + OAuth
  │  (full-page navigation)                     `state`, redirects to Google
  │                                                     │
  │                                              user consents on accounts.google.com
  │                                                     │
  │  ◀── redirect: /results?youtube=connected ──  GET /api/youtube/callback validates
  │      or ?youtube=error&code=...               `state`, exchanges the code, fetches
  │                                                the channel (channels.list mine=true),
  │                                                stores credentials server-side
  │
  │  POST /api/jobs/{job_id}/youtube/upload ──▶  resolves the job's original video by
  │  ◀── {upload_id, status: "queued"}            job_id (never a browser-supplied path),
  │                                                starts a background resumable upload
  │  GET /api/youtube/uploads/{upload_id} (poll)  (videos.insert via
  │  ◀── {status, progress, video_id, ...}        google-api-python-client)
```

Key design points:

- **No user-account system existed**, so the YouTube connection is bound to
  an opaque, cryptographically random ClipContext session id in an
  HttpOnly cookie (`src/youtube/session.py`) — not a global token, and
  never one browser's credentials usable by another.
- **OAuth `state` is mandatory, single-use, and expiring**
  (`src/youtube/state_store.py`): generated per connect attempt, bound to
  the session id, consumed exactly once on callback, rejected if missing,
  mismatched, or older than 10 minutes.
- **Server-side, in-memory token storage** (`src/youtube/token_store.py`),
  same tradeoff as the existing job registry: a backend restart disconnects
  every session's YouTube account (users just see "disconnected" and
  reconnect), but nothing ever crosses between sessions. Only the fields
  needed to reconstruct credentials are stored — never returned to the
  browser, never written into `generated_content.json`/`audit_report.json`.
- **Scope**: `youtube.upload` + `youtube.readonly` — `youtube.upload` alone
  was tried first (it's the narrowest scope for `videos.insert`), but the
  live YouTube Data API rejects `channels.list(mine=true)` under that scope
  alone with a 403 `insufficientPermissions`, so `youtube.readonly` is
  included to identify the connected channel. Still well short of the
  broad `youtube` (manage account) scope. Configurable via
  `GOOGLE_OAUTH_SCOPES`.
- **Resumable upload**: `googleapiclient.http.MediaFileUpload(...,
  resumable=True)` in 8MB chunks, `next_chunk()` progress reporting, bounded
  exponential-backoff retry on transient 5xx errors — the original video
  file is never read fully into memory.
- **The video source is always resolved server-side** from `job_id` via
  `resolve_upload_video_path()` — the browser cannot supply a filesystem
  path.
- **Metadata is built fresh per upload** (`src/youtube/metadata.py`):
  selected hashtags are appended to the description with clean spacing,
  and separately turned into deduplicated YouTube tags (leading `#`
  stripped). `generated_content.json` is never mutated.
- **Duplicate-upload protection**: the upload button disables immediately
  on click, and the backend rejects a second `POST .../youtube/upload` for
  the same session+job while one is still queued/uploading
  (`YOUTUBE_UPLOAD_IN_PROGRESS`).

### Required Google Cloud setup

1. Open [Google Cloud Console](https://console.cloud.google.com/) and
   select (or create) the project used for `YOUTUBE_API_KEY`.
2. **APIs & Services > Library** — enable **YouTube Data API v3** (if not
   already enabled).
3. **APIs & Services > OAuth consent screen** (Google Auth Platform) —
   configure it: app name "ClipContext", user support email, appropriate
   audience (External, unless you're using Workspace-internal). While the
   app is in **Testing** mode, add every Google account you'll use to test
   the connect flow under **Test users** — Google will reject OAuth for any
   Google account not on that list.
4. **APIs & Services > Credentials > Create Credentials > OAuth client ID**.
   - Application type: **Web application**.
   - Authorized redirect URIs: add the backend's callback URL exactly.
     - Local dev: `http://localhost:8000/api/youtube/callback`
     - Production: `https://<your-deployed-backend-host>/api/youtube/callback`
   - Authorized JavaScript origins: not required (the OAuth flow is
     server-to-server from the backend; the frontend never calls Google
     directly).
5. Copy the generated **Client ID** and **Client secret** into the backend
   `.env` (repo root, not `frontend/.env.local`):
   ```
   GOOGLE_CLIENT_ID=...
   GOOGLE_CLIENT_SECRET=...
   GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/api/youtube/callback
   ```
   Never paste these into chat, source files, or `.env.example`.

### Environment variables

See `.env.example` for the full annotated list. Summary:

| Variable | Required | Notes |
|---|---|---|
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | For the YouTube feature | From the OAuth client above. Without these, everything else in ClipContext still works; `/api/youtube/connect` returns `YOUTUBE_OAUTH_NOT_CONFIGURED`. |
| `GOOGLE_OAUTH_REDIRECT_URI` | For the YouTube feature | Must exactly match an authorized redirect URI on the OAuth client. |
| `FRONTEND_URL` | Optional (default `http://localhost:3000`) | Where the OAuth callback redirects after completing. |
| `GOOGLE_OAUTH_SCOPES` | Optional | Defaults to `youtube.upload` only. |
| `COOKIE_SECURE` / `COOKIE_SAMESITE` | Optional | Defaults `false` / `lax`, correct for local http dev. See "Deployment" below for cross-origin production values. |

### Upload settings & metadata

- **Privacy**: Private / Unlisted / Public — defaults to **Private** in the
  UI; the backend requires it be supplied explicitly (no implicit default).
- **Audience**: the user must explicitly choose "made for kids" or not
  before the upload button enables; this maps to the documented
  `status.selfDeclaredMadeForKids` field.
- **Category**: defaults to category id `22` ("People & Blogs") — no
  category selector UI, since `videos.insert` requires *some* valid
  `categoryId` and building a full picker was judged out of scope for the
  hackathon target.
- Both title (100 chars) and description (5000 chars) are validated against
  the current YouTube Data API v3 limits, server-side, regardless of what
  the frontend already enforces.

### Quota and OAuth Testing-mode limitations

- The YouTube Data API has a finite daily quota; `videos.insert` is quota-
  expensive. Each user upload click produces exactly one insert request
  (idempotency guard described above) — do not add polling-triggered
  retries.
- While the Google OAuth consent screen is in **Testing** mode, *only*
  Google accounts added as **Test users** (step 3 above) can complete the
  connect flow — this is a Google-enforced restriction, not a ClipContext
  one. Moving to a verified/production OAuth app (required before
  arbitrary public users can connect) is a separate Google verification
  process; consult current Google OAuth verification requirements for the
  `youtube.upload` scope before a public launch.
- Refresh tokens are not permanent — Google can revoke them, and they can
  expire from disuse. When a stored token can no longer be refreshed, the
  upload fails with `YOUTUBE_RECONNECT_REQUIRED` and the stale credentials
  are discarded server-side; the UI prompts "Reconnect YouTube".

### API endpoints (YouTube)

- `GET /api/youtube/status` — `{ connected, channel_id, channel_title,
  channel_thumbnail_url }`. Never includes tokens.
- `GET /api/youtube/connect` — redirects to Google's consent screen.
- `GET /api/youtube/callback` — consumes the OAuth code, redirects to
  `${FRONTEND_URL}/results?youtube=connected` or `?youtube=error&code=...`.
- `POST /api/youtube/disconnect` — revokes (best-effort) and deletes the
  session's stored credentials.
- `POST /api/jobs/{job_id}/youtube/upload` — body `{ title, description,
  hashtags, privacy_status, made_for_kids }`; returns `{ upload_id, status
  }` immediately, uploads in a background thread.
- `GET /api/youtube/uploads/{upload_id}` — `{ status, progress, message,
  video_id, video_url, title, code, error }`; only visible to the session
  that created it.

### Local testing checklist

Always test the first real upload with `privacy_status: "private"`. The
frontend defaults to Private; do not manually switch to Public until
you've confirmed end-to-end behavior on a private video.

## ClipContext Accounts (optional Google sign-in + saved artifacts)

Users can optionally create a ClipContext account to save generated
results (titles, descriptions, hashtags, VideoContext, rankings) and
revisit them later. **This is entirely optional** — upload, processing,
results, and YouTube upload all work with zero ClipContext account.

### ClipContext login vs. YouTube OAuth — two different systems

This is the most important thing to understand about this feature:

| | **ClipContext account login** | **Connect with YouTube** |
|---|---|---|
| Purpose | Identifies *you* to save/retrieve artifacts | Authorizes ClipContext to upload videos to *a* channel |
| Technology | Firebase Authentication (Google provider) | Raw Google OAuth 2.0 web-server flow |
| Identity | Firebase UID | YouTube channel ID (via a `cc_session` cookie) |
| Where it's checked | `Authorization: Bearer <Firebase ID token>` header | `cc_session` HttpOnly cookie |
| Backend module | `src/firebase/`, `src/api/auth_dependencies.py` | `src/youtube/`, `src/api/youtube_routes.py` |

A user can be logged into ClipContext with Google account A and have
connected a YouTube channel authorized through Google account B — the two
are never assumed to be the same identity anywhere in this codebase.
Logging out of ClipContext does **not** disconnect YouTube, and
disconnecting YouTube does **not** log the user out of ClipContext.

### Architecture

```
Next.js frontend                             FastAPI backend
  │  Firebase Auth (Google provider,          (src/api/artifact_routes.py)
  │  signInWithPopup) — client-side,
  │  talks directly to Firebase, not
  │  through this backend
  │
  │  On save: getIdToken() ──────────────▶  Authorization: Bearer <token>
  │                                                │
  │                                         src/firebase/auth.py verifies
  │                                         the token via Firebase Admin SDK
  │                                                │
  │                                         verified Firebase UID
  │                                                │
  │                                         src/artifacts/repository.py
  │                                                │
  │  ◀── SavedArtifact ────────────────────  Cloud Firestore:
  │                                          users/{uid}/artifacts/{id}
```

- **The frontend never talks to Firestore directly.** All artifact reads/
  writes go through the FastAPI backend, which verifies the Firebase ID
  token and derives the UID server-side — the browser cannot forge another
  user's UID, and Firestore access is centralized in one place
  (`src/artifacts/repository.py`), not scattered through route handlers.
- **Canonical content, not browser-submitted content.** `POST
  /api/artifacts` takes a `job_id` and selected candidate ids; the backend
  re-reads the actual `PipelineResult` from the job registry and builds the
  artifact from that — the browser cannot fabricate arbitrary generated
  content by resending its own copy.
- **Idempotent by source job.** Saving the same job twice (double-click,
  re-render, retry) updates the existing artifact's selection instead of
  creating a duplicate — see `ArtifactRepository.upsert_by_source_job`.
- **What's persisted**: generated titles/descriptions/hashtags, rankings,
  VideoContext, the selected candidate ids, and — if that job's video was
  already uploaded to YouTube in the same browser session — safe upload
  metadata (video id/url, privacy status, channel id/title). **Never**
  persisted: YouTube access/refresh tokens, Firebase ID tokens, OAuth
  client secrets, or the original video file. Firestore is not video blob
  storage; only the generated artifact is saved. A saved artifact's detail
  page has no "Upload to YouTube" button, because the original video isn't
  retained server-side for historical artifacts.

### Firestore data model

```
users/{uid}
  display_name, email, photo_url, created_at, last_login_at

users/{uid}/artifacts/{artifact_id}
  source_job_id, created_at, updated_at
  video: { original_filename, display_name }
  video_context: { topic, content_type, multimodal_summary, core_message }
  generated_content: { titles[10], descriptions[10], hashtags[10] }
  rankings: { titles[10], descriptions[10], hashtags[10] }
  selection: { title_id, description_id, hashtag_set_id }
  youtube_upload: { uploaded, video_id, video_url, privacy_status,
                     channel_id, channel_title, uploaded_at }
```

### Firestore security rules

Because every artifact read/write goes through the authenticated FastAPI
backend (using the Firebase Admin SDK, which bypasses Firestore security
rules by design), the browser should never query Firestore directly. Set
Firestore to deny all direct client access — in Firebase Console under
**Firestore Database → Rules**:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if false;
    }
  }
}
```

If Firebase Console created your database in "test mode" (which defaults
to `allow read, write: if true` for 30 days), replace it with the rules
above — test mode is not safe to leave in place.

### Required Firebase setup

1. Open [Firebase Console](https://console.firebase.google.com/) and
   either add Firebase to the **same Google Cloud project** already used
   for `YOUTUBE_API_KEY`/YouTube OAuth (recommended — one project, one
   billing account, simpler to reason about), or create a new project.
2. **Build → Authentication** → **Get started** → **Sign-in method** tab →
   enable **Google** as a provider. Set a support email when prompted.
3. **Build → Firestore Database** → **Create database** → choose a
   location close to your users → start in whichever mode you like, then
   immediately apply the security rules above.
4. **Project settings** (gear icon) → **General** tab → scroll to **Your
   apps** → **Add app → Web** (`</>`). Register it (nickname doesn't
   matter, no hosting setup needed). Firebase shows a `firebaseConfig`
   object — copy each value into `frontend/.env.local`:
   ```
   NEXT_PUBLIC_FIREBASE_API_KEY=...
   NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=...
   NEXT_PUBLIC_FIREBASE_PROJECT_ID=...
   NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=...
   NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=...
   NEXT_PUBLIC_FIREBASE_APP_ID=...
   ```
5. **Project settings → Service accounts** tab → **Generate new private
   key** → downloads a JSON file. This is the Firebase Admin credential for
   the backend. **Do not commit it.** Save it somewhere outside the repo
   (or inside the repo root if you want, since `firebase-service-account*.json`
   / `*firebase-adminsdk*.json` / `serviceAccountKey.json` are already
   gitignored — but outside the repo is safer). Then set in the root
   `.env`:
   ```
   FIREBASE_PROJECT_ID=<the projectId from step 4>
   GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/that-file.json
   ```
6. **Authentication → Settings → Authorized domains** — `localhost` is
   authorized by default for local dev. Add your deployed frontend domain
   here before testing Google sign-in in production (see Deployment
   below).

### Environment variables

| Variable | File | Required | Notes |
|---|---|---|---|
| `NEXT_PUBLIC_FIREBASE_API_KEY` etc. (6 values) | `frontend/.env.local` | For the accounts feature | Not a server secret — ships in the deployed JS bundle by design. |
| `FIREBASE_PROJECT_ID` | root `.env` | For the accounts feature | Without it, `/api/artifacts/*` returns `FIREBASE_NOT_CONFIGURED` (503); everything else still works. |
| `GOOGLE_APPLICATION_CREDENTIALS` | root `.env` | One of these two | Path to the downloaded service-account JSON. |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | root `.env` | One of these two | The service-account JSON inline, for hosts without file-mount support. Use instead of, not alongside, `GOOGLE_APPLICATION_CREDENTIALS`. |

If neither Admin credential is set and the backend itself runs on Google
Cloud (Cloud Run, GCE, GKE) with an attached service account, Application
Default Credentials are used automatically.

### API endpoints (accounts)

- `POST /api/artifacts` — `{ job_id, selected_title_id,
  selected_description_id, selected_hashtag_set_id, video_display_name? }`.
  Requires `Authorization: Bearer <Firebase ID token>`. Validates the job
  is complete and the candidate ids are real, then saves (or updates, if
  this job was already saved) the artifact.
- `GET /api/artifacts` — `{ artifacts: [...] }`, newest first, summary
  fields only.
- `GET /api/artifacts/{artifact_id}` — full saved artifact. 404 if it
  doesn't exist or isn't yours (ownership is enforced by deriving the
  Firestore path from the verified UID, not from any client-supplied id).
- `DELETE /api/artifacts/{artifact_id}` — 204 on success, 404 if not found
  or not yours.

### Known limitations

- Job results (`PipelineResult`) live in the same in-memory job registry as
  the rest of the pipeline — see "Known limitations" below. Saving an
  artifact for a job whose tracking was lost to a backend restart returns
  `JOB_INCOMPLETE`; already-*saved* artifacts are unaffected (they're in
  Firestore, not the job registry).
- The original video file is never persisted as part of an artifact.
  Historical artifacts show generated content and, if applicable, past
  YouTube upload metadata — not a re-uploadable video.

## Testing

```bash
make test    # pytest tests/ — paths, job registry, API validation, schemas,
             # the YouTube OAuth/session/upload suite (test_youtube_*.py),
             # and the Firebase auth/artifact suite (test_auth_dependencies.py,
             # test_artifact_api.py, test_firebase_admin.py)
             # all external AI/YouTube/Firebase/Firestore calls are mocked;
             # no real network calls, uploads, or Firestore writes in tests
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

### Deploying the YouTube feature

If the frontend and backend are on different origins in production (e.g.
frontend on Vercel, backend on Railway/Fly/Cloud Run), the YouTube session
cookie needs cross-site cookie settings:

```
COOKIE_SECURE=true
COOKIE_SAMESITE=none
```

`SameSite=None` is rejected by browsers unless `Secure` is also set — the
backend enforces that pairing automatically, but set both explicitly in
your production environment regardless. You'll also need, in the backend's
production environment:

```
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_OAUTH_REDIRECT_URI=https://<your-backend-host>/api/youtube/callback
FRONTEND_URL=https://<your-frontend-host>
ALLOWED_ORIGINS=https://<your-frontend-host>
```

Add the production `GOOGLE_OAUTH_REDIRECT_URI` as a second "Authorized
redirect URI" on the same OAuth client in Google Cloud Console (keep the
localhost one too, for continued local development) — do not guess this
URL; it must exactly match your deployed backend's actual host and the
`/api/youtube/callback` path. Test the production OAuth connect flow and
perform the first production upload with `privacy_status: "private"`
before considering the feature launched.

### Deploying ClipContext accounts

1. In Firebase Console → **Authentication → Settings → Authorized
   domains**, add your deployed frontend's domain (e.g.
   `your-app.vercel.app`). Google sign-in fails with an
   `auth/unauthorized-domain` error from any origin not on this list —
   `localhost` is authorized by default but production domains are not
   added automatically.
2. Set the same `NEXT_PUBLIC_FIREBASE_*` values in the frontend host's
   environment-variable manager (Vercel/Netlify/etc.), not just locally.
3. On the backend host, set `FIREBASE_PROJECT_ID` and provide Admin
   credentials appropriate to that host:
   - If the backend runs on Cloud Run/GCE/GKE with an attached service
     account that has Firestore access, you can omit both credential
     variables entirely (Application Default Credentials).
   - Otherwise, set `FIREBASE_SERVICE_ACCOUNT_JSON` to the service-account
     JSON contents in your host's secret manager (do not write it to a
     file in the deployed image) — most non-GCP hosts (Railway, Fly,
     Render) only support environment variables, not mounted files, which
     is exactly why this variable exists as an alternative to
     `GOOGLE_APPLICATION_CREDENTIALS`.
4. Confirm Firestore security rules deny direct client access (see above)
   before going live — this matters more in production than locally.

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
- **YouTube connections and upload job tracking are in-memory only**,
  same tradeoff as job state above: a backend restart disconnects every
  session's YouTube account and forgets in-flight upload progress. Nothing
  crosses between sessions, and nothing is lost on disk — the user just
  sees "disconnected" and reconnects, or a completed YouTube video (which
  already exists on their channel) simply isn't re-discoverable via
  `GET /api/youtube/uploads/{id}` after a restart.
- **Google OAuth Testing-mode restriction.** Until the OAuth consent screen
  is moved out of Testing mode (a separate Google verification process for
  the `youtube.upload` scope), only Google accounts explicitly added as
  Test users in Google Cloud Console can complete the Connect YouTube flow.
- **Saving an artifact depends on the in-memory job registry still holding
  that job's result.** A backend restart between finishing a job and
  clicking "Save Results" returns `JOB_INCOMPLETE` for that specific job —
  already-*saved* artifacts are unaffected, since they live in Firestore,
  not the job registry.
- **The original uploaded video is never part of a saved artifact.** Only
  generated text/rankings/VideoContext are persisted; a saved artifact's
  detail page has no video preview or re-upload action.
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
- **`Save Results` fails with a 503 "Cloud save is not configured"`** —
  `FIREBASE_PROJECT_ID` isn't set in the backend `.env`. Everything else in
  ClipContext still works; see "ClipContext Accounts" above to configure it.
- **`auth/unauthorized-domain` on Google sign-in** — the current origin
  isn't in Firebase Console → Authentication → Settings → Authorized
  domains. `localhost` is included by default; production domains must be
  added manually.
- **`auth/popup-blocked` or the sign-in popup does nothing** — the browser
  blocked the popup opened by `signInWithPopup`. Allow popups for the site
  and retry.
