import json
import subprocess
from pathlib import Path
from typing import TypedDict


class BranchInfo(TypedDict):
    parent: str | None
    children: list[str]
    is_trunk: bool


def get_branch_stack(repo_root: Path, branch: str) -> list[str] | None:
    """Get the graphite stack for a given branch.

    Returns a list of branch names from top to bottom in the stack,
    or None if graphite is not configured or the cache file is missing.

    For worktrees, this automatically finds the shared .git directory.
    """
    # Get the common git directory (handles both main repo and worktrees)
    result = subprocess.run(
        ["git", "rev-parse", "--git-common-dir"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None

    git_dir = Path(result.stdout.strip())
    if not git_dir.is_absolute():
        git_dir = repo_root / git_dir

    cache_file = git_dir / ".graphite_cache_persist"
    if not cache_file.exists():
        return None

    # Parse the graphite cache
    cache_data = json.loads(cache_file.read_text(encoding="utf-8"))
    branches_data = cache_data.get("branches", [])

    # Build parent-child relationships
    branch_info: dict[str, BranchInfo] = {}
    for branch_name, info in branches_data:
        parent: str | None = info.get("parentBranchName")
        children: list[str] = info.get("children", [])
        is_trunk: bool = info.get("validationResult") == "TRUNK"
        branch_info[branch_name] = BranchInfo(parent=parent, children=children, is_trunk=is_trunk)

    # Check if the branch exists in the cache
    if branch not in branch_info:
        return None

    # Build the linear stack by:
    # 1. Collecting ancestors from current branch up to trunk
    # 2. Collecting descendants from current branch down
    # Result: [trunk, ..., parent, current, child, ..., leaf]

    # Traverse up to collect ancestors (current branch + all parents up to trunk)
    ancestors: list[str] = []
    current = branch
    while current in branch_info:
        ancestors.append(current)
        parent = branch_info[current]["parent"]
        if parent is None or parent not in branch_info:
            break
        current = parent

    # Reverse to get [trunk, ..., parent, current]
    ancestors.reverse()

    # Traverse down to collect descendants (all children in linear chain from current branch)
    descendants: list[str] = []
    current = branch
    while True:
        children = branch_info[current]["children"]
        if not children:
            break
        # For linear stacks, follow the first child
        # TODO: In branching stacks, this may need smarter logic
        first_child = children[0]
        if first_child not in branch_info:
            break
        descendants.append(first_child)
        current = first_child

    # Combine: ancestors includes current, so just add descendants
    return ancestors + descendants
