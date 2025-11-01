"""List command for showing installed hooks."""

import click

from dot_agent_kit.io import (
    get_user_claude_dir,
    load_hook_manifest,
)


@click.command("list")
def list_hooks() -> None:
    """List all installed hooks."""
    claude_dir = get_user_claude_dir()
    hooks_dir = claude_dir / ".dot-agent" / "hooks"

    if not hooks_dir.exists():
        click.echo("No hooks installed")
        return

    # Scan for kit hook directories
    kit_dirs = [d for d in hooks_dir.iterdir() if d.is_dir()]

    if not kit_dirs:
        click.echo("No hooks installed")
        return

    # Display hooks grouped by kit
    total_hooks = 0
    enabled_hooks = 0

    for kit_dir in sorted(kit_dirs):
        hooks_toml = kit_dir / "hooks.toml"
        if not hooks_toml.exists():
            continue

        manifest = load_hook_manifest(hooks_toml)
        click.echo(f"\n{manifest.kit_id} (v{manifest.kit_version})")

        for hook in manifest.hooks:
            total_hooks += 1
            if hook.enabled:
                enabled_hooks += 1

            status = "✓" if hook.enabled else "✗"
            status_text = (
                click.style("enabled", fg="green")
                if hook.enabled
                else click.style("disabled", fg="red")
            )

            click.echo(f"  {status} {hook.name} [{status_text}]")
            click.echo(f"      Lifecycle: {hook.lifecycle}")
            click.echo(f"      Matcher:   {hook.matcher or '(always)'}")
            if hook.description:
                click.echo(f"      {hook.description}")

    disabled_count = total_hooks - enabled_hooks
    click.echo(f"\nTotal: {total_hooks} hooks ({enabled_hooks} enabled, {disabled_count} disabled)")
