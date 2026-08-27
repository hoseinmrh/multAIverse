SHELL := /bin/bash
export UV_CACHE_DIR := $(CURDIR)/backend/.uv-cache
BACKEND_HOST ?= 127.0.0.1
BACKEND_PORT ?= 8000
FRONTEND_HOST ?= 127.0.0.1
FRONTEND_PORT ?= 3000

.PHONY: setup dev backend-dev frontend-dev test lint format format-check typecheck build seed reset-db simulation-demo mock-narrative-demo

setup:
	cd backend && uv sync --all-groups --frozen
	CI=true pnpm install --frozen-lockfile

dev:
	BACKEND_HOST="$(BACKEND_HOST)" BACKEND_PORT="$(BACKEND_PORT)" FRONTEND_HOST="$(FRONTEND_HOST)" FRONTEND_PORT="$(FRONTEND_PORT)" bash scripts/dev.sh

backend-dev:
	cd backend && uv run uvicorn app.main:app --reload --host "$(BACKEND_HOST)" --port "$(BACKEND_PORT)"

frontend-dev:
	pnpm --dir frontend exec next dev --hostname "$(FRONTEND_HOST)" --port "$(FRONTEND_PORT)"

test:
	cd backend && uv run pytest
	pnpm --dir frontend test

lint:
	cd backend && uv run ruff check app tests migrations ../scripts
	pnpm --dir frontend lint

format:
	cd backend && uv run ruff format app tests migrations ../scripts
	pnpm --dir frontend format

format-check:
	cd backend && uv run ruff format --check app tests migrations ../scripts
	pnpm --dir frontend format:check

typecheck:
	cd backend && uv run mypy app tests ../scripts
	pnpm --dir frontend typecheck

build:
	cd backend && uv run python -m compileall -q app migrations ../scripts
	pnpm --dir frontend build

seed:
	cd backend && PYTHONPATH=. uv run python ../scripts/seed_demo.py

reset-db:
	cd backend && PYTHONPATH=. uv run python ../scripts/reset_database.py

simulation-demo:
	cd backend && PYTHONPATH=. uv run python ../scripts/simulate_demo.py

mock-narrative-demo:
	cd backend && PYTHONPATH=. uv run python ../scripts/mock_narrative_demo.py
