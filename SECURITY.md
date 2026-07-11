# Security Policy

## Reporting a vulnerability

If you find a security issue in ClipContext — an auth bypass, a way to
access another user's data, a credential leak, an injection vector, or
similar — please **do not** open a public GitHub issue.

Instead, use GitHub's private vulnerability reporting for this repository
(**Security** tab → **Report a vulnerability**), or email the maintainer
directly if that isn't available. Include:

- What you found and where (file/endpoint if known).
- Steps to reproduce.
- What you think the impact is.

Expect an acknowledgement within a few days. This is a hackathon-origin
project maintained on a best-effort basis — there's no formal SLA, but
security reports get priority over feature work.

## Scope

In scope: the FastAPI backend (`src/`), the Next.js frontend (`frontend/`),
and how they integrate with Firebase, YouTube OAuth, Fireworks, and the AMD
vLLM inference path.

Out of scope: vulnerabilities in third-party services themselves (Firebase,
Google OAuth, Fireworks, YouTube Data API) — report those to the relevant
vendor.

## Known, accepted limitations

These are documented tradeoffs, not vulnerabilities — see
[docs/Backend.md](docs/Backend.md) and [README.md](README.md) "Known
limitations" for the full list. The short version: job state and YouTube
session/token storage are in-memory (single-instance only, by design, not
an oversight), and this is a hackathon-scope project without a security
audit — treat a public deployment accordingly (see
[docs/Deployment.md](docs/Deployment.md) for hardening notes).

## Handling secrets

Never commit `.env`, `frontend/.env.local`, or any Firebase service-account
JSON file. See [docs/Environment.md](docs/Environment.md) for what every
credential does and where it belongs. If you accidentally commit a secret,
rotate it immediately at the provider (Fireworks, Google Cloud, Firebase) —
removing it from a later commit does not remove it from git history.
