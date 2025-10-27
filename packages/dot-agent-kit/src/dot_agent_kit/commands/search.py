"""Search command for finding kits in the registry."""

import click

from dot_agent_kit.io.registry import load_bundled_registry


@click.command()
@click.argument("term")
def search(term: str) -> None:
    """Search the dot-agent kit registry."""
    registry = load_bundled_registry()
    results = registry.search(term)

    if not results:
        click.echo(f"No kits found matching '{term}'")
        raise SystemExit(1)

    for entry in results:
        click.echo(f"{entry.name}  {entry.url}")
        if entry.description:
            click.echo(f"  {entry.description}")
