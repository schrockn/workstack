#!/usr/bin/env python3
# /// script
# dependencies = [
#   "click>=8.1.7",
# ]
# requires-python = ">=3.13"
# ///
"""Publish workstack and devclikit packages to PyPI.

This script automates the synchronized publishing workflow for both packages.

RECOVERY FROM FAILURES:

1. Pre-build failure (git, version parsing, etc):
   - No changes made, safe to fix issue and retry

2. Build failure:
   - Version bumps made but not committed
   - Run: git checkout -- pyproject.toml packages/devclikit/pyproject.toml uv.lock
   - Fix build issue and retry

3. devclikit publish failure:
   - Version bumps made but not committed
   - Run: git checkout -- pyproject.toml packages/devclikit/pyproject.toml uv.lock
   - Investigate PyPI issue and retry

4. workstack publish failure (devclikit already published):
   - devclikit published to PyPI but workstack failed
   - DO NOT revert version bumps
   - Fix workstack issue and manually publish:
     * cd dist
     * uvx uv-publish workstack-<version>*
   - Then commit and push

5. Git commit/push failure (both packages published):
   - Both packages published successfully
   - Manually commit and push:
     * git add pyproject.toml packages/devclikit/pyproject.toml uv.lock
     * git commit -m "Published <version>"
     * git push
"""

import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

import click


@dataclass(frozen=True)
class PackageInfo:
    """Information about a publishable package."""

    name: str
    path: Path
    pyproject_path: Path


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


def discover_workspace_packages(repo_root: Path) -> list[PackageInfo]:
    """Discover all publishable packages in workspace.

    Returns:
        List of packages in dependency order (dependencies first)
    """
    packages = [
        PackageInfo(
            name="devclikit",
            path=repo_root / "packages" / "devclikit",
            pyproject_path=repo_root / "packages" / "devclikit" / "pyproject.toml",
        ),
        PackageInfo(
            name="workstack",
            path=repo_root,
            pyproject_path=repo_root / "pyproject.toml",
        ),
    ]

    # Validate all packages exist
    for pkg in packages:
        if not pkg.pyproject_path.exists():
            click.echo(f"✗ Package not found: {pkg.name} at {pkg.path}", err=True)
            raise SystemExit(1)

    return packages


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
        click.echo(f"[DRY RUN] Would update {pyproject_path.name}: {old_line} -> {new_line}")
        return

    updated_content = content.replace(old_line, new_line)
    pyproject_path.write_text(updated_content, encoding="utf-8")


def validate_version_consistency(packages: list[PackageInfo]) -> str:
    """Ensure all packages have the same version.

    Returns:
        The current version if consistent

    Raises:
        SystemExit: If versions are inconsistent
    """
    versions = {}
    for pkg in packages:
        version = get_current_version(pkg.pyproject_path)
        versions[pkg.name] = version

    unique_versions = set(versions.values())
    if len(unique_versions) > 1:
        click.echo("✗ Version mismatch across packages:", err=True)
        for name, version in versions.items():
            click.echo(f"  {name}: {version}", err=True)
        raise SystemExit(1)

    return list(unique_versions)[0]


def synchronize_versions(
    packages: list[PackageInfo],
    old_version: str,
    new_version: str,
    dry_run: bool,
) -> None:
    """Update version in all package pyproject.toml files.

    Args:
        packages: List of packages to update
        old_version: Current version to replace
        new_version: New version to write
        dry_run: If True, skip actual file writes
    """
    for pkg in packages:
        update_version(pkg.pyproject_path, old_version, new_version, dry_run)
        if not dry_run:
            click.echo(f"  ✓ Updated {pkg.name}: {old_version} → {new_version}")


def run_uv_sync(repo_root: Path, dry_run: bool) -> None:
    """Update lockfile with uv sync."""
    if dry_run:
        click.echo("[DRY RUN] Would run: uv sync")
        return
    run_command(["uv", "sync"], cwd=repo_root, description="uv sync")
    click.echo("✓ Dependencies synced")


