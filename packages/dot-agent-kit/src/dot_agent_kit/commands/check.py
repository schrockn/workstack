"""Check command for verifying kit status."""

import click


@click.command()
@click.option("--validate", is_flag=True, help="Validate artifact frontmatter")
def check(validate: bool) -> None:
    """Check the status of installed kits."""
    raise NotImplementedError("Coming in commit 5")
