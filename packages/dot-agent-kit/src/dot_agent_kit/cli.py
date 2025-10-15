from pathlib import Path
from typing import NoReturn

import click

from dot_agent_kit import __version__, list_available_files, read_resource_file
from dot_agent_kit.config import (
    DotAgentConfig,
    find_agent_dir,
    get_config_path,
)
from dot_agent_kit.sync import (
    FileSyncResult,
    collect_statuses,
    generate_diff,
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

    click.echo("Available documentation files:")
    for file in files:
        click.echo(f"  {file}")


@main.command()
@click.argument("relative_path")
@click.option("--force", "force_overwrite", is_flag=True, help="Overwrite existing file")
def extract(relative_path: str, force_overwrite: bool) -> None:
    """Extract a specific documentation file into the local .agent directory."""
    agent_dir = _require_agent_dir()

    available = set(list_available_files())
    if relative_path not in available:
        _fail(f"Error: {relative_path} is not provided by dot-agent-kit.")

    local_path = agent_dir / relative_path
    if local_path.exists() and not force_overwrite:
        _fail(f"Error: {relative_path} already exists. Use --force to overwrite.")

    local_path.parent.mkdir(parents=True, exist_ok=True)
    content = read_resource_file(relative_path)
    local_path.write_text(content, encoding="utf-8")
    click.echo(f"Extracted {relative_path} into {agent_dir}")


@main.command()
def check() -> None:
    """Check if managed files are up-to-date."""
    agent_dir = _require_agent_dir()

    config_path = get_config_path(agent_dir)
    config = DotAgentConfig.load(config_path)

    statuses = collect_statuses(agent_dir, config)

    missing = [path for path, status in statuses.items() if status == "missing"]
    different = [path for path, status in statuses.items() if status == "different"]
    excluded = [path for path, status in statuses.items() if status == "excluded"]
    unavailable = [path for path, status in statuses.items() if status == "unavailable"]
    up_to_date = [path for path, status in statuses.items() if status == "up-to-date"]

    click.echo(f"Up-to-date files: {len(up_to_date)}")
    click.echo(f"Missing files: {len(missing)}")
    click.echo(f"Modified files: {len(different)}")
    click.echo(f"Excluded files: {len(excluded)}")
    click.echo(f"Unavailable files: {len(unavailable)}")

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


@main.command()
@click.argument("relative_path")
def diff(relative_path: str) -> None:
    """Show differences between local and packaged versions."""
    agent_dir = _require_agent_dir()

    available = set(list_available_files())
    if relative_path not in available:
        _fail(f"Error: {relative_path} is not provided by dot-agent-kit.")

    local_path = agent_dir / relative_path
    if not local_path.exists():
        _fail(f"Error: {relative_path} does not exist locally.")

    package_content = read_resource_file(relative_path)
    local_content = local_path.read_text(encoding="utf-8")
    if local_content == package_content:
        click.echo(f"No differences for {relative_path}.")
        return

    diff_text = generate_diff(relative_path, local_content, package_content)
    click.echo(diff_text)


@main.command()
def status() -> None:
    """Show a summary of the .agent directory."""
    agent_dir = _require_agent_dir()

    config_path = get_config_path(agent_dir)
    config = DotAgentConfig.load(config_path)
    statuses = collect_statuses(agent_dir, config)

    click.echo(f".agent directory: {agent_dir}")
    click.echo(f"Configured version: {config.version}")
    click.echo(f"Managed files: {len(config.managed_files)}")
    click.echo(f"Excluded files: {len(config.exclude)}")
    click.echo(f"Custom files: {len(config.custom_files)}")

    out_of_date = [path for path, status in statuses.items() if status in {"missing", "different"}]
    if out_of_date:
        click.echo("Files requiring attention:")
        for path in out_of_date:
            click.echo(f"  {path}")
    else:
        click.echo("All managed files are up-to-date.")


if __name__ == "__main__":
    main()
