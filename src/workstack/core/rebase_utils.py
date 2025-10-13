"""Utility functions for rebase operations."""

from dataclasses import dataclass
from pathlib import Path

from workstack.core.rebaseops import RebaseOps


@dataclass(frozen=True)
class RebasePlan:
    """Plan for a rebase operation."""

    source_branch: str
    target_branch: str
    merge_base: str
    commits_to_rebase: list[dict[str, str]]
    estimated_conflicts: int  # -1 if unknown


@dataclass(frozen=True)
class ConflictInfo:
    """Information about a file conflict."""

    file_path: str
    conflict_type: str  # "content", "rename", "delete"
    our_version: str | None
    their_version: str | None


def create_rebase_plan(
    rebase_ops: RebaseOps,
    cwd: Path,
    source: str,
    target: str,
) -> RebasePlan | None:
    """Create a plan for rebasing source onto target.

    Args:
        rebase_ops: RebaseOps instance
        cwd: Repository directory
        source: Branch to be rebased
        target: Branch to rebase onto

    Returns:
        RebasePlan if possible, None if branches have no common ancestor
    """
    merge_base = rebase_ops.get_merge_base(cwd, source, target)
    if merge_base is None:
        return None

    commits = rebase_ops.get_commit_range(cwd, target, source)

    return RebasePlan(
        source_branch=source,
        target_branch=target,
        merge_base=merge_base,
        commits_to_rebase=commits,
        estimated_conflicts=-1,  # Unknown until attempted
    )


def parse_conflict_markers(file_content: str) -> list[ConflictInfo]:
    """Parse git conflict markers in file content.

    Args:
        file_content: Content of file with conflict markers

    Returns:
        List of ConflictInfo objects describing each conflict region
    """
    conflicts = []
    lines = file_content.split("\n")

    i = 0
    while i < len(lines):
        if lines[i].startswith("<<<<<<<"):
            # Found conflict start
            ours_start = i + 1

            # Find separator
            separator = -1
            for j in range(ours_start, len(lines)):
                if lines[j].startswith("======="):
                    separator = j
                    break

            if separator == -1:
                i += 1
                continue

            # Find end
            theirs_end = -1
            for j in range(separator + 1, len(lines)):
                if lines[j].startswith(">>>>>>>"):
                    theirs_end = j
                    break

            if theirs_end == -1:
                i += 1
                continue

            our_version = "\n".join(lines[ours_start:separator])
            their_version = "\n".join(lines[separator + 1 : theirs_end])

            conflicts.append(
                ConflictInfo(
                    file_path="",  # Set by caller
                    conflict_type="content",
                    our_version=our_version,
                    their_version=their_version,
                )
            )

            i = theirs_end + 1
        else:
            i += 1

    return conflicts


def count_commits_between(
    rebase_ops: RebaseOps,
    cwd: Path,
    base: str,
    head: str,
) -> int:
    """Count commits between base and head.

    Args:
        rebase_ops: RebaseOps instance
        cwd: Repository directory
        base: Base ref
        head: Head ref

    Returns:
        Number of commits in range base..head
    """
    commits = rebase_ops.get_commit_range(cwd, base, head)
    return len(commits)


def is_rebase_needed(
    rebase_ops: RebaseOps,
    cwd: Path,
    branch: str,
    parent: str,
) -> bool:
    """Check if branch needs rebasing onto parent.

    Args:
        rebase_ops: RebaseOps instance
        cwd: Repository directory
        branch: Branch to check
        parent: Parent branch

    Returns:
        True if parent has commits not in branch
    """
    return count_commits_between(rebase_ops, cwd, branch, parent) > 0
