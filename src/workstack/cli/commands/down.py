from pathlib import Path

import click

from workstack.cli.commands.switch import (
    _activate_root_repo,
    _activate_worktree,
    _ensure_graphite_enabled,
    _resolve_down_navigation,
)
from workstack.cli.core import discover_repo_context
from workstack.core.context import WorkstackContext


@click.command("down")
@click.option(
    "--script", is_flag=True, help="Print only the activation script without usage instructions."
)
@click.pass_obj
def down_cmd(ctx: WorkstackContext, script: bool) -> None:
    """Move to parent branch in Graphite stack.

    With shell integration (recommended):
      workstack down

    The shell wrapper function automatically activates the worktree.
    Run 'workstack init --shell' to set up shell integration.

    Without shell integration:
      source <(workstack down --script)

    This will cd to the parent branch's worktree (or root repo if parent is trunk),
    create/activate .venv, and load .env variables.
    Requires Graphite to be enabled: 'workstack config set use_graphite true'
    """
    _ensure_graphite_enabled(ctx)
    repo = discover_repo_context(ctx, Path.cwd())

    # Get current branch
    current_branch = ctx.git_ops.get_current_branch(Path.cwd())
    if current_branch is None:
        click.echo("Error: Not currently on a branch (detached HEAD)", err=True)
        raise SystemExit(1)

    # Get all worktrees for checking if target has a worktree
    worktrees = ctx.git_ops.list_worktrees(repo.root)

    # Resolve navigation to get target branch or 'root'
    target_name = _resolve_down_navigation(ctx, repo, current_branch, worktrees)

    # Check if target_name refers to 'root' which means root repo
    if target_name == "root":
        _activate_root_repo(repo, script, "down")

    _activate_worktree(repo, target_name, script, "down")
