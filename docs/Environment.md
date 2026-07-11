# Environment Variables

ClipContext reads configuration from two places: a root `.env` file for the
FastAPI backend (see [`.env.example`](../.env.example)) and
`frontend/.env.local` for the Next.js frontend (see
[`frontend/.env.local.example`](../frontend/.env.local.example)). This
document describes every variable in both files. For how these get set on
each hosting platform, see [Deployment.md](Deployment.md); for the
AMD-specific variables in more depth, see [AMD.md](AMD.md).

## Minimum viable local setup

The backend's `src/config.py` (`validate_environment()`, called at FastAPI
startup) only hard-requires three variables — if any are missing, the
process raises `RuntimeError` and refuses to start:

```
FIREWORKS_API_KEY=
YOUTUBE_API_KEY=
GEMINI_API_KEY=
```

Everything else in `.env.example` — AI provider routing, AMD vLLM, upload
limits, YouTube OAuth, Firebase — is optional and has a working default (or
a feature that cleanly disables itself with a structured error response
when unset, rather than crashing the app).

On the frontend side, `NEXT_PUBLIC_API_BASE_URL` isn't checked by any
backend startup code, but the frontend has no way to reach the backend
without it, so in practice it's required for the app to do anything useful
locally.

So the smallest set of environment variables to run ClipContext locally
with zero optional features is:

| Variable | File |
|---|---|
| `FIREWORKS_API_KEY` | root `.env` |
| `YOUTUBE_API_KEY` | root `.env` |
| `GEMINI_API_KEY` | root `.env` |
| `NEXT_PUBLIC_API_BASE_URL` | `frontend/.env.local` |

With just these four set, ClipContext runs the full core workflow (upload,
process, results) with local Whisper transcription, Fireworks
content-generation/discriminator/vision, and Gemini vision fallback. AMD
vLLM, YouTube OAuth upload, and ClipContext account login all stay off
until their own variables are set — none of them are required for the app
to function.

`make setup` bootstraps both files for you (`cp .env.example .env` and
`cp frontend/.env.local.example frontend/.env.local`) if they don't already
exist.

---

## Backend — required (root `.env`)

Backend process fails to start if any of these are unset.

| Variable | Required | Purpose | Example |
|---|---|---|---|
| `FIREWORKS_API_KEY` | Yes | Fireworks API key. Used for Kimi vision (visual timeline analysis) and, by default, the `content_generation`/`discriminator` text stages. | `fw_3ZaBcDeFgHiJkLmNoPqRsT` |
| `YOUTUBE_API_KEY` | Yes | YouTube Data API key (separate from OAuth below — this is for read-only trend analysis, not upload). Create in Google Cloud Console. | `AIzaSyD-ExampleYouTubeDataApiKey123` |
| `GEMINI_API_KEY` | Yes | Google Gemini API key, used as a vision fallback path (`src/ai/vision/gemma.py`). | `AIzaSyC-ExampleGeminiApiKey456` |

## AI provider selection — content generation / discriminator stages (root `.env`)

Optional. Both stages default to `"fireworks"` with no fallback if unset —
leaving these unset reproduces the app's original, pre-AMD behavior
exactly. See [AMD.md](AMD.md) for the full routing/orchestrator explanation.

| Variable | Required | Purpose | Example |
|---|---|---|---|
| `CONTENT_GENERATION_PROVIDER` | Optional | Provider for the 10 titles/10 descriptions/10 hashtag-set stage: `fireworks` (default) or `amd_vllm`. | `amd_vllm` |
| `CONTENT_GENERATION_FALLBACK_PROVIDER` | Optional | Provider to fall back to if the primary above fails or is unreachable. Only meaningful if the primary is set to something other than `fireworks`. | `fireworks` |
| `DISCRIMINATOR_PROVIDER` | Optional | Provider for the independent ranking stage: `fireworks` (default) or `amd_vllm`. | `fireworks` |
| `DISCRIMINATOR_FALLBACK_PROVIDER` | Optional | Fallback provider for the discriminator stage. | `fireworks` |

## AMD GPU inference — ROCm + vLLM (root `.env`)

Optional. Leave unset to run ClipContext with zero AMD configuration —
every stage just uses Fireworks. **Required only if**
`CONTENT_GENERATION_PROVIDER` or `DISCRIMINATOR_PROVIDER` above is set to
`amd_vllm`. This backend process is the only thing that ever talks to this
endpoint — never the browser. See [AMD.md](AMD.md) and
[`amd/README.md`](../amd/README.md) for how to start the vLLM server on the
AMD hackathon notebook.

