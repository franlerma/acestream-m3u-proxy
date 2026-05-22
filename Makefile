.PHONY: install dev lint typecheck test run clean

install:
	uv venv .venv
	uv pip install -r requirements.txt

dev:
	uv pip install -r requirements.txt
	uv pip install --dev

lint:
	ruff check src/ tests/
	ruff format src/ tests/

typecheck:
	mypy src/

test:
	pytest --cov=src --cov-report=term-missing

run:
	uv run python -m src.acestream_proxy.main

requirements:
	uv pip compile pyproject.toml -o requirements.txt

clean:
	rm -rf .venv __pycache__ .mypy_cache .ruff_cache .pytest_cache dist