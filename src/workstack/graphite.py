"""Graphite integration for workstack.

Graphite (https://graphite.dev) is a stacked git workflow tool that allows developers
to manage dependent branches in linear stacks. This module reads graphite's internal
metadata to display stack information for worktrees.

## What is Graphite?

Graphite organizes branches into "stacks" - linear chains of dependent branches built
on top of each other. For example:

    main (trunk)
      └─ feature/phase-1
           └─ feature/phase-2
                └─ feature/phase-3

Each branch in the stack depends on its parent, making it easy to work on multiple
related changes while keeping them in separate PRs.

## Graphite Cache File

Graphite maintains a persistent cache of branch relationships at:
`.git/.graphite_cache_persist`

This is a JSON file with the following structure:

```json
{
  "branches": [
    ["main", {
      "validationResult": "TRUNK",
      "children": ["feature/phase-1", "other-feature"]
    }],
    ["feature/phase-1", {
      "parentBranchName": "main",
      "children": ["feature/phase-2"]
    }],
    ["feature/phase-2", {
      "parentBranchName": "feature/phase-1",
      "children": []
    }]
  ]
}
```

### Cache Structure Details

- `branches`: Array of [branch_name, branch_metadata] tuples
- `validationResult: "TRUNK"`: Marks the trunk branch (main/master)
- `parentBranchName`: The parent branch in the stack (null for trunk)
- `children`: Array of child branch names that branch off from this branch

### Linear Stacks vs Branching

While graphite supports branching (a trunk can have multiple children), individual
stacks are typically linear. When displaying a stack for a specific branch, we show
only the linear chain that branch belongs to:

- Traverse DOWN: From current branch to trunk (collecting ancestors)
- Traverse UP: From current branch, following the first child (collecting descendants)

This gives us a linear chain even if the full graph has branches:

```
main
 ├─ feature-a (not shown if we're on feature-b-1)
 └─ feature-b-1
      └─ feature-b-2  (linear stack: main → feature-b-1 → feature-b-2)
```

## Git Worktrees and Common Directory

Git worktrees share the same `.git` directory structure. The actual `.git` directory
may be in a different location than the worktree. We use `git rev-parse --git-common-dir`
to find the shared git directory where `.graphite_cache_persist` is stored.
"""

import json
from pathlib import Path
from typing import Any, TypedDict

from workstack.context import WorkstackContext


class BranchInfo(TypedDict):
    """Metadata for a single branch in the graphite stack.

    Fields:
        parent: The parent branch name, or None if this is a trunk branch
        children: List of child branch names that branch off from this branch
        is_trunk: True if this is a trunk branch (main/master), False otherwise
    """

    parent: str | None
    children: list[str]
    is_trunk: bool


def _load_graphite_cache(cache_file: Path) -> dict[str, Any]:
    """Load and parse graphite cache file.

    Args:
        cache_file: Path to .graphite_cache_persist file

    Returns:
        Parsed cache data dictionary

    Raises:
        json.JSONDecodeError: If cache file is corrupted (fail-fast)
        FileNotFoundError: If cache file doesn't exist
    """
    cache_data = json.loads(cache_file.read_text(encoding="utf-8"))
    return cache_data


