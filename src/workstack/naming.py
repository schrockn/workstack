from __future__ import annotations

import re


_SAFE_COMPONENT_RE = re.compile(r"[^A-Za-z0-9._/-]+")


def sanitize_branch_component(name: str) -> str:
    """Return a sanitized, predictable branch component from an arbitrary name.

    - Lowercases input
    - Replaces characters outside `[A-Za-z0-9._/-]` with `-`
    - Collapses consecutive `-`
    - Strips leading/trailing `-` and `/`
    Returns `"work"` if the result is empty.
    """

    lowered = name.strip().lower()
    replaced = _SAFE_COMPONENT_RE.sub("-", lowered)
    collapsed = re.sub(r"-+", "-", replaced)
    trimmed = collapsed.strip("-/")
    return trimmed or "work"


def sanitize_worktree_name(name: str) -> str:
    """Sanitize a worktree name for use as a directory name.

    - Lowercases input
    - Replaces underscores with hyphens
    - Replaces characters outside `[A-Za-z0-9.-]` with `-`
    - Collapses consecutive `-`
    - Strips leading/trailing `-`
    Returns `"work"` if the result is empty.
    """

    lowered = name.strip().lower()
    # Replace underscores with hyphens
    replaced_underscores = lowered.replace("_", "-")
    # Replace unsafe characters with hyphens
    replaced = re.sub(r"[^a-z0-9.-]+", "-", replaced_underscores)
    # Collapse consecutive hyphens
    collapsed = re.sub(r"-+", "-", replaced)
    # Strip leading/trailing hyphens
    trimmed = collapsed.strip("-")
    return trimmed or "work"


def default_branch_for_worktree(name: str) -> str:
    """Default branch name for a worktree with the given `name`.

    Uses the pattern `work/<sanitized-name>`.
    """

    return f"work/{sanitize_branch_component(name)}"
