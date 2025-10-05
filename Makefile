.PHONY: format prettier prettier-check pyright test all-ci publish

prettier:
	prettier --write '**/*.md' --ignore-path .gitignore

prettier-check:
	prettier --check '**/*.md' --ignore-path .gitignore

format:
	uv run ruff format

pyright:
	uv run pyright

test:
	uv run pytest

all-ci: format prettier pyright test

# Publish to PyPI. Token is read from ~/.pypirc
publish:
	uvx uv-publish
