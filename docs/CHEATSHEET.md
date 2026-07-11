# Cheat Sheet

Quick reference — commands, URLs, and env vars, no explanation. See linked
docs for the "why."

## Commands

```bash
# Setup
make setup                    # venv + pip install + npm ci + copy .env templates

# Run locally
make backend                  # uvicorn --reload, :8000
make frontend                 # next dev, :3000
docker compose up --build     # both, containerized, hot-reload

# CLI (bypasses the API, same pipeline)
.venv/bin/python main.py path/to/video.mp4 --creator @handle --platform youtube

# Test / lint
make test                     # pytest tests/ — all external calls mocked
ruff check src main.py        # backend lint (unused imports, undefined names)
cd frontend && npm run lint   # frontend eslint
cd frontend && npx tsc --noEmit   # frontend typecheck
cd frontend && npm run build  # also runs lint + typecheck

# Docker (backend only, production-style)
docker build -t clipcontext-backend .
docker run -p 8000:8000 --env-file .env clipcontext-backend
```

## Local URLs

| URL | What |
|---|---|
| `http://localhost:3000` | Frontend |
| `http://localhost:8000` | Backend |
| `http://localhost:8000/health` | Liveness check |
| `http://localhost:8000/api/providers/status` | AI provider reachability (Fireworks/AMD) |
| `http://localhost:8000/docs` | FastAPI auto-generated Swagger UI |

## Minimum env vars to run locally

```
# root .env
FIREWORKS_API_KEY=
YOUTUBE_API_KEY=
GEMINI_API_KEY=

# frontend/.env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Full reference: [Environment.md](Environment.md).

## Switch content generation to AMD

```
# root .env — after starting the vLLM server, see AMD.md
CONTENT_GENERATION_PROVIDER=amd_vllm
CONTENT_GENERATION_FALLBACK_PROVIDER=fireworks
AMD_VLLM_BASE_URL=https://<tunnel-url>/v1
AMD_VLLM_MODEL=Qwen/Qwen2.5-7B-Instruct
AMD_VLLM_API_KEY=<matches --api-key on the vLLM server>
```

Verify: `curl http://localhost:8000/api/providers/status`. Full detail:
[AMD.md](AMD.md).

## Production deploy commands

```bash
# AMD notebook (see AMD.md for the full sequence)
bash amd/start_vllm.sh                                  # tmux session "vllm"
./cloudflared tunnel --url http://localhost:8000         # tmux session "tunnel"
python amd/verify_rocm.py
python amd/smoke_test.py

# Check AMD reachability on the deployed backend
curl https://<your-backend>/api/providers/status
```

## Key env vars by feature

| Feature | Required vars |
|---|---|
| Core pipeline | `FIREWORKS_API_KEY`, `YOUTUBE_API_KEY`, `GEMINI_API_KEY` |
| AMD content generation | `AMD_VLLM_BASE_URL`, `AMD_VLLM_MODEL`, `CONTENT_GENERATION_PROVIDER=amd_vllm` |
| YouTube connect/upload | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_OAUTH_REDIRECT_URI` |
| ClipContext accounts | `FIREBASE_PROJECT_ID`, `GOOGLE_APPLICATION_CREDENTIALS` (or `FIREBASE_SERVICE_ACCOUNT_JSON`), `NEXT_PUBLIC_FIREBASE_*` (6 vars) |
| Cross-origin production (Vercel+Railway) | `COOKIE_SECURE=true`, `COOKIE_SAMESITE=none`, `ALLOWED_ORIGINS` |

Full reference: [Environment.md](Environment.md).

## Common fixes

| Symptom | Fix |
|---|---|
| `ffmpeg: command not found` | `brew install ffmpeg` / `apt install ffmpeg` |
| Bare `Killed` in backend logs | OOM killer — see [Deployment.md](Deployment.md) |
| CORS error in browser console | Set `ALLOWED_ORIGINS` in backend `.env`, restart |
| `NEXT_PUBLIC_*` change not showing up | Redeploy — it's baked in at build time |
| `auth/unauthorized-domain` | Add domain in Firebase Console → Authorized domains |
| YouTube "access blocked" | Add your Google account as a Test user on the OAuth consent screen |
| AMD badge missing, `provider_used: fireworks` | Truthful fallback — check `/api/providers/status` |

Full troubleshooting guide: [Troubleshooting.md](Troubleshooting.md).
