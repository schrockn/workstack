"""Search command for finding kits in the registry."""

import click


@click.command()
@click.argument("term", required=False)
def search(term: str | None) -> None:
    """Search the dot-agent kit registry."""
    raise NotImplementedError("Coming in commit 3")
