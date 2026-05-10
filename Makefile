.PHONY: api api-test api-lint api-fmt mcp mcp-test mcp-lint mcp-fmt up down test lint fmt help

help:
	@echo "Targets:"
	@echo "  api / mcp           - run dev server"
	@echo "  api-test / mcp-test - run pytest"
	@echo "  api-lint / mcp-lint - ruff check + mypy"
	@echo "  api-fmt / mcp-fmt   - ruff format"
	@echo "  up / down           - docker compose up/down for local infra"
	@echo "  test / lint / fmt   - run target across both python apps"

api:
	cd apps/api && uv run uvicorn app.main:app --reload --port 8000

api-test:
	cd apps/api && uv run python -m pytest

api-lint:
	cd apps/api && uv run python -m ruff check . && uv run python -m mypy app

api-fmt:
	cd apps/api && uv run python -m ruff format .

mcp:
	cd apps/mcp && uv run python -m app.main

mcp-test:
	cd apps/mcp && uv run python -m pytest

mcp-lint:
	cd apps/mcp && uv run python -m ruff check . && uv run python -m mypy app

mcp-fmt:
	cd apps/mcp && uv run python -m ruff format .

up:
	docker compose -f infra/docker/docker-compose.yml up -d

down:
	docker compose -f infra/docker/docker-compose.yml down

test: api-test mcp-test
lint: api-lint mcp-lint
fmt: api-fmt mcp-fmt
