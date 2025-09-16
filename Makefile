.PHONY: format pyright test

format:
	uv run ruff format

pyright:
	uv run pyright

test:
	uv run pytest
