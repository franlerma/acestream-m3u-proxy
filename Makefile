.PHONY: install dev lint typecheck test run clean up down

install:
	uv sync --extra dev

dev:
	uv sync --extra dev

lint:
	uv run ruff check src/ tests/
	uv run ruff format src/ tests/

typecheck:
	uv run mypy src/

test:
	uv run pytest

run:
	uv run python -m src.acestream_proxy.main

clean:
	rm -rf .venv __pycache__ .mypy_cache .ruff_cache .pytest_cache dist

up:
	docker compose up --build -d

down:
	docker compose down
