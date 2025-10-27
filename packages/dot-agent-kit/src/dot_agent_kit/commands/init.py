"""Init command for installing dot-agent kits."""

import click

from dot_agent_kit.io.state import load_project_config, save_project_config
from dot_agent_kit.operations.install import install_kit
from dot_agent_kit.sources.resolver import SourceResolver


@click.command()
@click.option("--package", help="Python package name")
@click.option("--github", help="GitHub repository URL")
@click.option("--kit", help="Kit name from registry")
@click.option("--force", is_flag=True, help="Overwrite existing files")
def init(package: str, github: str, kit: str, force: bool) -> None:
    """Initialize a dot-agent kit."""
    # Validate that exactly one source is specified
    sources = [package, github, kit]
    if sum(bool(s) for s in sources) != 1:
        click.echo("Specify exactly one of: --package, --github, or --kit", err=True)
        raise SystemExit(1)

    resolver = SourceResolver()

    # Resolve the source
    if package:
        source = resolver.resolve_from_package(package)
        package_name = package
    elif github:
        source = resolver.resolve_from_github(github)
        if not source:
            raise SystemExit(1)
        package_name = source.package_name
    else:  # kit
        source = resolver.resolve_from_registry(kit)
        if not source:
            raise SystemExit(1)
        package_name = source.package_name

    # Install the kit
    config = load_project_config()
    installed_kit = install_kit(package_name, config, force=force)

    # Update configuration
    config.add_kit(installed_kit)
    save_project_config(config)
