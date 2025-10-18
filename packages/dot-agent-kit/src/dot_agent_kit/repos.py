"""Repository operations for .agent/ folder management."""

import shutil
from datetime import UTC, datetime
from pathlib import Path

from dot_agent_kit.repo_metadata import (
    calculate_folder_hash,
    get_repo_metadata,
    write_repo_metadata,
)


def install_to_repo(source_path: Path, target_repo: Path) -> None:
    """Install .agent/ folder into target repository.

    Copies the source .agent/ folder to the target repository and adds
    management metadata to track installation.

    Raises:
        ValueError: If source is not a .agent directory or target already has .agent/
    """
    # Validate source is .agent directory
    if not source_path.exists():
        raise ValueError(f"Source path does not exist: {source_path}")

    if not source_path.is_dir():
        raise ValueError(f"Source path is not a directory: {source_path}")

    if source_path.name != ".agent":
        raise ValueError(f"Source must be a .agent directory: {source_path}")

    # Validate target is a directory
    if not target_repo.exists():
        raise ValueError(f"Target repository does not exist: {target_repo}")

    if not target_repo.is_dir():
        raise ValueError(f"Target repository is not a directory: {target_repo}")

    # Check if target already has .agent/
    target_agent_dir = target_repo / ".agent"
    if target_agent_dir.exists():
        raise ValueError(f"Target already has .agent/ directory: {target_agent_dir}")

    # Copy .agent/ folder
    shutil.copytree(source_path, target_agent_dir)

    # Calculate hash of installed content
    installed_hash = calculate_folder_hash(target_agent_dir)

    # Create metadata
    metadata = {
        "managed": True,
        "installed_at": datetime.now(UTC).isoformat(),
        "original_hash": installed_hash,
        "current_hash": installed_hash,
        "source_url": str(source_path.resolve()),
    }

    # Write metadata to README.md frontmatter
    write_repo_metadata(target_repo, metadata)


def update_repo(repo_path: Path) -> bool:
    """Update existing .agent/ folder with latest version from source.

    Returns True if update was performed, False if no update needed or not managed.

    Raises:
        ValueError: If repo has no .agent/ folder or is not managed
    """
    # Get current metadata
    metadata_obj = get_repo_metadata(repo_path)
    if metadata_obj is None:
        raise ValueError(f"Repository has no .agent/ folder: {repo_path}")

    if not metadata_obj.managed:
        raise ValueError(f"Repository .agent/ folder is not managed: {repo_path}")

    if metadata_obj.source_url is None:
        raise ValueError(f"Repository has no source_url in metadata: {repo_path}")

    # Check if source still exists
    source_path = Path(metadata_obj.source_url)
    if not source_path.exists():
        raise ValueError(f"Source path no longer exists: {source_path}")

    if not source_path.is_dir():
        raise ValueError(f"Source path is not a directory: {source_path}")

    # Calculate source hash
    source_hash = calculate_folder_hash(source_path)

    # Check if update is needed
    if metadata_obj.current_hash == source_hash:
        return False

    # Backup and remove existing .agent/ folder (except README.md)
    agent_dir = repo_path / ".agent"
    readme_path = agent_dir / "README.md"

    # Save README.md content
    if readme_path.exists():
        readme_path.read_text(encoding="utf-8")

    # Remove all files except README.md
    for item in agent_dir.iterdir():
        if item.name != "README.md":
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

    # Copy new content from source (except README.md)
    for item in source_path.iterdir():
        if item.name != "README.md":
            target = agent_dir / item.name
            if item.is_dir():
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)

    # Update metadata with new hash
    new_hash = calculate_folder_hash(agent_dir)
    metadata = {
        "managed": True,
        "installed_at": metadata_obj.installed_at.isoformat()
        if metadata_obj.installed_at
        else None,
        "original_hash": metadata_obj.original_hash,
        "current_hash": new_hash,
        "source_url": str(source_path.resolve()),
    }

    # Write updated metadata
    write_repo_metadata(repo_path, metadata)

    return True


def check_for_updates(repo_path: Path) -> bool:
    """Check if .agent folder needs updating.

    Returns True if updates are available, False otherwise.
    """
    metadata = get_repo_metadata(repo_path)
    if metadata is None:
        return False

    if not metadata.managed:
        return False

    if metadata.source_url is None:
        return False

    source_path = Path(metadata.source_url)
    if not source_path.exists():
        return False

    if not source_path.is_dir():
        return False

    source_hash = calculate_folder_hash(source_path)
    return metadata.current_hash != source_hash


def find_all_repos(start_path: Path | None = None) -> list[Path]:
    """Find all repositories with .agent/ folders.

    Searches from start_path (default: cwd) for all directories containing .agent/ folders.
    Searches up to 3 levels deep to find repos while avoiding excessive scanning.

    Returns list of repository paths (directories containing .agent/).
    """
    if start_path is None:
        start_path = Path.cwd()

    repos: list[Path] = []

    # Check if start_path itself has .agent/
    agent_dir = start_path / ".agent"
    if agent_dir.exists() and agent_dir.is_dir():
        repos.append(start_path)

    # Search subdirectories up to 3 levels deep
    # This handles: ./repo, ./dir/repo, ./dir/subdir/repo
    try:
        for agent_dir in start_path.glob(".agent"):
            if agent_dir.is_dir():
                repo_path = agent_dir.parent
                if repo_path not in repos:
                    repos.append(repo_path)

        for agent_dir in start_path.glob("*/.agent"):
            if agent_dir.is_dir():
                repo_path = agent_dir.parent
                if repo_path not in repos:
                    repos.append(repo_path)

        for agent_dir in start_path.glob("*/*/.agent"):
            if agent_dir.is_dir():
                repo_path = agent_dir.parent
                if repo_path not in repos:
                    repos.append(repo_path)

        for agent_dir in start_path.glob("*/*/*/.agent"):
            if agent_dir.is_dir():
                repo_path = agent_dir.parent
                if repo_path not in repos:
                    repos.append(repo_path)
    except PermissionError:
        # Skip directories we can't access
        pass

    return sorted(repos)
