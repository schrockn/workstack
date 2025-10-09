#!/usr/bin/env python3
# /// script
# dependencies = [
#   "click>=8.1.7",
# ]
# requires-python = ">=3.13"
# ///
"""Publish workstack package to PyPI.

This script automates the full publishing workflow:
1. Pull latest changes from remote
2. Bump version in pyproject.toml
3. Update lockfile with uv sync
4. Build and publish to PyPI
5. Commit and push changes
"""

import re
import subprocess
from pathlib import Path

import click


def run_command(cmd: list[str], cwd: Path | None = None, description: str = "") -> str:
    """Run a command and return stdout.

    Args:
        cmd: Command to run as list of strings
        cwd: Working directory (defaults to current directory)
        description: Human-readable description for error messages

    Returns:
        stdout from the command

    Raises:
        SystemExit: If command fails
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        # Error boundary: CLI level
        click.echo(f"✗ Failed: {description}", err=True)
        click.echo(f"  Command: {' '.join(cmd)}", err=True)
        click.echo(f"  Error: {e.stderr}", err=True)
        raise SystemExit(1) from e


def run_git_pull(repo_root: Path, dry_run: bool) -> None:
    """Pull latest changes from remote."""
    if dry_run:
        click.echo("[DRY RUN] Would run: git pull")
        return
    run_command(["git", "pull"], cwd=repo_root, description="git pull")
    click.echo("✓ Pulled latest changes")


def get_current_version(pyproject_path: Path) -> str:
    """Parse current version from pyproject.toml.

    Args:
        pyproject_path: Path to pyproject.toml

    Returns:
        Current version string (e.g., "0.1.8")

    Raises:
        SystemExit: If version not found
    """
    if not pyproject_path.exists():
        click.echo(f"✗ pyproject.toml not found at {pyproject_path}", err=True)
        raise SystemExit(1)

    content = pyproject_path.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)

    if not match:
        click.echo("✗ Could not find version in pyproject.toml", err=True)
        raise SystemExit(1)

    return match.group(1)


def bump_patch_version(version: str) -> str:
    """Increment the patch version number.

    Args:
        version: Current version (e.g., "0.1.8")

    Returns:
        New version with incremented patch (e.g., "0.1.9")

    Raises:
        SystemExit: If version format is invalid
    """
    parts = version.split(".")
    if len(parts) != 3:
        click.echo(f"✗ Invalid version format: {version}", err=True)
        raise SystemExit(1)

    if not parts[2].isdigit():
        click.echo(f"✗ Invalid patch version: {parts[2]}", err=True)
        raise SystemExit(1)

    parts[2] = str(int(parts[2]) + 1)
    return ".".join(parts)


def update_version(pyproject_path: Path, old_version: str, new_version: str, dry_run: bool) -> None:
    """Update version in pyproject.toml.

    Args:
        pyproject_path: Path to pyproject.toml
        old_version: Current version to replace
        new_version: New version to write
        dry_run: If True, skip actual file write
    """
    content = pyproject_path.read_text(encoding="utf-8")
    old_line = f'version = "{old_version}"'
    new_line = f'version = "{new_version}"'

    if old_line not in content:
        click.echo(f"✗ Could not find version line in pyproject.toml: {old_line}", err=True)
        raise SystemExit(1)

    if dry_run:
        click.echo(f"[DRY RUN] Would update pyproject.toml: {old_line} -> {new_line}")
        return

    updated_content = content.replace(old_line, new_line)
    pyproject_path.write_text(updated_content, encoding="utf-8")


def run_uv_sync(repo_root: Path, dry_run: bool) -> None:
    """Update lockfile with uv sync."""
    if dry_run:
        click.echo("[DRY RUN] Would run: uv sync")
        return
    run_command(["uv", "sync"], cwd=repo_root, description="uv sync")
    click.echo("✓ Dependencies synced")


def run_make_publish(repo_root: Path, dry_run: bool) -> None:
    """Build and publish to PyPI using make publish."""
    if dry_run:
        click.echo("[DRY RUN] Would run: make publish")
        return
    run_command(["make", "publish"], cwd=repo_root, description="make publish")


def commit_changes(repo_root: Path, version: str, dry_run: bool) -> str:
    """Commit version bump changes.

    Args:
        repo_root: Repository root directory
        version: New version number
        dry_run: If True, print commands instead of executing

    Returns:
        Commit SHA (or fake SHA in dry-run mode)
    """
    commit_message = f"""Published {version}

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"""

    if dry_run:
        click.echo("[DRY RUN] Would run: git add pyproject.toml uv.lock")
        click.echo(f'[DRY RUN] Would run: git commit -m "Published {version}..."')
        return "abc123f"

    # Add modified files
    run_command(
        ["git", "add", "pyproject.toml", "uv.lock"],
        cwd=repo_root,
        description="git add",
    )

    # Commit changes
    run_command(
        ["git", "commit", "-m", commit_message],
        cwd=repo_root,
        description="git commit",
    )

    # Get commit SHA
    sha = run_command(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=repo_root,
        description="get commit SHA",
    )

    return sha


def push_to_remote(repo_root: Path, dry_run: bool) -> None:
    """Push commits to remote repository."""
    if dry_run:
        click.echo("[DRY RUN] Would run: git push")
        return
    run_command(["git", "push"], cwd=repo_root, description="git push")


def get_git_status(repo_root: Path) -> str:
    """Get current git status."""
    return run_command(
        ["git", "status", "--porcelain"],
        cwd=repo_root,
        description="git status",
    )


def filter_git_status(status: str, excluded_files: set[str]) -> list[str]:
    """Filter git status output to exclude specific files.

    Args:
        status: Git status output in porcelain format
        excluded_files: Set of filenames to exclude

    Returns:
        List of status lines that don't match excluded files

    Git porcelain format: "XY filename" where:
    - X and Y are single-character status codes
    - Space separator at position 2
    - Filename starts at position 3

    This correctly handles filenames with spaces.
    """
    lines = []
    for line in status.splitlines():
        # Parse by position: chars 0-1 are status, char 2 is space, 3+ is filename
        if len(line) >= 4:  # Minimum: "XY f"
            filename = line[3:]  # Skip status codes and space
            if filename not in excluded_files:
                lines.append(line)
    return lines


@click.command()
@click.option("--dry-run", is_flag=True, help="Show what would be done without making changes")
def main(dry_run: bool) -> None:
    """Execute the full publishing workflow."""
    if dry_run:
        click.echo("[DRY RUN MODE - No changes will be made]\n")

    # Determine repository root (script should be run from repo root)
    repo_root = Path.cwd()
    pyproject_path = repo_root / "pyproject.toml"

    if not pyproject_path.exists():
        click.echo("✗ Not in repository root (pyproject.toml not found)", err=True)
        click.echo("  Run this command from the repository root directory", err=True)
        raise SystemExit(1)

    # Check git status is clean (except pyproject.toml and uv.lock)
    status = get_git_status(repo_root)
    if status:
        # Filter out pyproject.toml and uv.lock changes
        excluded_files = {"pyproject.toml", "uv.lock"}
        lines = filter_git_status(status, excluded_files)

        if lines:
            click.echo("✗ Working directory has uncommitted changes:", err=True)
            for line in lines:
                click.echo(f"  {line}", err=True)
            raise SystemExit(1)

    click.echo("Starting publish workflow...\n")

    # Step 1: Pull latest changes
    run_git_pull(repo_root, dry_run)

    # Step 2: Bump version
    old_version = get_current_version(pyproject_path)
    new_version = bump_patch_version(old_version)
    update_version(pyproject_path, old_version, new_version, dry_run)
    click.echo(f"✓ Version bumped: {old_version} → {new_version}")

    # Step 3: Update lockfile
    run_uv_sync(repo_root, dry_run)

    # Step 4: Publish to PyPI
    run_make_publish(repo_root, dry_run)
    click.echo(f"✓ Published to PyPI: workstack-{new_version}")

    # Step 5: Commit changes
    sha = commit_changes(repo_root, new_version, dry_run)
    click.echo(f'✓ Committed: {sha} "Published {new_version}"')

    # Step 6: Push to remote
    push_to_remote(repo_root, dry_run)
    click.echo("✓ Pushed to origin/main")

    click.echo(f"\n✅ Successfully published workstack {new_version}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        click.echo("\n✗ Interrupted by user", err=True)
        raise SystemExit(130) from None
