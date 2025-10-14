"""Shared helper functions for Graphite-related tests."""

import json
from pathlib import Path


def setup_graphite_stack(
    git_dir: Path, branches: dict[str, dict[str, list[str] | str | bool | None]]
) -> None:
    """Set up a fake Graphite cache file with a stack structure.

    Args:
        git_dir: Path to .git directory
        branches: Dict mapping branch name to metadata with keys:
            - parent: parent branch name or None for trunk
            - children: list of child branch names
            - is_trunk: optional bool, defaults to False
    """
    cache_file = git_dir / ".graphite_cache_persist"
    cache_file.parent.mkdir(parents=True, exist_ok=True)

    branches_data = []
    for branch_name, metadata in branches.items():
        branch_data = {
            "children": metadata.get("children", []),
        }
        if metadata.get("parent") is not None:
            branch_data["parentBranchName"] = metadata["parent"]
        if metadata.get("is_trunk", False):
            branch_data["validationResult"] = "TRUNK"

        branches_data.append([branch_name, branch_data])

    cache_data = {"branches": branches_data}
    cache_file.write_text(json.dumps(cache_data), encoding="utf-8")
