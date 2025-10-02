.PHONY: format pyright test publish

format:
	uv run ruff format

pyright:
	uv run pyright

test:
	uv run pytest

# Publish to PyPI. Token is read from ~/.pypirc or the TWINE_PASSWORD environment variable
publish:
	uv build
	uv run twine upload dist/*
