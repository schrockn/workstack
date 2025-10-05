from pathlib import Path

import click

from ..core import discover_repo_context, ensure_work_dir, worktree_path_for
from ..git import detect_default_branch


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


def complete_worktree_names(
    ctx: click.Context, param: click.Parameter, incomplete: str
) -> list[str]:
    """Shell completion for worktree names. Includes default branch (main/master) for root repo.

    This is a shell completion function, which is an acceptable error boundary.
    Exceptions are caught to provide graceful degradation - if completion fails,
    we return an empty list rather than breaking the user's shell experience.
    """
    try:
        repo = discover_repo_context(Path.cwd())
        work_dir = repo.work_dir

        # Include default branch name (main or master) for root repo
        names = []
        default_branch = detect_default_branch(repo.root)
        if default_branch.startswith(incomplete):
            names.append(default_branch)

        # Add worktree directories
        if work_dir.exists():
            names.extend(
                [p.name for p in work_dir.iterdir() if p.is_dir() and p.name.startswith(incomplete)]
            )

        return names
    except Exception:
        # Shell completion error boundary: return empty list for graceful degradation
        return []


@click.command("switch")
@click.argument("name", metavar="NAME", shell_complete=complete_worktree_names)
@click.option(
    "--script", is_flag=True, help="Print only the activation script without usage instructions."
)
def switch_cmd(name: str, script: bool) -> None:
    """Print shell code to switch to a worktree and activate it.

    Usage: source <(workstack switch NAME --script)

    NAME can be a worktree name, or 'main'/'master' to switch to the root repo.
    This will cd to the worktree directory and source its activate.sh script.
    """

    repo = discover_repo_context(Path.cwd())

    # Check if name refers to the default branch (main/master) which means root repo
    default_branch = detect_default_branch(repo.root)

    if name in ("main", "master"):
        # User is trying to switch to root repo via branch name
        if name != default_branch:
            # User specified wrong branch name
            click.echo(
                f"Error: This repository uses '{default_branch}' as the default branch, "
                f"not '{name}'.",
                err=True,
            )
            raise SystemExit(1)

        # Switch to root repo
        root_path = repo.root
        if script:
            # Generate activation script for root repo (similar to worktrees)
            venv_path = root_path / ".venv"
            venv_activate = venv_path / "bin" / "activate"

            lines = [
                f"# work activate-script (root repo - {default_branch})",
                f"cd '{str(root_path)}'",
                "# Create venv if it doesn't exist",
                f"if [ ! -d '{str(venv_path)}' ]; then",
                "  echo 'Creating virtual environment with uv sync...'",
                "  uv sync",
                "fi",
                f"if [ -f '{str(venv_activate)}' ]; then",
                f"  . '{str(venv_activate)}'",
                "fi",
                "# Load .env into the environment (allexport)",
                "set -a",
                "if [ -f ./.env ]; then . ./.env; fi",
                "set +a",
                f'echo "Switched to root repo ({default_branch}): $(pwd)"',
            ]
            click.echo("\n".join(lines) + "\n", nl=True)
        else:
            click.echo(f"source <(workstack switch {default_branch} --script)")
        return

    work_dir = ensure_work_dir(repo)
    wt_path = worktree_path_for(work_dir, name)

    if not wt_path.exists():
        click.echo(f"Worktree not found: {wt_path}", err=True)
        raise SystemExit(1)

    if script:
        activation_script = render_activation_script(worktree_path=wt_path)
        click.echo(activation_script, nl=True)
    else:
        click.echo(f"source <(workstack switch {name} --script)")
