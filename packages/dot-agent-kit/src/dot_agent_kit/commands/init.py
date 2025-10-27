"""Init command for installing dot-agent kits."""

import click


@click.command()
@click.option("--package", help="Python package name")
@click.option("--github", help="GitHub repository URL")
@click.option("--kit", help="Kit name from registry")
@click.option("--force", is_flag=True, help="Overwrite existing files")
def init(package: str | None, github: str | None, kit: str | None, force: bool) -> None:
    """Initialize a dot-agent kit."""
    raise NotImplementedError("Coming in commit 4")
