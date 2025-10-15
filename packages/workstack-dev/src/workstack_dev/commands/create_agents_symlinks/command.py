"""Create AGENTS.md symlinks command."""

from pathlib import Path

import click


def is_git_repo_root(path: Path) -> bool:
    """Return True when the path looks like a git repository root."""
    git_dir = path / ".git"
    return git_dir.exists() and git_dir.is_dir()


def create_symlink_for_claude_md(claude_md_path: Path, dry_run: bool) -> str:
    """Create AGENTS.md symlink for the provided CLAUDE.md file."""
    agents_md_path = claude_md_path.parent / "AGENTS.md"

    if agents_md_path.exists():
        if agents_md_path.is_symlink():
            # Keep symlinks that already point at CLAUDE.md.
            if agents_md_path.readlink() == Path("CLAUDE.md"):
                return "skipped_correct"
        return "skipped_exists"

    if not dry_run:
        agents_md_path.symlink_to("CLAUDE.md")

    return "created"


def create_agents_symlinks(repo_root: Path, dry_run: bool, verbose: bool) -> tuple[int, int]:
    """Create missing AGENTS.md symlinks underneath the repository root."""
    created_count = 0
    skipped_count = 0

    claude_md_files = list(repo_root.rglob("CLAUDE.md"))

    if verbose:
        plural = "s" if len(claude_md_files) != 1 else ""
        click.echo(f"Found {len(claude_md_files)} CLAUDE.md file{plural}")

    for claude_md_path in claude_md_files:
        status = create_symlink_for_claude_md(claude_md_path, dry_run)

        rel_path = claude_md_path.relative_to(repo_root)
        if status == "created":
            created_count += 1
            if verbose:
                action = "Would create" if dry_run else "Created"
                click.echo(f"  ✓ {action}: {rel_path.parent}/AGENTS.md")
        else:
            skipped_count += 1
            if verbose:
                click.echo(f"  ⊘ Skipped: {rel_path.parent}/AGENTS.md (already exists)")

    return created_count, skipped_count


@click.command(name="create-agents-symlinks")
@click.option("--dry-run", is_flag=True, help="Show what would be done without making changes")
@click.option("--verbose", is_flag=True, help="Show detailed output")
def command(dry_run: bool, verbose: bool) -> None:
    """Create AGENTS.md symlinks for all CLAUDE.md files in the repository."""
    repo_root = Path.cwd()
    if not is_git_repo_root(repo_root):
        click.echo("Error: Must be run from git repository root", err=True)
        raise SystemExit(1)

    created_count, skipped_count = create_agents_symlinks(repo_root, dry_run, verbose)

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
