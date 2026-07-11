# API Reference

Base URL: wherever the FastAPI backend is running (`http://localhost:8000`
locally via `make backend`). All request/response bodies are JSON except
`POST /api/jobs`, which is `multipart/form-data`.

This is a literal reference to the routes defined in `src/api/routes.py`,
`src/api/artifact_routes.py`, and `src/api/youtube_routes.py`. See
[Backend.md](Backend.md) for the architecture behind these routes and
[AI-Pipeline.md](AI-Pipeline.md) for what `result` actually contains.

## Auth models used below

ClipContext has two independent, unrelated auth mechanisms — a request can
carry either, both, or neither:

- **Firebase ID token** — `Authorization: Bearer <firebase-id-token>`
  header, verified by `src/firebase/auth.py`. Required for every
  `/api/artifacts*` route. Enforced via the `get_current_user` FastAPI
  dependency (`src/api/auth_dependencies.py`), which raises `401` with a
  **plain string** `detail` (not the `{code, message}` shape used
  elsewhere) if the header is missing or the token is invalid/expired.
- **`cc_session` cookie** — an opaque, `HttpOnly`, server-generated session
  id (`src/youtube/session.py`) identifying "this browser" for the YouTube
  OAuth connection. Required for `/api/youtube/uploads/{id}` and
  `POST /api/jobs/{id}/youtube/upload`; optional (falls back to
  "disconnected") for `GET /api/youtube/status` and
  `POST /api/youtube/disconnect`.
- **None** — `/health`, `/api/providers/status`, `POST /api/jobs`,
  `GET /api/jobs/{id}`, and the OAuth entry/callback routes are open.

## Error body shapes

Two different conventions exist in this codebase, verified against the
actual `HTTPException` calls in each router:

1. **Plain string `detail`** — used by `src/api/routes.py` (job creation
   and lookup) and by Firebase auth failures in
   `src/api/auth_dependencies.py`. Example: `{"detail": "Job not found."}`.
2. **Structured `{code, message}` `detail`** — used by every route in
   `src/api/artifact_routes.py` and `src/api/youtube_routes.py`. Example:
   `{"detail": {"code": "JOB_NOT_FOUND", "message": "This ClipContext job could not be found."}}`.

Both are surfaced by FastAPI as a JSON body `{"detail": ...}` with the
given HTTP status code.

---

## Core job API (`src/api/routes.py`)

### `GET /health`