def build_package(package: PackageInfo, out_dir: Path, dry_run: bool) -> None:
    """Build a specific package in the workspace.

    Args:
        package: Package to build
        out_dir: Output directory for artifacts
        dry_run: If True, skip actual build
    """
    if dry_run:
        click.echo(f"[DRY RUN] Would run: uv build --package {package.name} -o {out_dir}")
        return

    # For devclikit, run from repo root; for workstack, also from repo root
    run_command(
        ["uv", "build", "--package", package.name, "-o", str(out_dir)],
        cwd=package.path if package.name == "workstack" else package.path.parent.parent,
        description=f"build {package.name}",
    )


def build_all_packages(
    packages: list[PackageInfo],
    repo_root: Path,
    dry_run: bool,
) -> Path:
    """Build all packages to a staging directory.

    Returns:
        Path to staging directory containing all artifacts
    """
    # Create staging directory
    staging_dir = repo_root / "dist"
    if staging_dir.exists() and not dry_run:
        # Clean existing artifacts
        for artifact in staging_dir.glob("*"):
            artifact.unlink()
    elif not dry_run:
        staging_dir.mkdir(parents=True, exist_ok=True)

    click.echo("\nBuilding packages...")
    for pkg in packages:
        build_package(pkg, staging_dir, dry_run)
        click.echo(f"  ✓ Built {pkg.name}")

    return staging_dir


def validate_build_artifacts(
    packages: list[PackageInfo],
    staging_dir: Path,
    version: str,
    dry_run: bool,
) -> None:
    """Verify all expected artifacts exist.

    Args:
        packages: List of packages that were built
        staging_dir: Directory containing artifacts
        version: Version number to check
        dry_run: If True, skip validation
    """
    if dry_run:
        click.echo("[DRY RUN] Would validate artifacts exist")
        return

    for pkg in packages:
        wheel = staging_dir / f"{pkg.name}-{version}-py3-none-any.whl"
        sdist = staging_dir / f"{pkg.name}-{version}.tar.gz"

        if not wheel.exists():
            click.echo(f"✗ Missing wheel: {wheel}", err=True)
            raise SystemExit(1)
        if not sdist.exists():
            click.echo(f"✗ Missing sdist: {sdist}", err=True)
            raise SystemExit(1)

    click.echo("  ✓ All artifacts validated")


def publish_package(package: PackageInfo, staging_dir: Path, version: str, dry_run: bool) -> None:
    """Publish a single package to PyPI.

    Args:
        package: Package to publish
        staging_dir: Directory containing built artifacts
        version: Version being published
        dry_run: If True, skip actual publish
    """
    if dry_run:
        click.echo(f"[DRY RUN] Would publish {package.name} to PyPI")
        return

    # Filter to only this package's artifacts
    artifacts = list(staging_dir.glob(f"{package.name}-{version}*"))

    if not artifacts:
        click.echo(f"✗ No artifacts found for {package.name} {version}", err=True)
        raise SystemExit(1)

    # Publish using uv-publish with specific files
    run_command(
        ["uvx", "uv-publish"] + [str(a) for a in artifacts],
        cwd=staging_dir,
        description=f"publish {package.name}",
    )


def wait_for_pypi_availability(package: PackageInfo, version: str, dry_run: bool) -> None:
    """Wait for package to be available on PyPI.

    Args:
        package: Package to check
        version: Version to wait for
        dry_run: If True, skip wait
    """
    if dry_run:
        click.echo(f"[DRY RUN] Would wait for {package.name} {version} on PyPI")
        return

    wait_seconds = 5
    click.echo(f"  ⏳ Waiting {wait_seconds}s for PyPI propagation...")
    time.sleep(wait_seconds)


