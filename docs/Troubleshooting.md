# Troubleshooting

Grouped by area. If you're not sure which area, check the error message
against the section headers first — most ClipContext errors are specific
enough to search for directly.

## Backend startup

**`FIREWORKS_API_KEY is not set` (or `YOUTUBE_API_KEY` / `GEMINI_API_KEY`)**
— `src/config.py`'s `validate_environment()` refuses to start the backend
without all three. Copy `.env.example` to `.env` and fill them in (see
[Environment.md](Environment.md)), then restart.

**`ffprobe`/`ffmpeg: command not found`** — FFmpeg isn't on `PATH`.
`brew install ffmpeg` (macOS), `apt install ffmpeg` (Debian/Ubuntu),
`choco install ffmpeg` (Windows). Verify with `ffmpeg -version` and
`ffprobe -version` before restarting the backend. Inside Docker this is
already installed in the image — if you see this error from a container,
you're likely running the wrong image or a stale build.

**Port already in use (`Address already in use`, port 8000 or 3000)** —
another process is bound to it.
```bash
lsof -i :8000        # find what's using it
kill <pid>            # or: PORT=8001 .venv/bin/uvicorn src.api.app:app --port 8001
```
For the frontend, `next dev -p 3001` or set `PORT=3001` before `npm run dev`.

**Python version errors installing `requirements.txt`** — this project
targets Python 3.13. `python3.13 -m venv .venv` explicitly if your default
`python3`/`python` resolves to a different version
(`python3 --version` to check). Some scientific/ML dependencies
(`opencv-python`, `faster-whisper`) lag on 3.14 wheel availability —
stick to 3.13 or 3.12.

## Frontend build/dev

**Node version errors, or `npm ci` failing on lockfile mismatch** — use
Node 20+. `nvm install 20 && nvm use 20` if you have multiple Node
versions installed. `npm ci` (not `npm install`) is what CI and
`make setup` use — it installs exactly what `package-lock.json` specifies
and fails loudly on drift, which is what you want when debugging a
"works on my machine" issue.

**"Failed to reach the ClipContext backend" in the browser** —
`NEXT_PUBLIC_API_BASE_URL` in `frontend/.env.local` doesn't point at a
running backend, or the backend crashed. Confirm `curl http://localhost:8000/health`
returns `{"status":"ok"}` first.

**CORS errors in the browser console** — set `ALLOWED_ORIGINS` in the
backend `.env` to include the frontend's exact origin (including port),
then restart the backend. In production, this must be the deployed
frontend's real origin (e.g. `https://your-app.vercel.app`), not
`localhost`.

**A `NEXT_PUBLIC_*` env var change isn't taking effect** — these are baked
into the JavaScript bundle at `next build` time, not read at runtime.
Locally, restart `next dev`. In Vercel, trigger a redeploy — changing the
value in the dashboard alone does nothing until the next build. See
[Deployment.md](Deployment.md).

## Docker / docker-compose

**`docker build` fails on `apt-get install ffmpeg`** — usually a
transient package-mirror issue; retry. If it persists, check you're not
behind a proxy that blocks `apt-get update`.

**`docker compose up` frontend container can't reach the backend
container** — the frontend service in `docker-compose.yml` is set to call
the backend via `http://localhost:8000`, resolved **in the browser**, not
inside the Docker network — `NEXT_PUBLIC_*` values are baked into
JavaScript that runs client-side, so `http://backend:8000` (the in-network
service name) would only work for server-side Next.js code, not the
browser fetches this app actually makes. Leave it as `localhost:8000` and
make sure the backend's port is actually published (`ports: ["8000:8000"]`
in `docker-compose.yml` — already the default).

**Container exits immediately with no error** — run
`docker compose logs backend` (or `frontend`) to see the actual crash;
`docker compose up` without `-d` should already show this live.

**Bind-mounted `node_modules` conflicts / frontend container is slow to
start the first time** — `docker-compose.yml` uses a named volume for
`node_modules` specifically so the container's own `npm ci` install
doesn't get shadowed by your host's `node_modules` (which may be built for
a different OS/arch). The first `docker compose up` runs a real
`npm ci` inside the container — this is expected to take longer than
subsequent starts.

## AI pipeline / content generation

**`Kimi returned no JSON object`** — the vision model occasionally emits a
very long `visible_text` list (e.g. a frame full of on-screen text) that
overruns `MAX_OUTPUT_TOKENS` in `src/ai/fireworks/multimodal.py`,
truncating the response mid-object. Increase that constant if you hit this
consistently on real footage.

