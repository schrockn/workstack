#!/usr/bin/env python3
# /// script
# dependencies = [
#   "click>=8.1.7",
# ]
# requires-python = ">=3.13"
# ///
"""Create AGENTS.md symlinks for all CLAUDE.md files in the repository."""

# pyright: reportMissingImports=false

from pathlib import Path

import click


def is_git_repo_root(path: Path) -> bool:
    """Check if the given path is a git repository root.

    Args:
        path: Path to check

    Returns:
        True if path contains a .git directory
    """
    git_dir = path / ".git"
    return git_dir.exists() and git_dir.is_dir()


def create_symlink_for_claude_md(claude_md_path: Path, dry_run: bool = False) -> str:
    """Create AGENTS.md symlink for a CLAUDE.md file.

    Args:
        claude_md_path: Path to the CLAUDE.md file
        dry_run: If True, don't actually create the symlink

    Returns:
        Status string: 'created', 'skipped_exists', 'skipped_correct'
    """
    agents_md_path = claude_md_path.parent / "AGENTS.md"

    # Check if AGENTS.md already exists
    if agents_md_path.exists():
        # If it's a symlink pointing to CLAUDE.md, skip (already correct)
        if agents_md_path.is_symlink():
            if agents_md_path.readlink() == Path("CLAUDE.md"):
                return "skipped_correct"
        # If it's a regular file or symlink to something else, skip
        return "skipped_exists"

    # Create the symlink
    if not dry_run:
        agents_md_path.symlink_to("CLAUDE.md")

    return "created"


def create_agents_symlinks(
    repo_root: Path, dry_run: bool = False, verbose: bool = False
) -> tuple[int, int]:
    """Find CLAUDE.md files and create AGENTS.md symlinks.

    Args:
        repo_root: Path to the git repository root
        dry_run: If True, show what would be done without making changes
        verbose: If True, show detailed output for each operation

    Returns:
        Tuple of (created_count, skipped_count)
    """
    created_count = 0
    skipped_count = 0

    # Find all CLAUDE.md files recursively
    claude_md_files = list(repo_root.rglob("CLAUDE.md"))

    if verbose:
        plural = "s" if len(claude_md_files) != 1 else ""
        click.echo(f"Found {len(claude_md_files)} CLAUDE.md file{plural}")

    for claude_md_path in claude_md_files:
        status = create_symlink_for_claude_md(claude_md_path, dry_run)

        if status == "created":
            created_count += 1
            if verbose:
                rel_path = claude_md_path.relative_to(repo_root)
                action = "Would create" if dry_run else "Created"
                click.echo(f"  ✓ {action}: {rel_path.parent}/AGENTS.md")
        else:
            skipped_count += 1
            if verbose:
                rel_path = claude_md_path.relative_to(repo_root)
                click.echo(f"  ⊘ Skipped: {rel_path.parent}/AGENTS.md (already exists)")

    return created_count, skipped_count


@click.command()
@click.option("--dry-run", is_flag=True)
@click.option("--verbose", is_flag=True)
def main(dry_run: bool, verbose: bool) -> None:
    """Execute create-agents-symlinks command."""
    # Check if we're at the git repository root
    repo_root = Path.cwd()
    if not is_git_repo_root(repo_root):
        click.echo("Error: Must be run from git repository root", err=True)
        raise SystemExit(1)

    created_count, skipped_count = create_agents_symlinks(repo_root, dry_run, verbose)

    # Print summary
    if not verbose and (created_count > 0 or skipped_count > 0):
        if dry_run:
            if created_count > 0:
                plural = "s" if created_count != 1 else ""
                click.echo(f"Would create {created_count} AGENTS.md symlink{plural}")
            if skipped_count > 0:
                click.echo(f"Would skip {skipped_count} (already exists)")
        else:
            if created_count > 0:
                plural = "s" if created_count != 1 else ""
                click.echo(f"✓ Created {created_count} AGENTS.md symlink{plural}")
            if skipped_count > 0:
                click.echo(f"⊘ Skipped {skipped_count} (already exists)")
    elif created_count == 0 and skipped_count == 0:
        click.echo("No CLAUDE.md files found")


if __name__ == "__main__":
    main()
