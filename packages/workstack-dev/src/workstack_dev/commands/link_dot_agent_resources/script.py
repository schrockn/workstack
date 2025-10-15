#!/usr/bin/env python3
# /// script
# dependencies = [
#   "click>=8.1.7",
# ]
# requires-python = ">=3.13"
# ///
"""Manage symlinks between .agent/tools/ and dot-agent-kit package resources."""

# pyright: reportMissingImports=false

import os
from pathlib import Path

import click


def get_repo_root() -> Path:
    """Get repository root directory."""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent

    click.echo("Error: Not in a git repository", err=True)
    raise SystemExit(1)


def get_tool_files_mapping(repo_root: Path) -> dict[Path, Path]:
    """Get mapping of symlink path to target path for all tool files."""
    agent_tools_dir = repo_root / ".agent" / "tools"
    package_tools_dir = (
        repo_root / "packages" / "dot-agent-kit" / "src" / "dot_agent_kit" / "resources" / "tools"
    )

    if not agent_tools_dir.exists():
        click.echo(f"Error: {agent_tools_dir} not found", err=True)
        raise SystemExit(1)

    if not package_tools_dir.exists():
        click.echo("Error: Not in workstack monorepo (packages/dot-agent-kit/ not found)", err=True)
        raise SystemExit(1)

    # Map all .md files in package resources
    mapping = {}
    for target_path in package_tools_dir.glob("*.md"):
        symlink_path = agent_tools_dir / target_path.name
        mapping[symlink_path] = target_path

    return mapping


def get_symlink_status(symlink_path: Path, target_path: Path) -> str:
    """Determine status of a symlink.

    Returns:
        'symlink_valid' | 'symlink_broken' | 'regular_file' | 'missing'
    """
    if not symlink_path.exists() and not symlink_path.is_symlink():
        return "missing"

    if symlink_path.is_symlink():
        if symlink_path.exists():
            # Resolve symlink and check if it points to correct target
            resolved = symlink_path.resolve()
            if resolved == target_path.resolve():
                return "symlink_valid"
            return "symlink_broken"
        return "symlink_broken"

    if symlink_path.is_file():
        return "regular_file"

    return "missing"


def create_symlink(symlink_path: Path, target_path: Path, force: bool, dry_run: bool) -> None:
    """Create a symlink from symlink_path to target_path.

    Args:
        symlink_path: Path where symlink will be created
        target_path: Path that symlink will point to
        force: Skip content validation if regular file exists
        dry_run: Preview without executing
    """
    # Validate target exists
    if not target_path.exists():
        click.echo(f"Error: Target does not exist: {target_path}", err=True)
        raise SystemExit(1)

    # Check if symlink path already exists
    if symlink_path.exists() or symlink_path.is_symlink():
        status = get_symlink_status(symlink_path, target_path)

        if status == "symlink_valid":
            # Already a valid symlink
            return

        if status == "regular_file":
            # Check content matches
            local_content = symlink_path.read_text(encoding="utf-8")
            package_content = target_path.read_text(encoding="utf-8")

            if local_content != package_content and not force:
                click.echo(f"Error: {symlink_path.name} has local changes", err=True)
                click.echo("Use --force to overwrite or manually resolve", err=True)
                raise SystemExit(1)

            # Remove regular file
            if not dry_run:
                symlink_path.unlink()

        elif status == "symlink_broken":
            # Remove broken symlink
            if not dry_run:
                symlink_path.unlink()

    # Create relative symlink
    # Calculate relative path from symlink to target
    relative_target = os.path.relpath(target_path, symlink_path.parent)

    if dry_run:
        click.echo(f"Would create: {symlink_path.name} -> {relative_target}")
    else:
        symlink_path.symlink_to(relative_target)

        # Verify symlink works
        if not symlink_path.exists():
            click.echo(f"Error: Created symlink is broken: {symlink_path}", err=True)
            raise SystemExit(1)


