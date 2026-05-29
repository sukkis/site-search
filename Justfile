test:
    uv run pytest

check:
    uv run ruff check
    uv run mypy site_search

ci: check
    uv run pytest -m "not local_only"

all: check test
