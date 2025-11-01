"""Disable command for disabling hooks."""

import click

from dot_agent_kit.commands.hook.utils import parse_hook_path
from dot_agent_kit.io import (
    get_user_claude_dir,
    update_hook_enabled,
)


@click.command("disable")
@click.argument("hook_path")
def disable_hook(hook_path: str) -> None:
    """Disable a specific hook.

    HOOK_PATH format: kit-name/hook-name

    Example:
        dot-agent hook disable my-kit/my-hook
    """
    claude_dir = get_user_claude_dir()
    hooks_dir = claude_dir / ".dot-agent" / "hooks"

    hooks_toml = parse_hook_path(hook_path, hooks_dir)
    hook_name = hook_path.split("/")[1]

    try:
        update_hook_enabled(hooks_toml, hook_name, enabled=False)
        click.echo(f"✓ Disabled hook: {hook_path}")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1) from e