**Purpose**: Liveness check (used by Railway's `healthcheckPath`).
**Auth**: None.
**Request**: none.
**Response** `200 HealthResponse`:
```json
{ "status": "ok" }
```
**Errors**: none.

---

### `GET /api/providers/status`

**Purpose**: Reports which AI provider (`fireworks` / `amd_vllm`) is
configured for the `content_generation` and `discriminator` stages, and
whether each is currently reachable. Never exposes API keys or the AMD
endpoint URL. Checking AMD vLLM reachability makes a live network call to
`AMD_VLLM_BASE_URL`, which is why this is a separate endpoint from
`/health` rather than folded into the liveness check.
**Auth**: None.
**Request**: none.
**Response** `200 ProviderStatusResponse`:
```json
{
  "stages": {
    "content_generation": { "provider_requested": "fireworks", "fallback_provider": null },
    "discriminator": { "provider_requested": "fireworks", "fallback_provider": null }
  },
  "providers": {
    "fireworks": { "configured": true, "reachable": null }
  }
}
```
(If `CONTENT_GENERATION_PROVIDER=amd_vllm`, an `amd_vllm` entry appears in
`providers` with `configured`, `reachable`, `model`, and optionally
`model_loaded` / `error_category`.)
**Errors**: none documented; provider health checks never raise
(`health_check()` catches all exceptions internally).

---

### `POST /api/jobs`

**Purpose**: Upload a video and start the pipeline as a background thread.
Returns immediately — does not wait for processing to finish.
**Auth**: None.
**Request**: `multipart/form-data`:

| Field | Type | Required | Notes |
|---|---|---|---|
| `video` | file | yes | Must have extension `.mp4`, `.mov`, or `.webm` (`ALLOWED_VIDEO_EXTENSIONS`). |
| `creator_handle` | string (form field) | no, default `""` | Normalized (lowercased, `@` stripped) via `normalize_creator_handle()`. Omit to skip creator trend analysis. |
| `platform` | string (form field) | no, default `"youtube"` | Must be `"youtube"` or `"web"` (`SUPPORTED_PLATFORMS`). |

`job_id` is deterministic: `sha256(video_hash:platform:creator_handle)[:16]`
(`compute_job_id`), so re-uploading the identical video with the same
platform/handle returns the same job id and reuses any prior work still on
disk. `MAX_UPLOAD_SIZE_MB` (default 200MB) caps upload size, enforced while
streaming to disk in 1MB chunks.

**Response** `200 JobCreateResponse`:
```json
{ "job_id": "3f9c2a1b7e4d5601", "status": "queued" }
```
**Errors**:
- `400` — unsupported `platform` (plain string detail).
- `400` — unsupported video extension (plain string detail).
- `413` — upload exceeds `MAX_UPLOAD_SIZE_MB` (plain string detail).
- `400` — empty upload, "No video file was received." (plain string detail).
- `500` — failed to store the upload, or failed to start the job thread (plain string detail).

**curl**:
```bash
curl -X POST http://localhost:8000/api/jobs \
  -F "video=@my-clip.mp4" \
  -F "creator_handle=somecreator" \
  -F "platform=youtube"
```

---

### `GET /api/jobs/{job_id}`

**Purpose**: Poll job status and progress. This is also the **only** way to
retrieve final results — there is no separate results endpoint; once
`status == "completed"`, `result` is populated in this same response.
**Auth**: None.
**Request**: path param `job_id: str`.
**Response** `200 JobStatusResponse`:
```json
{
  "job_id": "3f9c2a1b7e4d5601",
  "status": "processing",
  "stage": "visual_analysis",
  "progress": 55,
  "message": "Analysing visual window 4/9",
  "result": null,
  "error": null
}
```
On completion, `status` becomes `"completed"`, `stage` becomes
`"completed"`, `progress` is `100`, and `result` holds the full
`PipelineResult` (see [AI-Pipeline.md](AI-Pipeline.md) for its shape). On
failure, `status` is `"failed"` and `error` holds a user-safe message.
**Errors**:
- `404` — no job with this id in the in-memory registry (never existed, or
  the backend restarted since it was created) (plain string detail: `"Job not found."`).

**curl**:
```bash
curl http://localhost:8000/api/jobs/3f9c2a1b7e4d5601
```

---

## Artifact API (`src/api/artifact_routes.py`)

Requires a Firebase ID token on every route (`get_current_user`), plus
Firebase must be configured server-side or every route returns
`503 FIREBASE_NOT_CONFIGURED` before doing anything else:
```json
{ "detail": { "code": "FIREBASE_NOT_CONFIGURED", "message": "Cloud save is not configured on this server yet." } }
```

### `POST /api/artifacts`

**Purpose**: Save a completed job's results plus the user's title/
description/hashtag selection to Firestore, keyed by the caller's Firebase
uid. Upserts by `source_job_id` — saving the same job twice updates the
existing artifact rather than creating a duplicate.
**Auth**: Firebase ID token.
**Request body** `ArtifactCreateRequest`:
```json
{
  "job_id": "3f9c2a1b7e4d5601",
  "selected_title_id": 3,
  "selected_description_id": 1,
  "selected_hashtag_set_id": 7,
  "video_display_name": "my-video.mp4"
}
```
(`video_display_name` is optional and cosmetic only.)
**Response** `200 SavedArtifact` — see the shape under
`GET /api/artifacts/{artifact_id}` below.
**Errors**:
- `503 FIREBASE_NOT_CONFIGURED`.
- `404 {"code": "JOB_NOT_FOUND"}` — job id unknown to the in-memory registry.
- `409 {"code": "JOB_INCOMPLETE"}` — job isn't `completed` yet, or its
  result is gone (e.g. the backend restarted after it finished).
- `422 {"code": "INVALID_SELECTION"}` — a selected id isn't present in that
  job's `generated_content` (one error per pool: title/description/hashtag).
- `502 {"code": "ARTIFACT_SAVE_FAILED"}` — Firestore write failed.

---

### `GET /api/artifacts`

**Purpose**: List the signed-in user's saved artifacts, newest first.
**Auth**: Firebase ID token.
**Request**: none.
**Response** `200 ArtifactListResponse`:
```json
{
  "artifacts": [
    {
      "artifact_id": "8b1e...",
      "created_at": "2026-07-10T18:22:00Z",
      "topic": "Home espresso setup on a budget",
      "content_type": "tutorial",
      "selected_title": "I Spent $80 On My First Espresso Setup",
      "youtube_uploaded": true
    }
  ]
}
```
**Errors**:
- `503 FIREBASE_NOT_CONFIGURED`.
- `502 {"code": "ARTIFACT_LIST_FAILED"}`.

---

### `GET /api/artifacts/{artifact_id}`

**Purpose**: Fetch one saved artifact in full.
**Auth**: Firebase ID token (scoped to the caller's own uid — cannot read another user's artifact id).
**Response** `200 SavedArtifact`:
```json
{
  "artifact_id": "8b1e...",
  "source_job_id": "3f9c2a1b7e4d5601",
  "created_at": "2026-07-10T18:22:00Z",
  "updated_at": "2026-07-10T18:22:00Z",
  "video": { "original_filename": null, "display_name": "my-video.mp4" },
  "video_context": {
    "topic": "Home espresso setup on a budget",
    "content_type": "tutorial",
    "multimodal_summary": "...",
    "core_message": "..."
  },
  "generated_content": { "titles": [...], "descriptions": [...], "hashtags": [...] },
  "rankings": { "titles": [...], "descriptions": [...], "hashtags": [...] },
  "selection": { "title_id": 3, "description_id": 1, "hashtag_set_id": 7 },
  "youtube_upload": { "uploaded": false }
}
```
**Errors**:
- `503 FIREBASE_NOT_CONFIGURED`.
- `502 {"code": "ARTIFACT_LOAD_FAILED"}`.
- `404 {"code": "ARTIFACT_NOT_FOUND"}`.

---

### `DELETE /api/artifacts/{artifact_id}`

**Purpose**: Delete a saved artifact.
**Auth**: Firebase ID token.
**Response**: `204 No Content` (empty body).
**Errors**:
- `503 FIREBASE_NOT_CONFIGURED`.
- `502 {"code": "ARTIFACT_DELETE_FAILED"}`.
- `404 {"code": "ARTIFACT_NOT_FOUND"}`.

---

## YouTube API (`src/api/youtube_routes.py`)

"Connect with YouTube" — a session-cookie-based flow, unrelated to the
Firebase artifact routes above.

### `GET /api/youtube/status`

**Purpose**: Whether this browser session currently has a connected
YouTube channel.
**Auth**: `cc_session` cookie, optional (no cookie → `connected: false`).
**Response** `200 YouTubeConnectionStatus`:
```json
{ "connected": true, "channel_id": "UC...", "channel_title": "My Channel", "channel_thumbnail_url": "https://..." }
```
**Errors**: none.

---

### `GET /api/youtube/connect`

**Purpose**: Start the OAuth flow — redirects to Google's consent screen.
Creates a `cc_session` cookie if the browser doesn't already have one.
**Auth**: None (session cookie is created here if missing).
**Response**: `302 Redirect` to Google's authorization URL.
**Errors**:
- `503 {"code": "YOUTUBE_OAUTH_NOT_CONFIGURED"}` — `GOOGLE_CLIENT_ID` /
  `GOOGLE_CLIENT_SECRET` / `GOOGLE_OAUTH_REDIRECT_URI` not all set.

---

### `GET /api/youtube/callback`

**Purpose**: Google's OAuth redirect target — exchanges the authorization
code, fetches channel info, stores credentials. Called by Google, not
directly by the frontend.
**Auth**: `cc_session` cookie must already exist (set during `/connect`).
**Response**: Always `302 Redirect` to `{FRONTEND_URL}/results`, either
`?youtube=connected` on success or `?youtube=error&code=<CODE>` on failure
— this route never raises an `HTTPException` itself. Possible `code`
values: `OAUTH_DENIED`, `OAUTH_STATE_INVALID`, `OAUTH_EXCHANGE_FAILED`,
`YOUTUBE_NO_CHANNEL`, `YOUTUBE_UPLOAD_FAILED`.

---

### `POST /api/youtube/disconnect`

**Purpose**: Revoke and forget this session's YouTube credentials.
**Auth**: `cc_session` cookie, optional.
**Response** `200 YouTubeConnectionStatus`:
```json
{ "connected": false }
```
**Errors**: none.

---

### `POST /api/jobs/{job_id}/youtube/upload`

**Purpose**: Upload a completed job's source video to the connected
YouTube channel. Runs on a background thread; returns immediately with an
`upload_id` to poll.
**Auth**: `cc_session` cookie bound to a connected YouTube account.
**Request body** `YouTubeUploadRequest`:
```json
{
  "title": "I Spent $80 On My First Espresso Setup",
  "description": "Full breakdown of the gear...",
  "hashtags": ["#espresso", "#coffee"],
  "privacy_status": "private",
  "made_for_kids": false
}
```
`title` max 100 chars, `description` max 5000 chars
(`MAX_TITLE_LENGTH` / `MAX_DESCRIPTION_LENGTH`); `privacy_status` must be
one of `private` / `unlisted` / `public`; both validated by pydantic
(invalid values produce FastAPI's standard `422` body, not a `{code,
message}` one).
**Response** `200 YouTubeUploadCreated`:
```json
{ "upload_id": "6a2f...", "status": "queued" }
```
**Errors**:
- `401 {"code": "YOUTUBE_NOT_CONNECTED"}` — no session cookie, or no stored
  credentials for it.
- `404 {"code": "JOB_NOT_FOUND"}`.
- `409 {"code": "JOB_INCOMPLETE"}` — job hasn't finished processing.
- `404 {"code": "VIDEO_SOURCE_MISSING"}` — original uploaded video file no
  longer on disk.
- `409 {"code": "YOUTUBE_UPLOAD_IN_PROGRESS"}` — an upload for this
  session+job is already active.

---

### `GET /api/youtube/uploads/{upload_id}`

**Purpose**: Poll YouTube upload progress.
**Auth**: `cc_session` cookie must match the session that created the upload.
**Response** `200 YouTubeUploadStatus`:
```json
{
  "upload_id": "6a2f...",
  "status": "uploading",
  "progress": 42,
  "message": "Uploading video to YouTube",
  "video_id": null,
  "video_url": null,
  "title": null,
  "code": null,
  "error": null
}
```
On completion, `status` is `"completed"` and `video_id` / `video_url` /
`title` are populated. On failure, `status` is `"failed"` with `code` (a
`YouTubeErrorCode`, e.g. `YOUTUBE_QUOTA_EXCEEDED`, `YOUTUBE_API_DISABLED`,
`YOUTUBE_INSUFFICIENT_SCOPE`) and a human-readable `error`.
**Errors**:
- `404 {"code": "UPLOAD_NOT_FOUND"}` — returned uniformly whether the
  upload id doesn't exist, there's no session cookie, or the cookie
  belongs to a different session than the one that created the upload
  (avoids leaking whether an upload id exists to the wrong caller).

---

## See also

- [Backend.md](Backend.md) — architecture behind these routes, the
  in-memory job registry, and why deployment is capped at one replica.
- [AI-Pipeline.md](AI-Pipeline.md) — the full shape of `PipelineResult`
  (the `result` field on `JobStatusResponse`).
