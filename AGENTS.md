# Repository Guidelines

## Project Structure & Module Organization
- Source code lives under `src/workstack/`. The package name is `workstack` and the CLI entry point is `workstack:main` (see `pyproject.toml`).
- Add new modules in `src/workstack/` using small, focused files. Keep the public API minimal via `src/workstack/__init__.py`.
- Place tests under `tests/` mirroring the source layout (e.g., `tests/test_module.py` for `src/work/module.py`).

## Environment & Tooling
- Workflow: use `uv sync` for environment and dependency management; run tools via `uv run`.
- Linting/formatting: Ruff
- Type checking: Pyright
- Testing: Pytest

## Coding Style & Naming Conventions
- Python 3.13; follow PEP 8 with 4‑space indentation and type hints everywhere.
- Names: modules/packages `snake_case`; classes `PascalCase`; functions/variables `snake_case`; constants `UPPER_SNAKE_CASE`.
- Keep functions short; prefer pure functions. Document public functions with concise docstrings.
 - Ruff is configured in `pyproject.toml` (import sorting, lint rules).

## Testing Guidelines
- Use Pytest. Put tests in `tests/` and name files `test_*.py` with test functions `test_*`.
- Execute tests via the uv workflow (e.g., with `uv run`). Coverage can target the `workstack` package.
- Aim for meaningful coverage on new/changed code and include edge cases.
 - Pytest is configured in `pyproject.toml` (`testpaths`, default `-q`).

## Commit & Pull Request Guidelines
- Commits: imperative mood, concise subject (≤72 chars), descriptive body when needed. Example: `feat: add task parser for workstack CLI`.
- Group related changes; avoid mixing refactors with features.
- PRs: include a clear description, linked issues, test plan (commands/output), and notes on breaking changes. Add screenshots or sample CLI output when relevant.

## Security & Configuration Tips
- Do not commit secrets or tokens. Use environment variables and local `.env` files (keep out of VCS).
- Python version is pinned in `.python-version`; prefer matching your local interpreter to that version.
