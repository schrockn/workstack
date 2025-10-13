.PHONY: format format-check lint prettier prettier-check pyright upgrade-pyright test all-ci clean publish fix

prettier:
	prettier --write '**/*.md' --ignore-path .gitignore

prettier-check:
	prettier --check '**/*.md' --ignore-path .gitignore

format:
	uv run ruff format

format-check:
	uv run ruff format --check

lint:
	uv run ruff check

fix:
	uv run ruff check --fix --unsafe-fixes

pyright:
	uv run pyright

upgrade-pyright:
	uv remove pyright --group dev && uv add --dev pyright

test:
	uv run pytest

all-ci: lint format-check prettier-check pyright test

# Clean build artifacts
clean:
	rm -rf dist/*.whl dist/*.tar.gz

# Build both devclikit and workstack packages
build: clean
	cd packages/devclikit && uv build
	uv build

# Publish both packages to PyPI (devclikit first, then workstack)
# Credentials are read from ~/.pypirc
publish: build
	@echo "Publishing devclikit..."
	uvx uv-publish ./dist/devclikit-*.whl ./dist/devclikit-*.tar.gz
	@echo "Publishing workstack..."
	uvx uv-publish ./dist/workstack-*.whl ./dist/workstack-*.tar.gz
	@echo "✓ Both packages published successfully"
