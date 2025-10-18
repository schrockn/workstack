from pathlib import Path
from typing import NoReturn

import click

from dot_agent_kit import __version__
from dot_agent_kit.markdown_header import (
    find_agent_dir,
    parse_markdown_frontmatter,
)
from dot_agent_kit.repo_metadata import get_repo_metadata
from dot_agent_kit.repos import (
    check_for_updates,
    find_all_repos,
    install_to_repo,
    update_repo,
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

    agent_dir.mkdir(parents=True)

    results = sync_all_files(agent_dir, force=False, dry_run=False)

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

    results = sync_all_files(
        agent_dir,
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

    statuses = collect_statuses(agent_dir)

    missing = [path for path, status in statuses.items() if status == "missing"]
    different = [path for path, status in statuses.items() if status == "different"]
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

    # Fail if package files have been modified or are missing
    if different or missing:
        click.echo("", err=True)
        click.echo("Error: Package files are not in sync with bundled versions.", err=True)
        click.echo("", err=True)
        click.echo(
            "Package files in .agent/packages/ are managed by dot-agent-kit",
            err=True,
        )
        click.echo(
            "and should not be edited directly. Run 'dot-agent sync' to restore them.",
            err=True,
        )
        raise SystemExit(1)


@main.command()
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.argument("target", type=click.Path(exists=True, path_type=Path))
def install(source: Path, target: Path) -> None:
    """Install .agent folder from SOURCE into TARGET repository.

    SOURCE must be a .agent directory.
    TARGET must be a repository directory without an existing .agent/ folder.

    Example:
        dot-agent install /path/to/template/.agent /path/to/project
    """
    # Validate and install
    if not source.exists():
        _fail(f"Error: Source path does not exist: {source}")

    if not source.is_dir():
        _fail(f"Error: Source path is not a directory: {source}")

    if source.name != ".agent":
        _fail(f"Error: Source must be a .agent directory, got: {source.name}")

    if not target.exists():
        _fail(f"Error: Target repository does not exist: {target}")

    if not target.is_dir():
        _fail(f"Error: Target repository is not a directory: {target}")

    target_agent = target / ".agent"
    if target_agent.exists():
        _fail(f"Error: Target already has .agent/ directory: {target_agent}")

    # Perform installation
    install_to_repo(source, target)

    click.echo(f"Installed .agent/ folder to {target}")
    click.echo(f"  Source: {source}")

    metadata = get_repo_metadata(target)
    if metadata and metadata.installed_at:
        click.echo(f"  Installed: {metadata.installed_at.strftime('%Y-%m-%d %H:%M:%S')}")


@main.command()
@click.option(
    "--repo", type=click.Path(exists=True, path_type=Path), help="Specific repository to update"
)
@click.option("--all", "update_all", is_flag=True, help="Update all known repositories")
def update(repo: Path | None, update_all: bool) -> None:
    """Update .agent folders in specified or all repositories.

    Use --repo to update a specific repository, or --all to update all known repositories.

    Example:
        dot-agent update --repo /path/to/project
        dot-agent update --all
    """
    if not repo and not update_all:
        _fail("Error: Must specify either --repo or --all")

    if repo and update_all:
        _fail("Error: Cannot specify both --repo and --all")

    repos_to_update: list[Path] = []

    if repo:
        if not repo.exists():
            _fail(f"Error: Repository does not exist: {repo}")
        if not repo.is_dir():
            _fail(f"Error: Repository is not a directory: {repo}")

        repos_to_update.append(repo)
    elif update_all:
        all_repos = find_all_repos()
        # Filter to only managed repos
        for repo_path in all_repos:
            metadata = get_repo_metadata(repo_path)
            if metadata and metadata.managed:
                repos_to_update.append(repo_path)

        if not repos_to_update:
            click.echo("No managed repositories found.")
            return

    # Update each repository
    updated_count = 0
    skipped_count = 0

    for repo_path in repos_to_update:
        metadata = get_repo_metadata(repo_path)
        if not metadata:
            click.echo(f"{repo_path}: No .agent/ folder found", err=True)
            continue

        if not metadata.managed:
            click.echo(f"{repo_path}: Not managed (skipping)", err=True)
            skipped_count += 1
            continue

        # Check if update is needed
        if not check_for_updates(repo_path):
            click.echo(f"{repo_path}: Already up to date")
            skipped_count += 1
            continue

        # Perform update
        update_repo(repo_path)
        click.echo(f"{repo_path}: Updated")
        updated_count += 1

    click.echo("")
    click.echo(f"Updated: {updated_count}")
    click.echo(f"Skipped: {skipped_count}")


@main.command()
def repos() -> None:
    """Show status of .agent folders across all repositories.

    Displays all repositories with .agent/ folders, showing installation
    date and whether updates are available.
    """
    all_repos = find_all_repos()

    if not all_repos:
        click.echo("No repositories with .agent/ folders found.")
        return

    click.echo("Repositories with .agent/ folders:")
    click.echo("")

    for repo_path in all_repos:
        metadata = get_repo_metadata(repo_path)

        # Get current branch if it's a git repo
        git_dir = repo_path / ".git"
        branch_info = ""
        if git_dir.exists():
            head_file = git_dir / "HEAD"
            if head_file.exists():
                head_content = head_file.read_text(encoding="utf-8").strip()
                if head_content.startswith("ref: refs/heads/"):
                    branch = head_content.replace("ref: refs/heads/", "")
                    branch_info = f" ({branch})"

        click.echo(f"{repo_path}{branch_info}")

        if metadata:
            if metadata.managed:
                if metadata.installed_at:
                    click.echo(
                        f"  Installed: {metadata.installed_at.strftime('%Y-%m-%d %H:%M:%S')}"
                    )

                if metadata.source_url:
                    click.echo(f"  Source: {metadata.source_url}")

                if check_for_updates(repo_path):
                    click.echo(click.style("  Status: Updates available", fg="yellow"))
                else:
                    click.echo(click.style("  Status: Up to date", fg="green"))
            else:
                click.echo(click.style("  Status: Not managed", dim=True))
        else:
            click.echo(click.style("  Status: No metadata", dim=True))

        click.echo("")


if __name__ == "__main__":
    main()
