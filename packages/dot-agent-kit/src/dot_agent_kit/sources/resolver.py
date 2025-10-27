"""Source resolver for finding kits from various inputs."""

from dot_agent_kit.io.registry import load_bundled_registry
from dot_agent_kit.sources.standalone import StandaloneSource
from dot_agent_kit.utils.github import github_url_to_package_name


class SourceResolver:
    """Resolve kit sources from various inputs."""

    def resolve_from_package(self, package_name: str) -> StandaloneSource:
        """Resolve a source from a package name."""
        return StandaloneSource(package_name)

    def resolve_from_github(self, github_url: str) -> StandaloneSource | None:
        """Resolve a source from a GitHub URL."""
        package_name = github_url_to_package_name(github_url)
        source = StandaloneSource(package_name)

        if source.is_available():
            return source

        # Package not installed, provide instructions
        import click

        click.echo("ℹ Package not installed. Run:", err=True)
        click.echo(f"  uv pip install git+{github_url}", err=True)
        return None

    def resolve_from_registry(self, kit_name: str) -> StandaloneSource | None:
        """Resolve a source from a registry name."""
        registry = load_bundled_registry()
        entry = registry.find_by_name(kit_name)

        if not entry:
            import click

            click.echo(f"Kit not found in registry: {kit_name}", err=True)
            return None

        # Use the explicit package_name from the registry entry
        package_name = entry.package_name
        source = StandaloneSource(package_name)

        if source.is_available():
            return source

        # Package not installed, provide instructions with GitHub URL
        import click

        click.echo("ℹ Package not installed. Run:", err=True)
        click.echo(f"  uv pip install git+{entry.url}", err=True)
        return None
