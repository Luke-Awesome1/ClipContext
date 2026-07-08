.PHONY: setup backend frontend test lint build

PYTHON := python3.13

setup:
	$(PYTHON) -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt
	cd frontend && npm ci
	@test -f .env || cp .env.example .env
	@test -f frontend/.env.local || cp frontend/.env.local.example frontend/.env.local
	@echo "Now edit .env with your FIREWORKS_API_KEY, YOUTUBE_API_KEY, GEMINI_API_KEY."

backend:
	.venv/bin/uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm run dev

test:
	.venv/bin/python -m pytest tests/ -v

lint:
	cd frontend && npm run lint

build:
	cd frontend && npm run build
