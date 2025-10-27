"""List command for displaying available and installed kits."""

import json

import click

from dot_agent_kit.io.registry import load_bundled_registry
from dot_agent_kit.io.state import load_project_config


@click.command()
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format")
def list_cmd(json_output: bool) -> None:
    """List available and installed kits."""
    registry = load_bundled_registry()
    config = load_project_config()

    # Build unified view of all kits
    kits_info = []

    # Track which registry entries are installed
    installed_names = {kit.kit_id for kit in config.kits.values()}

    # Add all registry entries (installed or not)
    for entry in registry.entries:
        is_installed = entry.name in installed_names
        installed_kit = config.get_kit(entry.name) if is_installed else None

        kits_info.append(
            {
                "name": entry.name,
                "version": installed_kit.version if installed_kit else "latest",
                "description": entry.description,
                "installed": is_installed,
                "url": entry.url,
            }
        )

    # Add any installed kits not in registry (edge case)
    for kit_id, kit in config.kits.items():
        if kit_id not in {entry.name for entry in registry.entries}:
            kits_info.append(
                {
                    "name": kit_id,
                    "version": kit.version,
                    "description": "(not in registry)",
                    "installed": True,
                    "url": "",
                }
            )

    if not kits_info:
        click.echo("No kits available")
        return

    if json_output:
        # Output as JSON
        click.echo(json.dumps(kits_info, indent=2))
    else:
        # Output as table
        _print_table(kits_info)


def _print_table(kits_info: list[dict]) -> None:
    """Print kits information as a formatted table."""
    # Find max widths for each column
    max_name_len = max(len(kit["name"]) for kit in kits_info)
    max_version_len = max(len(kit["version"]) for kit in kits_info)

    # Print header
    click.echo(f"{'STATUS':<8} {'NAME':<{max_name_len}} {'VERSION':<{max_version_len}} DESCRIPTION")
    click.echo("-" * (8 + max_name_len + max_version_len + 50))

    # Print each kit
    for kit in kits_info:
        status = "✓" if kit["installed"] else " "
        name = kit["name"]
        version = kit["version"]
        description = kit["description"]

        click.echo(f"{status:<8} {name:<{max_name_len}} {version:<{max_version_len}} {description}")
