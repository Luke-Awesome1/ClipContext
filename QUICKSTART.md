# Quickstart

The fastest path from `git clone` to a running app. For full detail on any
step, see [docs/DeveloperGuide.md](docs/DeveloperGuide.md).

## 1. Prerequisites

- Python 3.13, Node.js 20+, FFmpeg on `PATH`.
- Three API keys: [Fireworks AI](https://fireworks.ai/), [YouTube Data API v3](https://console.cloud.google.com/apis/library/youtube.googleapis.com) (a Google Cloud API key), [Google Gemini](https://aistudio.google.com/apikey).

## 2. Clone and set up

```bash
git clone <your-fork-or-this-repo-url>
cd act2-captioner
make setup
```

## 3. Add your keys

Open `.env` (created by `make setup`) and set:

```
FIREWORKS_API_KEY=...
YOUTUBE_API_KEY=...
GEMINI_API_KEY=...
```

That's the entire minimum. Everything else — AMD GPU inference, YouTube
upload, ClipContext accounts — is optional and off by default.

## 4. Run it

```bash
# terminal 1
make backend

# terminal 2
make frontend
```

Open **http://localhost:3000**, upload a short video (30s–2min), and
watch it process.

## 5. What next

| I want to... | Go to |
|---|---|
| Understand what I'm looking at | [docs/Architecture.md](docs/Architecture.md) |
| Enable AMD GPU inference | [docs/AMD.md](docs/AMD.md) |
| Enable "Connect with YouTube" upload | [docs/YouTube.md](docs/YouTube.md) |
| Enable saved accounts | [docs/Firebase.md](docs/Firebase.md) |
| Deploy to production | [docs/Deployment.md](docs/Deployment.md) |
| Something's broken | [docs/Troubleshooting.md](docs/Troubleshooting.md) |
| Contribute a change | [CONTRIBUTING.md](CONTRIBUTING.md) |

Command reference: [docs/CHEATSHEET.md](docs/CHEATSHEET.md).
