from __future__ import annotations

from pathlib import Path
import re
import tomllib


def detect_root_project_name(repo_root: Path) -> str | None:
    """Return the declared project name at the repo root, if any.

    Checks root `pyproject.toml`'s `[project].name`. If absent, tries to heuristically
    extract from `setup.py` by matching `name="..."` or `name='...'`.
    """

    root_pyproject = repo_root / "pyproject.toml"
    if root_pyproject.exists():
        try:
            data = tomllib.loads(root_pyproject.read_text(encoding="utf-8"))
            project = data.get("project") or {}
            name = project.get("name")
            if isinstance(name, str) and name:
                return name
        except Exception:
            pass

    setup_py = repo_root / "setup.py"
    if setup_py.exists():
        try:
            text = setup_py.read_text(encoding="utf-8")
            m = re.search(r"name\s*=\s*['\"]([^'\"]+)['\"]", text)
            if m:
                return m.group(1)
        except Exception:
            pass

    return None


def is_repo_named(repo_root: Path, expected_name: str) -> bool:
    """Return True if the root project name matches `expected_name` (case-insensitive)."""
    name = detect_root_project_name(repo_root)
    return (name or "").lower() == expected_name.lower()
