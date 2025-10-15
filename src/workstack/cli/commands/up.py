from pathlib import Path

import click

from workstack.cli.activation import render_activation_script
from workstack.cli.commands.switch import _resolve_up_navigation
from workstack.cli.core import discover_repo_context, ensure_workstacks_dir, worktree_path_for
from workstack.cli.debug import debug_log
from workstack.cli.shell_utils import write_script_to_temp
from workstack.core.context import WorkstackContext


@click.command("up")
@click.option(
    "--script", is_flag=True, help="Print only the activation script without usage instructions."
)
@click.pass_obj
def up_cmd(ctx: WorkstackContext, script: bool) -> None:
    """Move to child branch in Graphite stack.

    With shell integration (recommended):
      workstack up

    The shell wrapper function automatically activates the worktree.
    Run 'workstack init --shell' to set up shell integration.

    Without shell integration:
      source <(workstack up --script)

    This will cd to the child branch's worktree, create/activate .venv, and load .env variables.
    Requires Graphite to be enabled: 'workstack config set use_graphite true'
    """
    # Check Graphite requirement
    if not ctx.global_config_ops.get_use_graphite():
        click.echo(
            "Error: 'up' command requires Graphite to be enabled. "
            "Run 'workstack config set use_graphite true'",
            err=True,
        )
        raise SystemExit(1)

    repo = discover_repo_context(ctx, Path.cwd())

    # Get current branch
    current_branch = ctx.git_ops.get_current_branch(Path.cwd())
    if current_branch is None:
        click.echo("Error: Not currently on a branch (detached HEAD)", err=True)
        raise SystemExit(1)

    # Get all worktrees for checking if target has a worktree
    worktrees = ctx.git_ops.list_worktrees(repo.root)

    # Resolve navigation to get target branch
    target_name = _resolve_up_navigation(ctx, repo, current_branch, worktrees)

    # Get worktree path
    workstacks_dir = ensure_workstacks_dir(repo)
    wt_path = worktree_path_for(workstacks_dir, target_name)

    if not wt_path.exists():
        click.echo(f"Worktree not found: {wt_path}", err=True)
        raise SystemExit(1)

    if script:
        activation_script = render_activation_script(worktree_path=wt_path)
        script_path = write_script_to_temp(
            activation_script,
            command_name="up",
            comment=f"activate {target_name}",
        )

        debug_log(f"Up: Generated script at {script_path}")
        debug_log(f"Up: Script content:\n{activation_script}")
        debug_log(f"Up: File exists? {script_path.exists()}")

        click.echo(str(script_path), nl=False)
    else:
        click.echo(
            "Shell integration not detected. "
            "Run 'workstack init --shell' to set up automatic activation."
        )
        click.echo("\nOr use: source <(workstack up --script)")
