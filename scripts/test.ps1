$ErrorActionPreference = "Stop"
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
