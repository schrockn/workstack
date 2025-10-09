#!/usr/bin/env python3
"""Publish workstack package to PyPI.

This script automates the full publishing workflow:
1. Pull latest changes from remote
2. Bump version in pyproject.toml
3. Update lockfile with uv sync
4. Build and publish to PyPI
5. Commit and push changes
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path


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
        print(f"✗ Failed: {description}", file=sys.stderr)
        print(f"  Command: {' '.join(cmd)}", file=sys.stderr)
        print(f"  Error: {e.stderr}", file=sys.stderr)
        sys.exit(1)


def run_git_pull(repo_root: Path, dry_run: bool) -> None:
    """Pull latest changes from remote."""
    if dry_run:
        print("[DRY RUN] Would run: git pull")
        return
    run_command(["git", "pull"], cwd=repo_root, description="git pull")
    print("✓ Pulled latest changes")


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
        print(f"✗ pyproject.toml not found at {pyproject_path}", file=sys.stderr)
        sys.exit(1)

    content = pyproject_path.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)

    if not match:
        print("✗ Could not find version in pyproject.toml", file=sys.stderr)
        sys.exit(1)

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
        print(f"✗ Invalid version format: {version}", file=sys.stderr)
        sys.exit(1)

    try:
        parts[2] = str(int(parts[2]) + 1)
    except ValueError:
        print(f"✗ Invalid patch version: {parts[2]}", file=sys.stderr)
        sys.exit(1)

    return ".".join(parts)


def update_version(
    pyproject_path: Path, old_version: str, new_version: str, dry_run: bool
) -> None:
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
        print(f"✗ Could not find version line in pyproject.toml: {old_line}", file=sys.stderr)
        sys.exit(1)

    if dry_run:
        print(f"[DRY RUN] Would update pyproject.toml: {old_line} -> {new_line}")
        return

    updated_content = content.replace(old_line, new_line)
    pyproject_path.write_text(updated_content, encoding="utf-8")


def run_uv_sync(repo_root: Path, dry_run: bool) -> None:
    """Update lockfile with uv sync."""
    if dry_run:
        print("[DRY RUN] Would run: uv sync")
        return
    run_command(["uv", "sync"], cwd=repo_root, description="uv sync")
    print("✓ Dependencies synced")


def run_make_publish(repo_root: Path, dry_run: bool) -> None:
    """Build and publish to PyPI using make publish."""
    if dry_run:
        print("[DRY RUN] Would run: make publish")
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
        print("[DRY RUN] Would run: git add pyproject.toml uv.lock")
        print(f'[DRY RUN] Would run: git commit -m "Published {version}..."')
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
        print("[DRY RUN] Would run: git push")
        return
    run_command(["git", "push"], cwd=repo_root, description="git push")


def get_git_status(repo_root: Path) -> str:
    """Get current git status."""
    return run_command(
        ["git", "status", "--porcelain"],
        cwd=repo_root,
        description="git status",
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Publish workstack package to PyPI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script automates the full publishing workflow:
  1. Pull latest changes from remote
  2. Bump version in pyproject.toml
  3. Update lockfile with uv sync
  4. Build and publish to PyPI
  5. Commit and push changes
        """,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making any changes",
    )
    return parser.parse_args()


def main() -> None:
    """Execute the full publishing workflow."""
    args = parse_args()
    dry_run = args.dry_run

    if dry_run:
        print("[DRY RUN MODE - No changes will be made]\n")

    # Determine repository root (script should be run from repo root)
    repo_root = Path.cwd()
    pyproject_path = repo_root / "pyproject.toml"

    if not pyproject_path.exists():
        print("✗ Not in repository root (pyproject.toml not found)", file=sys.stderr)
        print("  Run this script from the repository root directory", file=sys.stderr)
        sys.exit(1)

    # Check git status is clean (except pyproject.toml and uv.lock)
    status = get_git_status(repo_root)
    if status:
        # Filter out pyproject.toml and uv.lock changes
        excluded_files = ("pyproject.toml", "uv.lock")
        lines = [line for line in status.splitlines() if not line.endswith(excluded_files)]
        if lines:
            print("✗ Working directory has uncommitted changes:", file=sys.stderr)
            for line in lines:
                print(f"  {line}", file=sys.stderr)
            sys.exit(1)

    print("Starting publish workflow...\n")

    # Step 1: Pull latest changes
    run_git_pull(repo_root, dry_run)

    # Step 2: Bump version
    old_version = get_current_version(pyproject_path)
    new_version = bump_patch_version(old_version)
    update_version(pyproject_path, old_version, new_version, dry_run)
    print(f"✓ Version bumped: {old_version} → {new_version}")

    # Step 3: Update lockfile
    run_uv_sync(repo_root, dry_run)

    # Step 4: Publish to PyPI
    run_make_publish(repo_root, dry_run)
    print(f"✓ Published to PyPI: workstack-{new_version}")

    # Step 5: Commit changes
    sha = commit_changes(repo_root, new_version, dry_run)
    print(f'✓ Committed: {sha} "Published {new_version}"')

    # Step 6: Push to remote
    push_to_remote(repo_root, dry_run)
    print("✓ Pushed to origin/main")

    print(f"\n✅ Successfully published workstack {new_version}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n✗ Interrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)
