# Contributing to ClipContext

Thanks for considering a contribution. This is a hackathon-origin project
now being kept to open-source standards — contributions are welcome, but
please read this before opening a PR.

## Before you start

- For anything larger than a small fix (a new feature, a schema change, a
  new pipeline stage), open an issue first to discuss the approach. Small
  bug fixes and doc improvements can go straight to a PR.
- Read [AGENTS.md](AGENTS.md) — it lists the non-negotiable invariants
  this codebase maintains (provider fallback truthfulness, auth boundary
  separation, in-memory-state-implies-single-instance, etc.). A PR that
  removes one of these without discussion will likely be asked to change.
- Read [docs/Architecture.md](docs/Architecture.md) for the system shape
  before touching a module you haven't worked in before.

## Local setup

Full walkthrough: [docs/DeveloperGuide.md](docs/DeveloperGuide.md) and
[QUICKSTART.md](QUICKSTART.md). Short version:

```bash
git clone <your-fork-url>
cd act2-captioner
make setup     # creates .venv, installs Python + Node deps, copies .env templates
# fill in .env with at least FIREWORKS_API_KEY, YOUTUBE_API_KEY, GEMINI_API_KEY

make backend   # terminal 1 — FastAPI on :8000
make frontend  # terminal 2 — Next.js on :3000
```

## Making a change

1. Create a branch off `main`: `git checkout -b fix/short-description`.
2. Make the smallest change that solves the problem. This codebase
   deliberately avoids speculative abstraction — see the "no unnecessary
   complexity" note in [docs/DeveloperGuide.md](docs/DeveloperGuide.md).
3. If you touched `src/`, run `make test` (pytest, all external calls
   mocked — no real API keys or GPU needed to run the suite).
4. If you touched `frontend/`, run `cd frontend && npm run lint && npx tsc --noEmit && npm run build`.
5. If you touched a Pydantic model in `src/models/` or
   `src/pipeline/schemas.py`, update the matching TypeScript type in
   `frontend/types/*.ts` — these are hand-kept in sync, not generated.
6. If you touched an AI prompt (`src/prompts/`, `src/models/discriminator/d_prompt.txt`,
   or any inline prompt in `src/ai/`), see
   [docs/PROMPT_ENGINEERING.md](docs/PROMPT_ENGINEERING.md) for the
   rationale behind the current prompts before changing them, and update
   that doc if your change is a deliberate improvement.

## Commit messages

Plain, descriptive, present-tense summaries of *why*, not a changelog of
every line touched. No enforced format (no Conventional Commits
requirement), but keep the first line under ~72 characters.

## Pull requests

- Fill out the PR template (auto-populated when you open a PR).
- Keep PRs scoped to one concern. A PR that fixes a bug and reformats
  unrelated files is harder to review and more likely to get blocked.
- Note any behavior change explicitly in the PR description, even a small
  one — this repo has several deliberately-non-obvious behaviors (see
  AGENTS.md's invariants list) and reviewers need to know if you changed
  one on purpose vs. accidentally.
- CI (`.github/workflows/`) runs backend tests, frontend build/lint/
  typecheck automatically. A PR won't merge with a red check.

## Code style

- **Python**: the codebase uses an unusually vertical, one-argument-per-line
  formatting style in many places — match the surrounding file's style
  rather than reflowing it to a different convention. `ruff check` (config
  in `pyproject.toml`) enforces correctness rules (unused imports,
  undefined names) but not formatting.
- **TypeScript/React**: standard `eslint-config-next` rules
  (`frontend/.eslintrc.json`), enforced via `npm run lint`.
- Comments explain *why*, not *what* — see the existing codebase for the
  house style. Don't add comments that just restate the code.

## Reporting bugs / requesting features

Use the GitHub issue templates (`.github/ISSUE_TEMPLATE/`). Include
reproduction steps for bugs — "it doesn't work" without steps is hard to
act on.

## Security issues

Do not open a public issue for a security vulnerability — see
[SECURITY.md](SECURITY.md).

## License

By contributing, you agree your contributions are licensed under this
project's [MIT License](LICENSE).