**Job fails at the transcription stage with a bare `Killed` in the logs,
no Python traceback** — this is the Linux OOM killer (SIGKILL), not an
application bug — almost always seen on a memory-constrained host (e.g.
Railway's 1GB plan). See [Deployment.md](Deployment.md) "The real memory
constraint" for the full explanation and mitigations
(`WHISPER_MODEL_SIZE`, or running locally instead).

**YouTube trend/quota HTTP errors** — the trend analyzers surface a
sanitized `RuntimeError` describing the HTTP status; check your
`YOUTUBE_API_KEY` quota in Google Cloud Console
(**APIs & Services → Quotas**).

**A stage configured for `amd_vllm` always shows `provider_used: "fireworks"`
in `ai_audit`** — this is the pipeline behaving correctly (truthful
fallback), not a bug. Check `GET /api/providers/status` first; if
`reachable: false` for `amd_vllm`, confirm the vLLM server is actually
running on the notebook (`amd/verify_rocm.py`, then `amd/smoke_test.py`
from a machine that can reach it) and that `AMD_VLLM_BASE_URL`/
`AMD_VLLM_MODEL` in the backend's `.env` match exactly. See
[AMD.md](AMD.md).

## Firebase / ClipContext accounts

**`Save Results` fails with a 503 "Cloud save is not configured"** —
`FIREBASE_PROJECT_ID` isn't set in the backend `.env`. Everything else in
ClipContext still works; see [Firebase.md](Firebase.md) to configure it.

**`auth/unauthorized-domain` on Google sign-in** — the current origin isn't
in **Firebase Console → Authentication → Settings → Authorized domains**.
`localhost` is included by default; production domains must be added
manually. See [Firebase.md](Firebase.md).

**`auth/popup-blocked`, or the sign-in popup does nothing** — the browser
blocked the popup opened by `signInWithPopup`. Allow popups for the site
and retry.

**Backend can't verify Firebase ID tokens / Admin SDK init fails** — check
exactly one of `GOOGLE_APPLICATION_CREDENTIALS` (file path) or
`FIREBASE_SERVICE_ACCOUNT_JSON` (inline JSON) is set, not both, and that
the file path (if used) actually exists and is readable by the process
(a relative path resolved from a different working directory than you
expect is the usual cause).

## YouTube OAuth / upload

**"access blocked" on the Google consent screen** — the OAuth consent
screen is in Testing mode and the Google account you're using isn't on the
**Test users** list (Google Cloud Console → APIs & Services → OAuth
consent screen). Add it, or move the app out of Testing mode (a separate
Google verification process). See [YouTube.md](YouTube.md).

**OAuth callback redirects but shows an error, or bounces back to the
homepage** — check `GOOGLE_OAUTH_REDIRECT_URI` in the backend `.env`
exactly matches an Authorized redirect URI registered on the OAuth client
(scheme, host, port, and path all have to match exactly — a trailing
slash mismatch is enough to fail this).

**Upload fails with `YOUTUBE_RECONNECT_REQUIRED`** — the stored refresh
token was revoked or expired from disuse. This is expected occasionally;
the UI prompts "Reconnect YouTube" — click it and redo the consent flow.

## Deployment (Vercel / Railway)

**Vercel build fails immediately, "no Next.js project found" or similar**
— **Settings → General → Root Directory** isn't set to `frontend`. This is
a monorepo; Vercel needs to be told the Next.js app isn't at the repo
root. See [Deployment.md](Deployment.md).

**Railway deploy succeeds but the app returns 502 "Application failed to
respond"** — check the target port in Railway's networking settings
matches what the container actually binds. The Dockerfile's `CMD` honors
`$PORT` if Railway injects one — if Railway's own `PORT` env var differs
from a port you manually set elsewhere, the app binds to Railway's value,
and the networking config needs to point at that same value, not a
guessed one. Check the actual `Uvicorn running on http://0.0.0.0:<port>`
line in the deploy logs to see what it really bound to.

**Railway container repeatedly restarts / crash-loops** — check
`restartPolicyMaxRetries` in `railway.toml` (currently 3) hasn't been
exhausted, and check the logs for the bare `Killed` OOM signature above
before assuming it's an application bug.

**Backend works locally but the deployed frontend can't reach it** — the
deployed `NEXT_PUBLIC_API_BASE_URL` doesn't point at the deployed backend
(remember: build-time baked, needs a redeploy after changing), or the
backend's `ALLOWED_ORIGINS` doesn't include the deployed frontend's
origin.

## Still stuck

Check [Environment.md](Environment.md) to confirm every variable your
feature needs is actually set in the right file, and
`GET /api/providers/status` / `GET /health` on the running backend for a
live signal before assuming code is broken. If none of the above matches,
open an issue with the exact error text and which area it's in — see
[CONTRIBUTING.md](../CONTRIBUTING.md).
