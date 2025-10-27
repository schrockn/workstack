"""Sync kit artifacts from .claude/ to kit package directories."""

import shutil
from pathlib import Path

import click

# Repository root is the current working directory (where make is run)
REPO_ROOT = Path.cwd()
CLAUDE_DIR = REPO_ROOT / ".claude"
PACKAGES_DIR = REPO_ROOT / "packages"

# Kit definitions: maps kit name to (source_pattern, dest_dir, file_list)
KIT_CONFIGS = {
    "dev-runners-da-kit": {
        "source_dir": CLAUDE_DIR / "agents",
        "dest_dir": PACKAGES_DIR / "dev-runners-da-kit" / "agents",
        "files": [
            "pytest-runner.md",
            "ruff-runner.md",
            "pyright-runner.md",
            "prettier-runner.md",
        ],
    },
}


def sync_file(source: Path, dest: Path, dry_run: bool, verbose: bool) -> bool:
    """Sync a single file from source to destination."""
    if not source.exists():
        click.echo(f"  ✗ Source not found: {source.relative_to(REPO_ROOT)}", err=True)
        return False

    if dry_run:
        if verbose:
            click.echo(f"  Would copy: {source.name}")
        return True

    # Ensure destination directory exists
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Copy file
    shutil.copy2(source, dest)
    if verbose:
        click.echo(f"  ✓ Synced: {source.name}")
    return True


@click.command(name="sync-kit")
@click.argument("kit_name", required=False)
@click.option("--dry-run", is_flag=True, help="Show what would be synced")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
def sync_kit_command(kit_name: str | None, dry_run: bool, verbose: bool) -> None:
    """Sync kit artifacts from .claude/ to kit packages.

    If KIT_NAME is not provided, syncs all configured kits.
    Available kits: dev-runners-da-kit
    """
    # Determine which kits to sync
    if kit_name:
        if kit_name not in KIT_CONFIGS:
            click.echo(f"Error: Unknown kit '{kit_name}'", err=True)
            click.echo(f"Available kits: {', '.join(KIT_CONFIGS.keys())}")
            raise SystemExit(1)
        kits_to_sync = {kit_name: KIT_CONFIGS[kit_name]}
    else:
        kits_to_sync = KIT_CONFIGS

    # Sync each kit
    for name, config in kits_to_sync.items():
        click.echo(f"Syncing {name}...")

        source_dir = config["source_dir"]
        dest_dir = config["dest_dir"]
        files = config["files"]

        synced_count = 0
        for filename in files:
            source = source_dir / filename
            dest = dest_dir / filename
            if sync_file(source, dest, dry_run, verbose):
                synced_count += 1

        if synced_count > 0:
            action = "Would sync" if dry_run else "Synced"
            plural = "" if synced_count == 1 else "s"
            click.echo(f"  {action} {synced_count} file{plural}")
        else:
            click.echo("  No files synced")