def publish_all_packages(
    packages: list[PackageInfo],
    staging_dir: Path,
    version: str,
    dry_run: bool,
) -> None:
    """Publish all packages in dependency order.

    Packages are already sorted in dependency order (devclikit first).
    """
    click.echo("\nPublishing to PyPI...")

    for i, pkg in enumerate(packages):
        publish_package(pkg, staging_dir, version, dry_run)
        click.echo(f"  ✓ Published {pkg.name} {version}")

        # Wait after publishing dependencies (all but last)
        if i < len(packages) - 1:
            wait_for_pypi_availability(pkg, version, dry_run)


def commit_changes(
    repo_root: Path,
    packages: list[PackageInfo],
    version: str,
    dry_run: bool,
) -> str:
    """Commit version bump changes for all packages.

    Args:
        repo_root: Repository root directory
        packages: List of packages that were updated
        version: New version number
        dry_run: If True, print commands instead of executing

    Returns:
        Commit SHA (or fake SHA in dry-run mode)
    """
    commit_message = f"""Published workstack and devclikit {version}

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"""

    if dry_run:
        files_to_add = [str(pkg.pyproject_path.relative_to(repo_root)) for pkg in packages]
        files_to_add.append("uv.lock")
        click.echo(f"[DRY RUN] Would run: git add {' '.join(files_to_add)}")
        click.echo(f'[DRY RUN] Would run: git commit -m "Published {version}..."')
        return "abc123f"

    # Add all pyproject.toml files and lockfile
    files_to_add = [str(pkg.pyproject_path.relative_to(repo_root)) for pkg in packages]
    files_to_add.append("uv.lock")

    run_command(
        ["git", "add"] + files_to_add,
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
    """Execute the synchronized multi-package publishing workflow."""
    if dry_run:
        click.echo("[DRY RUN MODE - No changes will be made]\n")

    # Step 0: Setup
    repo_root = Path.cwd()
    if not (repo_root / "pyproject.toml").exists():
        click.echo("✗ Not in repository root (pyproject.toml not found)", err=True)
        click.echo("  Run this command from the repository root directory", err=True)
        raise SystemExit(1)

    # Step 1: Discover packages
    click.echo("Discovering workspace packages...")
    packages = discover_workspace_packages(repo_root)
    click.echo(f"  ✓ Found {len(packages)} packages: {', '.join(p.name for p in packages)}")

    # Step 2: Check git status
    status = get_git_status(repo_root)
    if status:
        # Filter out version files that will be updated
        excluded_files = {
            "pyproject.toml",
            "uv.lock",
            "packages/devclikit/pyproject.toml",
        }
        lines = filter_git_status(status, excluded_files)

        if lines:
            click.echo("✗ Working directory has uncommitted changes:", err=True)
            for line in lines:
                click.echo(f"  {line}", err=True)
            raise SystemExit(1)

    click.echo("\nStarting synchronized publish workflow...\n")

    # Step 3: Pull latest changes
    run_git_pull(repo_root, dry_run)

    # Step 4: Validate version consistency
    old_version = validate_version_consistency(packages)
    click.echo(f"  ✓ Current version: {old_version} (consistent)")

    # Step 5: Bump versions
    new_version = bump_patch_version(old_version)
    click.echo(f"\nBumping version: {old_version} → {new_version}")
    synchronize_versions(packages, old_version, new_version, dry_run)

    # Step 6: Update lockfile
    run_uv_sync(repo_root, dry_run)

    # Step 7: Build all packages
    staging_dir = build_all_packages(packages, repo_root, dry_run)
    validate_build_artifacts(packages, staging_dir, new_version, dry_run)

    # Step 8: Publish all packages
    publish_all_packages(packages, staging_dir, new_version, dry_run)

    # Step 9: Commit changes
    sha = commit_changes(repo_root, packages, new_version, dry_run)
    click.echo(f'\n✓ Committed: {sha} "Published {new_version}"')

    # Step 10: Push to remote
    push_to_remote(repo_root, dry_run)
    click.echo("✓ Pushed to origin")

    # Success summary
    click.echo("\n✅ Successfully published:")
    for pkg in packages:
        click.echo(f"  • {pkg.name} {new_version}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        click.echo("\n✗ Interrupted by user", err=True)
        raise SystemExit(130) from None
