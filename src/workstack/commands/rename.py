from pathlib import Path

import click

from workstack.commands.create import make_env_content, sanitize_worktree_name
from workstack.commands.switch import complete_worktree_names
from workstack.config import load_config
from workstack.context import WorkstackContext
from workstack.core import discover_repo_context, ensure_work_dir, worktree_path_for


@click.command("rename")
@click.argument("old_name", metavar="OLD_NAME", shell_complete=complete_worktree_names)
@click.argument("new_name", metavar="NEW_NAME")
@click.pass_obj
def rename_cmd(ctx: WorkstackContext, old_name: str, new_name: str) -> None:
    """Rename a worktree directory.

    Renames the worktree directory and updates git metadata.
    The .env file is regenerated with updated paths and name.
    """
    # Sanitize new name
    sanitized_new_name = sanitize_worktree_name(new_name)

    repo = discover_repo_context(ctx, Path.cwd())
    work_dir = ensure_work_dir(repo)

    old_path = worktree_path_for(work_dir, old_name)
    new_path = worktree_path_for(work_dir, sanitized_new_name)

    # Validate old worktree exists
    if not old_path.exists() or not old_path.is_dir():
        click.echo(f"Worktree not found: {old_path}", err=True)
        raise SystemExit(1)

    # Validate new path doesn't already exist
    if new_path.exists():
        click.echo(f"Destination already exists: {new_path}", err=True)
        raise SystemExit(1)

    # Move via git worktree move
    ctx.git_ops.move_worktree(repo.root, old_path, new_path)

    # Regenerate .env file with updated paths and name
    cfg = load_config(work_dir)
    env_content = make_env_content(
        cfg, worktree_path=new_path, repo_root=repo.root, name=sanitized_new_name
    )
    (new_path / ".env").write_text(env_content, encoding="utf-8")

    click.echo(f"Renamed worktree: {old_name} -> {sanitized_new_name}")
    click.echo(str(new_path))
