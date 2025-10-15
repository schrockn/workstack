from pathlib import Path

import click

from workstack.cli.activation import render_activation_script
from workstack.cli.commands.switch import _resolve_down_navigation
from workstack.cli.core import discover_repo_context, ensure_workstacks_dir, worktree_path_for
from workstack.cli.debug import debug_log
from workstack.cli.shell_utils import write_script_to_temp
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
    # Check Graphite requirement
    if not ctx.global_config_ops.get_use_graphite():
        click.echo(
            "Error: 'down' command requires Graphite to be enabled. "
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

    # Resolve navigation to get target branch or 'root'
    target_name = _resolve_down_navigation(ctx, repo, current_branch, worktrees)

    # Check if target_name refers to 'root' which means root repo
    if target_name == "root":
        # Switch to root repo
        root_path = repo.root
        if script:
            # Generate activation script for root repo using shared function
            script_content = render_activation_script(
                worktree_path=root_path,
                final_message='echo "Switched to root repo: $(pwd)"',
                comment="work activate-script (root repo)",
            )
            script_path = write_script_to_temp(
                script_content,
                command_name="down",
                comment="activate root",
            )
            click.echo(str(script_path), nl=False)
        else:
            click.echo(f"Switched to root repo: {root_path}")
            click.echo(
                "\nShell integration not detected. "
                "Run 'workstack init --shell' to set up automatic activation."
            )
            click.echo("Or use: source <(workstack down --script)")
        return

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
            command_name="down",
            comment=f"activate {target_name}",
        )

        debug_log(f"Down: Generated script at {script_path}")
        debug_log(f"Down: Script content:\n{activation_script}")
        debug_log(f"Down: File exists? {script_path.exists()}")

        click.echo(str(script_path), nl=False)
    else:
        click.echo(
            "Shell integration not detected. "
            "Run 'workstack init --shell' to set up automatic activation."
        )
        click.echo("\nOr use: source <(workstack down --script)")
