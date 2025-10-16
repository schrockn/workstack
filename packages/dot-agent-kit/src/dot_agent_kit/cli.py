from datetime import datetime
from pathlib import Path
from typing import NoReturn

import click

from dot_agent_kit import __version__, list_available_files, read_resource_file
from dot_agent_kit.config import (
    DotAgentConfig,
    find_agent_dir,
    get_config_path,
    parse_markdown_frontmatter,
)
from dot_agent_kit.local import LocalFileDiscovery
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

    # Count local files
    discovery = LocalFileDiscovery(agent_dir)
    local_files = discovery.discover_local_files()

    click.echo(f".agent directory: {agent_dir}")
    click.echo(f"Configured version: {config.version}")
    click.echo(f"Installed files: {len(config.installed_files)}")
    click.echo(f"Excluded files: {len(config.exclude)}")
    click.echo(f"Custom files: {len(config.custom_files)}")
    click.echo(f"Local files: {len(local_files)}")

    out_of_date = [path for path, status in statuses.items() if status in {"missing", "different"}]
    if out_of_date:
        click.echo("Files requiring attention:")
        for path in out_of_date:
            click.echo(f"  {path}")
    else:
        click.echo("All installed files are up-to-date.")


@main.command()
@click.option("--pattern", help="Glob pattern to filter files (e.g., '*.md', 'docs/*')")
@click.option(
    "--long",
    "long_format",
    is_flag=True,
    help="Show detailed output with size and modification time",
)
def inspect(pattern: str | None, long_format: bool) -> None:
    """List all local files in the .agent directory.

    This shows files in the .agent directory root and subdirectories,
    excluding installed package files in packages/.
    """
    agent_dir = _require_agent_dir()
    discovery = LocalFileDiscovery(agent_dir)
    files = discovery.discover_local_files(pattern=pattern)

    if not files:
        if pattern:
            click.echo(f"No local files match pattern: {pattern}")
        else:
            click.echo("No local files found in .agent directory.")
        return

    if long_format:
        click.echo(f"Local files in {agent_dir}:\n")
        for file in files:
            size_kb = file.size / 1024
            modified = datetime.fromtimestamp(file.modified_time).strftime("%Y-%m-%d %H:%M:%S")
            click.echo(f"  {file.relative_path}")
            click.echo(f"    Size: {size_kb:.1f} KB")
            click.echo(f"    Modified: {modified}")
            click.echo(f"    Type: {file.file_type}")
            if file != files[-1]:
                click.echo("")
    else:
        click.echo(f"Local files in {agent_dir}:\n")
        categories = discovery.categorize_files(files)

        for category in sorted(categories.keys()):
            if category == "root":
                click.echo("Root:")
            else:
                click.echo(f"{category}/:")

            for file in categories[category]:
                click.echo(f"  {file.relative_path}")

            if category != sorted(categories.keys())[-1]:
                click.echo("")


@main.command()
@click.argument("relative_path")
def show(relative_path: str) -> None:
    """Display the contents of a local file in the .agent directory.

    This reads files from the .agent directory root and subdirectories,
    excluding installed package files in packages/.
    """
    agent_dir = _require_agent_dir()
    discovery = LocalFileDiscovery(agent_dir)

    # Exception handling acceptable: read_file() provides detailed error messages
    # for different failure modes (not found, is directory, in packages/).
    # We catch to provide user-friendly CLI messages.
    try:
        content = discovery.read_file(relative_path)
    except FileNotFoundError:
        _fail(f"Error: {relative_path} not found in {agent_dir}")
    except IsADirectoryError:
        _fail(f"Error: {relative_path} is a directory. Use 'dot-agent inspect' to list files.")
    except ValueError as e:
        _fail(f"Error: {e}")

    click.echo(content)


@main.command()
def tree() -> None:
    """Show directory structure of the .agent directory.

    Displays a tree view distinguishing local files from installed packages.
    """
    agent_dir = _require_agent_dir()
    discovery = LocalFileDiscovery(agent_dir)

    # Get all files including directories
    files = discovery.discover_local_files(include_directories=True)

    if not files:
        click.echo("No local files found in .agent directory.")
        return

    click.echo(f"{agent_dir}/")

    # Build tree structure
    tree_dict: dict[str, list[str]] = {}
    for file in files:
        parts = Path(file.relative_path).parts
        if len(parts) == 1:
            if "." not in tree_dict:
                tree_dict["."] = []
            tree_dict["."].append(file.relative_path)
        else:
            parent = str(Path(*parts[:-1]))
            if parent not in tree_dict:
                tree_dict[parent] = []
            tree_dict[parent].append(file.relative_path)

    # Display root files first
    if "." in tree_dict:
        for item in sorted(tree_dict["."]):
            file = discovery.get_file(item)
            if file and file.is_directory:
                click.echo(f"  {item}/")
            else:
                click.echo(f"  {item}")

    # Display subdirectories
    for parent in sorted(tree_dict.keys()):
        if parent == ".":
            continue

        click.echo(f"  {parent}/")
        for item in sorted(tree_dict[parent]):
            relative_to_parent = Path(item).name
            file = discovery.get_file(item)
            if file and file.is_directory:
                click.echo(f"    {relative_to_parent}/")
            else:
                click.echo(f"    {relative_to_parent}")

    # Note about packages
    packages_dir = agent_dir / "packages"
    if packages_dir.exists():
        click.echo("\n(packages/ directory not shown - contains installed package files)")


if __name__ == "__main__":
    main()
