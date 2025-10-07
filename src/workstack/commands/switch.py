from pathlib import Path

import click
from click.testing import CliRunner

from workstack.context import WorkstackContext, create_context
from workstack.core import discover_repo_context, ensure_work_dir, worktree_path_for


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
    ctx: click.Context, param: click.Parameter | None, incomplete: str
) -> list[str]:
    """Shell completion for worktree names. Includes 'root' for the repository root.

    This is a shell completion function, which is an acceptable error boundary.
    Exceptions are caught to provide graceful degradation - if completion fails,
    we return an empty list rather than breaking the user's shell experience.

    Args:
        ctx: Click context
        param: Click parameter (unused, but required by Click's completion protocol)
        incomplete: Partial input string to complete
    """
    try:
        # Get WorkstackContext from click.Context.obj
        # During shell completion, ctx.obj may not be initialized yet, so we create
        # a context on-demand if needed
        workstack_ctx = ctx.obj if isinstance(ctx.obj, WorkstackContext) else ctx.find_root().obj
        if not isinstance(workstack_ctx, WorkstackContext):
            # Create context for shell completion (CLI group callback not run yet)
            workstack_ctx = create_context(dry_run=False)

        repo = discover_repo_context(workstack_ctx, Path.cwd())
        work_dir = repo.work_dir

        # Include 'root' for root repo
        names = []
        if "root".startswith(incomplete):
            names.append("root")

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
@click.pass_obj
def switch_cmd(ctx: WorkstackContext, name: str, script: bool) -> None:
    """Switch to a worktree and activate its environment.

    With shell integration (recommended):
      workstack switch NAME

    The shell wrapper function automatically activates the worktree.
    Run 'workstack init --shell' to set up shell integration.

    Without shell integration:
      source <(workstack switch NAME --script)

    NAME can be a worktree name, or 'root' to switch to the root repo.
    This will cd to the worktree, create/activate .venv, and load .env variables.
    """

    repo = discover_repo_context(ctx, Path.cwd())

    # Check if user is trying to switch to main/master (should use root instead)
    if name.lower() in ("main", "master"):
        click.echo(
            f'Error: "{name}" cannot be used as a worktree name.\n'
            f"To switch to the {name} branch in the root repository, use:\n"
            f"  workstack switch root",
            err=True,
        )
        raise SystemExit(1)

    # Check if name refers to 'root' which means root repo
    if name == "root":
        # Switch to root repo
        root_path = repo.root
        if script:
            # Generate activation script for root repo (similar to worktrees)
            venv_path = root_path / ".venv"
            venv_activate = venv_path / "bin" / "activate"

            lines = [
                "# work activate-script (root repo)",
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
                'echo "Switched to root repo: $(pwd)"',
            ]
            click.echo("\n".join(lines) + "\n", nl=True)
        else:
            click.echo(
                "Shell integration not detected. "
                "Run 'workstack init --shell' to set up automatic activation."
            )
            click.echo("\nOr use: source <(workstack switch root --script)")
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
        click.echo(
            "Shell integration not detected. "
            "Run 'workstack init --shell' to set up automatic activation."
        )
        click.echo(f"\nOr use: source <(workstack switch {name} --script)")


@click.command(
    "__switch",
    hidden=True,
    add_help_option=False,
    context_settings={"ignore_unknown_options": True, "allow_interspersed_args": False},
)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def hidden_switch_cmd(args: tuple[str, ...]) -> None:
    """Hidden command used by shell wrapper to handle switch logic.

    This command intelligently delegates to the regular switch command
    or outputs the activation script based on the arguments.

    If arguments indicate the user wants help or explicit script output,
    we output a special marker that tells the shell wrapper to pass through
    to the regular command instead of using eval.
    """
    # Check if help flags or --script are present
    # These should pass through to the regular command, not be eval'd
    if "-h" in args or "--help" in args or "--script" in args:
        # Output special marker for shell wrapper to detect and pass through
        click.echo("__WORKSTACK_PASSTHROUGH__")
        raise SystemExit(0)

    # Normal case: output activation script
    # args should be just the worktree name
    if len(args) != 1:
        click.echo("Usage: workstack __switch NAME", err=True)
        raise SystemExit(1)

    name = args[0]

    # Use the regular switch logic with --script flag
    runner = CliRunner()
    result = runner.invoke(switch_cmd, [name, "--script"], obj=create_context(dry_run=False))

    # If the command failed, output passthrough marker so the shell wrapper
    # will call the regular command instead of trying to eval the error message
    if result.exit_code != 0:
        click.echo("__WORKSTACK_PASSTHROUGH__")
        raise SystemExit(result.exit_code)

    click.echo(result.output, nl=False)
    raise SystemExit(result.exit_code)