| Variable | Required | Purpose | Example |
|---|---|---|---|
| `AMD_VLLM_BASE_URL` | Only if a stage above is `amd_vllm` | Base URL of the OpenAI-compatible vLLM server — a notebook host or (in practice) a Cloudflare Tunnel URL. Never a browser-facing origin. | `https://random-two-words.trycloudflare.com/v1` |
| `AMD_VLLM_MODEL` | Only if a stage above is `amd_vllm` | Model id the vLLM server was started with (must match `--served-model-name` exactly). | `Qwen/Qwen2.5-7B-Instruct` |
| `AMD_VLLM_API_KEY` | Only if the vLLM server was started with `--api-key` | Bearer key the AMD server enforces. Recommended whenever the endpoint is reachable beyond localhost. | `a1b2c3d4-example-random-key` |
| `AMD_VLLM_TIMEOUT_SECONDS` | Optional (default `240`) | Request timeout in seconds for AMD vLLM calls. Raise if the notebook GPU is slow to warm up, or if `DISCRIMINATOR_PROVIDER=amd_vllm` is also enabled (its `max_tokens` ceiling is higher). | `300` |

## Backend — optional / tuning (root `.env`)

Sane defaults are applied if unset; nothing here blocks startup.

| Variable | Required | Purpose | Example |
|---|---|---|---|
| `ALLOWED_ORIGINS` | Optional | Comma-separated list of origins allowed to call the API (CORS). Defaults to a set of localhost ports (3000-3003). Set to the deployed frontend's origin in production. | `https://your-app.vercel.app` |
| `MAX_UPLOAD_SIZE_MB` | Optional | Maximum accepted video upload size, in megabytes. Defaults to `200`. | `200` |
| `PORT` | Optional | Port the FastAPI server binds to. Defaults to `8000`; hosts like Railway/Cloud Run inject this automatically. | `8000` |
| `WHISPER_MODEL_SIZE` | Optional | faster-whisper model size for local transcription (`src/ai/transcriber.py`). The code's actual default is `"tiny"` (the smallest available model) — chosen because `"small"` was observed to OOM-kill a memory-constrained deployment and even `"base"` reduced but did not eliminate intermittent OOM kills. Raise to `base`/`small`/`medium` only on a host with real memory headroom. See [Deployment.md](Deployment.md) for the full Railway memory discussion. | `base` |

> Note: `.env.example`'s inline comment for `WHISPER_MODEL_SIZE` says the
> default is `"base"`, but the actual default in `src/ai/transcriber.py`
> (`DEFAULT_WHISPER_MODEL_SIZE`) is `"tiny"`. The code is the source of
> truth for what actually loads when this variable is unset.

## YouTube OAuth — "Connect with YouTube" / "Upload to YouTube" (root `.env`)

Optional as a group. Leave all of these unset to run ClipContext without
the YouTube upload feature — every other part of the app works fine.
`GET /api/youtube/connect` returns a structured 503
(`YOUTUBE_OAUTH_NOT_CONFIGURED`) until `GOOGLE_CLIENT_ID`,
`GOOGLE_CLIENT_SECRET`, and `GOOGLE_OAUTH_REDIRECT_URI` are all set. Create
the client credentials in Google Cloud Console → APIs & Services →
Credentials (OAuth client ID, type "Web application"); see the root
`README.md` for the full walkthrough.

| Variable | Required | Purpose | Example |
|---|---|---|---|
| `GOOGLE_CLIENT_ID` | Only for YouTube upload feature | OAuth client id from Google Cloud Console. | `1234567890-exampleclientid.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | Only for YouTube upload feature | OAuth client secret. | `GOCSPX-ExampleClientSecret` |
| `GOOGLE_OAUTH_REDIRECT_URI` | Only for YouTube upload feature | Must exactly match an "Authorized redirect URI" on the OAuth client, and must point at this backend's own `/api/youtube/callback` route. Local dev default shown. | `http://localhost:8000/api/youtube/callback` |
| `FRONTEND_URL` | Optional (default `http://localhost:3000`) | Where the backend redirects the browser after the OAuth callback completes (`/results?youtube=connected` or `?youtube=error&code=...`). | `https://your-app.vercel.app` |
| `GOOGLE_OAUTH_SCOPES` | Optional | Space- or comma-separated OAuth scopes. Defaults to `youtube.upload` plus `youtube.readonly` — the upload scope alone is rejected by `channels.list(mine=true)`, which the app needs to show the connected channel's name. | `https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly` |
| `COOKIE_SECURE` | Optional (default `false`) | Session cookie `Secure` flag. Set `true` in production if frontend/backend are on different origins. | `true` |
| `COOKIE_SAMESITE` | Optional (default `lax`) | Session cookie `SameSite` policy. Set `none` in production if frontend/backend are on different origins (requires `COOKIE_SECURE=true` too — browsers reject `SameSite=None` without `Secure`). | `none` |