def remove_symlink(symlink_path: Path, dry_run: bool) -> None:
    """Remove symlink and restore as regular file.

    Args:
        symlink_path: Path to symlink
        dry_run: Preview without executing
    """
    if not symlink_path.is_symlink():
        # Not a symlink, skip
        return

    if not symlink_path.exists():
        # Broken symlink
        if dry_run:
            click.echo(f"Would remove broken: {symlink_path.name}")
        else:
            symlink_path.unlink()
        return

    # Read content through symlink
    content = symlink_path.read_text(encoding="utf-8")

    if dry_run:
        click.echo(f"Would restore as regular file: {symlink_path.name}")
    else:
        # Remove symlink
        symlink_path.unlink()

        # Write content as regular file
        symlink_path.write_text(content, encoding="utf-8")

        # Verify it's a regular file
        if symlink_path.is_symlink():
            click.echo(f"Error: Failed to convert to regular file: {symlink_path}", err=True)
            raise SystemExit(1)


def verify_symlinks(mapping: dict[Path, Path]) -> list[str]:
    """Verify all symlinks are valid.

    Returns:
        List of issues (empty if all valid)
    """
    issues = []

    for symlink_path, target_path in mapping.items():
        status = get_symlink_status(symlink_path, target_path)

        if status == "missing":
            issues.append(f"{symlink_path.name}: missing")
        elif status == "regular_file":
            issues.append(f"{symlink_path.name}: regular file (not symlink)")
        elif status == "symlink_broken":
            issues.append(f"{symlink_path.name}: broken symlink")

    return issues


def show_status(mapping: dict[Path, Path], verbose: bool) -> None:
    """Display status for each file."""
    click.echo("Tool file status:\n")

    symlink_valid_count = 0
    symlink_broken_count = 0
    regular_file_count = 0
    missing_count = 0

    for symlink_path, target_path in sorted(mapping.items()):
        status = get_symlink_status(symlink_path, target_path)
        relative_name = symlink_path.relative_to(symlink_path.parents[1])

        if status == "symlink_valid":
            relative_target = os.path.relpath(target_path, symlink_path.parents[1])
            click.echo(f"  {relative_name} → symlink (valid) → {relative_target}")
            symlink_valid_count += 1
        elif status == "symlink_broken":
            click.echo(f"  {relative_name} → symlink (broken)")
            symlink_broken_count += 1
        elif status == "regular_file":
            click.echo(f"  {relative_name} → regular file")
            regular_file_count += 1
        elif status == "missing":
            click.echo(f"  {relative_name} → missing")
            missing_count += 1

    click.echo("\nSummary:")
    if symlink_valid_count > 0:
        click.echo(f"  {symlink_valid_count} valid symlinks")
    if symlink_broken_count > 0:
        click.echo(f"  {symlink_broken_count} broken symlinks")
    if regular_file_count > 0:
        click.echo(f"  {regular_file_count} regular files")
    if missing_count > 0:
        click.echo(f"  {missing_count} missing files")


@click.command()
@click.option("--create", is_flag=True)
@click.option("--remove", is_flag=True)
@click.option("--status", is_flag=True)
@click.option("--verify", is_flag=True)
@click.option("--dry-run", is_flag=True)
@click.option("--verbose", is_flag=True)
@click.option("--force", is_flag=True)
def main(
    create: bool,
    remove: bool,
    status: bool,
    verify: bool,
    dry_run: bool,
    verbose: bool,
    force: bool,
) -> None:
    """Execute symlink management."""
    repo_root = get_repo_root()
    mapping = get_tool_files_mapping(repo_root)

    # Determine mode (default to status if no mode specified)
    if not any([create, remove, status, verify]):
        status = True

    # Execute requested operation
    if create:
        if verbose or dry_run:
            click.echo("Creating symlinks...\n")

        for symlink_path, target_path in mapping.items():
            create_symlink(symlink_path, target_path, force, dry_run)

        if not dry_run:
            click.echo("\nSymlinks created successfully")

    elif remove:
        if verbose or dry_run:
            click.echo("Removing symlinks...\n")

        for symlink_path in mapping.keys():
            remove_symlink(symlink_path, dry_run)

        if not dry_run:
            click.echo("\nSymlinks removed successfully")

    elif verify:
        issues = verify_symlinks(mapping)

        if not issues:
            if verbose:
                click.echo("All symlinks are valid")
            raise SystemExit(0)

        click.echo("Symlink issues found:\n", err=True)
        for issue in issues:
            click.echo(f"  {issue}", err=True)
        raise SystemExit(1)

    elif status:
        show_status(mapping, verbose)


if __name__ == "__main__":
    main()