def get_branch_stack(ctx: WorkstackContext, repo_root: Path, branch: str) -> list[str] | None:
    """Get the linear graphite stack for a given branch.

    This function reads graphite's cache file and builds the linear chain of branches
    that the given branch belongs to. The chain includes:
    - All ancestor branches from current up to trunk
    - All descendant branches from current down to the leaf

    Args:
        ctx: Workstack context with git operations
        repo_root: Path to the repository root (or worktree root)
        branch: Name of the branch to get the stack for

    Returns:
        List of branch names in the stack, ordered from trunk to leaf
        (e.g., ["main", "feature-1", "feature-2", "feature-3"]).
        Returns None if:
        - Graphite cache file doesn't exist
        - Git command fails
        - Branch is not tracked by graphite

    Algorithm:
        1. Find the common git directory using ctx.git_ops.get_git_common_dir()
           (This handles both main repos and worktrees correctly)

        2. Load and parse `.graphite_cache_persist` JSON file

        3. Build a parent-child relationship graph from the cache data

        4. Traverse DOWN from current branch to trunk, collecting ancestors:
           current → parent → grandparent → ... → trunk

        5. Traverse UP from current branch, following the first child only:
           current → child → grandchild → ... → leaf

        6. Combine into linear chain: [trunk, ..., parent, current, child, ..., leaf]

    Note on Linear vs Branching:
        While graphite's cache can represent a tree structure (trunk with multiple
        children), this function returns only the LINEAR chain that the given branch
        belongs to. When a branch has multiple children, we follow only the first one.

        This means if you have:
            main
             ├─ feature-a
             └─ feature-b-1
                  └─ feature-b-2

        And you call get_branch_stack(ctx, root, "feature-b-2"), you get:
            ["main", "feature-b-1", "feature-b-2"]

        Not: ["main", "feature-a", "feature-b-1", "feature-b-2"]

        Future Enhancement: Could use smarter logic to follow the child that's actually
        in the same stack as the target branch, rather than always taking the first child.

    Example:
        >>> stack = get_branch_stack(ctx, Path("/repo"), "feature/phase-2")
        >>> print(stack)
        ["main", "feature/phase-1", "feature/phase-2", "feature/phase-3"]
    """
    git_dir = ctx.git_ops.get_git_common_dir(repo_root)
    if git_dir is None:
        return None

    # Step 2: Check if graphite cache file exists
    cache_file = git_dir / ".graphite_cache_persist"
    if not cache_file.exists():
        return None

    # Step 3: Parse the graphite cache JSON file
    cache_data = _load_graphite_cache(cache_file)
    branches_data = cache_data.get("branches", [])

    # Step 4: Build parent-child relationship graph
    # The cache stores branches as [name, metadata] tuples, we convert to a dict
    # mapping branch name -> BranchInfo for easier traversal
    branch_info: dict[str, BranchInfo] = {}
    for branch_name, info in branches_data:
        parent: str | None = info.get("parentBranchName")
        children: list[str] = info.get("children", [])
        is_trunk: bool = info.get("validationResult") == "TRUNK"
        branch_info[branch_name] = BranchInfo(parent=parent, children=children, is_trunk=is_trunk)

    # Check if the requested branch exists in graphite's cache
    if branch not in branch_info:
        return None

    # Step 5: Traverse DOWN the stack to collect ancestors (current → parent → ... → trunk)
    # In graphite terminology, "down" means towards the trunk/base
    ancestors: list[str] = []
    current = branch
    while current in branch_info:
        ancestors.append(current)
        parent = branch_info[current]["parent"]
        if parent is None or parent not in branch_info:
            # Reached trunk (no parent) or parent not in cache
            break
        current = parent

    # Reverse to get [trunk, ..., grandparent, parent, current]
    ancestors.reverse()

    # Step 6: Traverse UP the stack to collect descendants (current → child → ... → leaf)
    # In graphite terminology, "up" means away from trunk towards the tip of the stack
    # Only follow the first child to maintain a linear chain
    descendants: list[str] = []
    current = branch
    while True:
        children = branch_info[current]["children"]
        if not children:
            # Reached a leaf node (no children)
            break
        # For linear stacks, follow the first child
        # NOTE: If there are multiple children (branching), we only follow the first one
        # This keeps the stack linear, but may not show all related branches
        first_child = children[0]
        if first_child not in branch_info:
            # Child exists in metadata but not in cache (shouldn't happen normally)
            break
        descendants.append(first_child)
        current = first_child

    # Step 7: Combine ancestors and descendants
    # ancestors already includes the current branch, so we just append descendants
    return ancestors + descendants
