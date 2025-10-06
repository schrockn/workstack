.PHONY: format lint prettier prettier-check pyright test all-ci clean publish fix

prettier:
	prettier --write '**/*.md' --ignore-path .gitignore

prettier-check:
	prettier --check '**/*.md' --ignore-path .gitignore

format:
	uv run ruff format

lint:
	uv run ruff check

fix:
	uv run ruff check --fix --unsafe-fixes

pyright:
	uv run pyright

test:
	uv run pytest

all-ci: lint format prettier-check pyright test

# Clean build artifacts
clean:
	rm -rf dist/*.whl dist/*.tar.gz

# Publish to PyPI. Token is read from ~/.pypirc
publish: clean
	uv build
	uvx uv-publish