## Firebase — ClipContext accounts (root `.env`)

Optional as a group, and intentionally separate from
`GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET` above, which authorize YouTube
uploads, not a ClipContext account login (see root `README.md` for why
these are two different systems). Leave unset to run ClipContext without
accounts — upload, process, results, and YouTube upload all keep working.
Account endpoints (`POST`/`GET`/`DELETE /api/artifacts`) return a
structured 503 (`FIREBASE_NOT_CONFIGURED`) until `FIREBASE_PROJECT_ID` is
set.

| Variable | Required | Purpose | Example |
|---|---|---|---|
| `FIREBASE_PROJECT_ID` | Only for ClipContext accounts | Firebase project id. | `clipcontext-example` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Only one of this or `FIREBASE_SERVICE_ACCOUNT_JSON`, never both | Path to a service-account JSON file (gitignored, never commit it). Only useful on hosts that support mounted files. | `/etc/secrets/firebase-adminsdk.json` |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | Only one of this or `GOOGLE_APPLICATION_CREDENTIALS`, never both | The service-account JSON contents inline, for hosts that only support environment variables (no file mounts — e.g. Railway/Render). | `{"type": "service_account", "project_id": "clipcontext-example", ...}` |

If both credential variables are unset and the backend itself runs on
Google Cloud (Cloud Run, GCE, GKE) with an attached service account,
Application Default Credentials are used automatically — no explicit
credential needed there.

---

## Frontend — required (`frontend/.env.local`)

| Variable | Required | Purpose | Example |
|---|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Yes | Base URL of the FastAPI backend the frontend calls. | `http://localhost:8000` (local) / `https://your-backend.up.railway.app` (production) |

Remember: `NEXT_PUBLIC_*` variables are baked into the JavaScript bundle at
`next build` time, not read live at runtime. Changing this in a hosting
provider's dashboard requires a redeploy to take effect — see
[Deployment.md](Deployment.md).

## Frontend — Firebase web config (`frontend/.env.local`)

Optional as a group. Not a server secret — Firebase web config ships in the
deployed JS bundle by design; Firebase's access control lives in
Authentication + Firestore security rules, not in hiding this config. Still
environment-specific, so it belongs in `frontend/.env.local` (or the
hosting provider's env var manager), not hardcoded. Leave unset to run
ClipContext without accounts.

| Variable | Required | Purpose | Example |
|---|---|---|---|
| `NEXT_PUBLIC_FIREBASE_API_KEY` | Only for ClipContext account login | Firebase web API key. | `AIzaSyExampleFirebaseWebKey789` |
| `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN` | Only for ClipContext account login | Firebase Auth domain. | `clipcontext-example.firebaseapp.com` |
| `NEXT_PUBLIC_FIREBASE_PROJECT_ID` | Only for ClipContext account login | Firebase project id (same value as backend's `FIREBASE_PROJECT_ID`). | `clipcontext-example` |
| `NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET` | Only for ClipContext account login | Firebase Storage bucket. | `clipcontext-example.appspot.com` |
| `NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID` | Only for ClipContext account login | Firebase Cloud Messaging sender id. | `123456789012` |
| `NEXT_PUBLIC_FIREBASE_APP_ID` | Only for ClipContext account login | Firebase web app id. | `1:123456789012:web:exampleappid1234` |

## Related documentation

- [Deployment.md](Deployment.md) — where each of these variables gets set
  on each hosting platform, and the Vercel build-time gotcha in full.
- [AMD.md](AMD.md) — AMD GPU integration deep-dive, including the
  Cloudflare Tunnel networking that determines `AMD_VLLM_BASE_URL` in
  practice.
