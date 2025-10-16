from pathlib import Path
from typing import NoReturn

import click

from dot_agent_kit import __version__
from dot_agent_kit.config import (
    DotAgentConfig,
    find_agent_dir,
    get_config_path,
    parse_markdown_frontmatter,
)
from dot_agent_kit.resource_loader import list_available_files, read_resource_file
from dot_agent_kit.sync import (
    FileSyncResult,
    collect_statuses,
    sync_all_files,
)


def _fail(message: str) -> NoReturn:
    """Emit a CLI error and exit."""
    click.echo(message, err=True)
    raise SystemExit(1)


def _require_agent_dir() -> Path:
    """Return the nearest .agent directory or exit if missing."""
    agent_dir = find_agent_dir()
    if agent_dir is None:
        _fail("Error: Not in a repository with a .agent/ directory. Run 'dot-agent init' first.")
    return agent_dir


@click.group()
@click.version_option(version=__version__)
def main() -> None:
    """Manage .agent/ automated documentation folders."""


@main.command()
def init() -> None:
    """Initialize .agent/ directory structure."""
    agent_dir = Path.cwd() / ".agent"
    if agent_dir.exists():
        _fail(f"Error: {agent_dir} already exists")

    tools_dir = agent_dir / "tools"
    tools_dir.mkdir(parents=True)

    config = DotAgentConfig.default()
    config_path = get_config_path(agent_dir)
    config.save(config_path)

    results = sync_all_files(agent_dir, config, force=False, dry_run=False)

    click.echo(f"Initialized .agent/ directory at {agent_dir}")
    for _, result in results.items():
        if result.changed:
            click.echo(f"  {result.message}")


@main.command()
@click.option("--force", "force_update", is_flag=True, help="Overwrite without diff preview")
@click.option("--dry-run", "dry_run_mode", is_flag=True, help="Show actions without writing")
def sync(force_update: bool, dry_run_mode: bool) -> None:
    """Update tool documentation to latest versions."""
    agent_dir = _require_agent_dir()

    config_path = get_config_path(agent_dir)
    config = DotAgentConfig.load(config_path)

    results = sync_all_files(
        agent_dir,
        config,
        force=force_update,
        dry_run=dry_run_mode,
    )

    changed_items: list[tuple[str, FileSyncResult]] = []
    for relative_path, result in results.items():
        if result.changed:
            changed_items.append((relative_path, result))

    if dry_run_mode:
        click.echo(f"Would update {len(changed_items)} files.")
    else:
        click.echo(f"Updated {len(changed_items)} files.")

    for _, result in changed_items:
        click.echo(f"- {result.message}")
        if not force_update and result.diff:
            click.echo(result.diff)


@main.command("list")
def list_files() -> None:
    """Show available documentation files."""
    files = list_available_files()
    if not files:
        click.echo("No documentation files bundled with the package.")
        return

    click.echo("Available documentation files:\n")
    for i, file in enumerate(files):
        content = read_resource_file(file)
        metadata, _ = parse_markdown_frontmatter(content)

        # Add visual separator between entries (but not before first)
        if i > 0:
            click.echo("")

        # File name in bold/bright style
        click.echo(click.style(f"  {file}", bold=True))

        if metadata.description:
            click.echo(f"    {metadata.description}")
        if metadata.url:
            click.echo(click.style(f"    {metadata.url}", dim=True))


@main.command()
def check() -> None:
    """Check if installed files are up-to-date."""
    agent_dir = _require_agent_dir()

    config_path = get_config_path(agent_dir)
    config = DotAgentConfig.load(config_path)

    statuses = collect_statuses(agent_dir, config)

    missing = [path for path, status in statuses.items() if status == "missing"]
    different = [path for path, status in statuses.items() if status == "different"]
    excluded = [path for path, status in statuses.items() if status == "excluded"]
    unavailable = [path for path, status in statuses.items() if status == "unavailable"]
    up_to_date = [path for path, status in statuses.items() if status == "up-to-date"]

    # Validate front matter in all available markdown files
    frontmatter_errors: list[tuple[str, str]] = []
    for file in list_available_files():
        if file.endswith(".md"):
            content = read_resource_file(file)
            try:
                parse_markdown_frontmatter(content)
            except Exception as e:
                frontmatter_errors.append((file, str(e)))

    click.echo(f"Up-to-date files: {len(up_to_date)}")
    click.echo(f"Missing files: {len(missing)}")
    click.echo(f"Modified files: {len(different)}")
    click.echo(f"Excluded files: {len(excluded)}")
    click.echo(f"Unavailable files: {len(unavailable)}")
    click.echo(f"Front matter errors: {len(frontmatter_errors)}")

    if missing:
        click.echo("Missing:")
        for path in missing:
            click.echo(f"  {path}")

    if different:
        click.echo("Modified:")
        for path in different:
            click.echo(f"  {path}")

    if unavailable:
        click.echo("Unavailable (not shipped in this package):")
        for path in unavailable:
            click.echo(f"  {path}")

    if frontmatter_errors:
        click.echo("Front matter errors:")
        for path, error in frontmatter_errors:
            click.echo(f"  {path}: {error}")


if __name__ == "__main__":
    main()
