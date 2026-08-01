SHELL := /bin/bash
export UV_CACHE_DIR := $(CURDIR)/backend/.uv-cache

.PHONY: setup dev backend-dev frontend-dev test lint format format-check typecheck build seed reset-db

setup:
	cd backend && uv sync --all-groups --frozen
	CI=true pnpm install --frozen-lockfile

dev:
	bash scripts/dev.sh

backend-dev:
	cd backend && uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

frontend-dev:
	pnpm --dir frontend dev

test:
	cd backend && uv run pytest
	pnpm --dir frontend test

lint:
	cd backend && uv run ruff check app tests
	pnpm --dir frontend lint

format:
	cd backend && uv run ruff format app tests
	pnpm --dir frontend format

format-check:
	cd backend && uv run ruff format --check app tests
	pnpm --dir frontend format:check

typecheck:
	cd backend && uv run mypy app tests
	pnpm --dir frontend typecheck

build:
	cd backend && uv run python -m compileall -q app
	pnpm --dir frontend build

seed:
	@echo "Demo database seeding is introduced in Phase 2." >&2
	@exit 2

reset-db:
	@echo "Database reset is introduced in Phase 2." >&2
	@exit 2
