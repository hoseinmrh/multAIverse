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
