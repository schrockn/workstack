from __future__ import annotations

from pathlib import Path


def render_activation_script(*, worktree_path: Path) -> str:
    """Return shell code that activates a worktree's venv and .env.

    The script:
      - cds into the worktree
      - creates .venv with `uv sync` if not present
      - sources `.venv/bin/activate` if present
      - exports variables from `.env` if present
    Works in bash and zsh.
    """

    wt = str(worktree_path)
    venv_activate = worktree_path / ".venv" / "bin" / "activate"
    lines: list[str] = [
        "# work activate-script",  # comment for visibility
        f"cd {quote(wt)}",
        "# Create venv if it doesn't exist",
        f"if [ ! -d {quote(str(worktree_path / '.venv'))} ]; then",
        "  echo 'Creating virtual environment with uv sync...'",
        "  uv sync",
        "fi",
        f"if [ -f {quote(str(venv_activate))} ]; then",
        f"  . {quote(str(venv_activate))}",
        "fi",
        "# Load .env into the environment (allexport)",
        "set -a",
        "if [ -f ./.env ]; then . ./.env; fi",
        "set +a",
        "# Optional: show where we are",
        'echo "Activated worktree: $(pwd)"',
    ]
    return "\n".join(lines) + "\n"


def quote(s: str) -> str:
    # Simple single-quote shell escaping
    return "'" + s.replace("'", "'\\''") + "'"
