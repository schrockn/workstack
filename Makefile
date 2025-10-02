.PHONY: format pyright test publish

format:
	uv run ruff format

pyright:
	uv run pyright

test:
	uv run pytest

# Publish to PyPI. Token is read from ~/.pypirc
publish:
	uvx uv-publish
