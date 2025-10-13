# PR 2: Rebase Stack Manager

## Overview

This PR creates the core infrastructure for managing rebase stacks (temporary worktrees used for safe rebasing). It provides stack lifecycle management, state tracking, and isolation guarantees.

**Status**: Planning Complete
**Timeline**: Week 2-3 (5 working days)
**Dependencies**: [PR 1: Git Operations](STACKED_REBASE_PR1_GIT_OPERATIONS.md)
**Next PR**: [PR 3: Basic CLI](STACKED_REBASE_PR3_BASIC_CLI.md)

## Goals

1. Create and manage rebase stack worktrees
2. Track stack state and metadata
3. Ensure proper stack isolation
4. Handle multiple concurrent stacks
5. Provide stack cleanup and recovery

## Non-Goals

- No CLI commands (PR 3)
- No conflict resolution (PR 4)
- No testing in stacks (PR 5)
- No user-facing features yet

## Files to Create

### `src/workstack/core/rebase_stack_ops.py`

Core rebase stack management operations.

### `tests/core/test_rebase_stack_ops.py`

Integration tests for stack management.

## Detailed Implementation

### 1. Data Structures

Define data structures for stack management:

```python
"""Rebase stack management operations."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path

from workstack.core.gitops import GitOps


class StackState(Enum):
    """State of a rebase stack."""

    CREATED = "created"  # Stack created, rebase not started
    IN_PROGRESS = "in_progress"  # Rebase running or paused
    CONFLICTED = "conflicted"  # Has unresolved conflicts
    RESOLVED = "resolved"  # Conflicts resolved, ready to test
    TESTED = "tested"  # Tests passed, ready to apply
    FAILED = "failed"  # Tests failed or rebase failed
    APPLIED = "applied"  # Successfully applied to target branch


@dataclass(frozen=True)
class StackInfo:
    """Information about a rebase stack."""

    branch_name: str
    stack_path: Path
    created_at: datetime
    state: StackState
    target_branch: str | None
    conflicts: list[str]
    commits_to_rebase: int
    commits_applied: int


@dataclass(frozen=True)
class StackMetadata:
    """Metadata stored for each rebase stack."""

    branch_name: str
    target_branch: str
    created_at: str  # ISO format
    original_commit: str  # SHA of branch before rebase
    state: str  # StackState value
```

### 2. RebaseStackOps Class

Create the main stack management class:

```python
class RebaseStackOps:
    """Operations for managing rebase stacks.

    Rebase stacks are temporary worktrees where rebases are performed
    in isolation before being applied to the actual branch.
    """

    def __init__(self, git_ops: GitOps) -> None:
        """Initialize with a GitOps instance.

        Args:
            git_ops: GitOps instance for git operations
        """
        self.git_ops = git_ops

    def create_stack(
        self,
        repo_root: Path,
        branch: str,
        target_branch: str,
    ) -> Path:
        """Create a new rebase stack for the given branch.

        Args:
            repo_root: Repository root directory
            branch: Branch name to create stack for
            target_branch: Branch to rebase onto

        Returns:
            Path to the created stack worktree

        The stack is created as a git worktree at:
        <repo_root>/../.rebase-stack-<branch>/
        """
        stack_path = self._get_stack_path(repo_root, branch)

        # Remove existing stack if present
        if stack_path.exists():
            self.cleanup_stack(repo_root, branch)

        # Create worktree for the branch
        self.git_ops.add_worktree(
            repo_root=repo_root,
            path=stack_path,
            branch=branch,
            ref=None,
            create_branch=False,
        )

        # Save metadata
        self._save_metadata(
            stack_path,
            StackMetadata(
                branch_name=branch,
                target_branch=target_branch,
                created_at=datetime.now().isoformat(),
                original_commit=self._get_commit_sha(stack_path),
                state=StackState.CREATED.value,
            ),
        )

        return stack_path

    def cleanup_stack(self, repo_root: Path, branch: str) -> None:
        """Remove a rebase stack.

        Args:
            repo_root: Repository root directory
            branch: Branch name whose stack to remove
        """
        stack_path = self._get_stack_path(repo_root, branch)

        if not stack_path.exists():
            return

        # Remove metadata
        metadata_file = stack_path / ".rebase-stack-metadata"
        if metadata_file.exists():
            metadata_file.unlink()

        # Remove worktree
        self.git_ops.remove_worktree(
            repo_root=repo_root,
            path=stack_path,
            force=True,
        )

    def get_stack_path(self, repo_root: Path, branch: str) -> Path:
        """Get the path for a branch's rebase stack.

        Args:
            repo_root: Repository root directory
            branch: Branch name

        Returns:
            Path where the stack would be located
        """
        return self._get_stack_path(repo_root, branch)

    def list_stacks(self, repo_root: Path) -> list[StackInfo]:
        """List all active rebase stacks.

        Args:
            repo_root: Repository root directory

        Returns:
            List of StackInfo for each active stack
        """
        stacks = []
        worktrees = self.git_ops.list_worktrees(repo_root)

        for wt in worktrees:
            # Check if this is a rebase stack
            if not wt.path.name.startswith(".rebase-stack-"):
                continue

            if wt.branch is None:
                continue

            metadata = self._load_metadata(wt.path)
            if metadata is None:
                continue

            # Get current rebase status
            rebase_status = self.git_ops.get_rebase_status(wt.path)
            conflicts = rebase_status.get("conflicts", [])

            # Determine state
            state = self._determine_state(wt.path, rebase_status, metadata)

            stacks.append(
                StackInfo(
                    branch_name=wt.branch,
                    stack_path=wt.path,
                    created_at=datetime.fromisoformat(metadata.created_at),
                    state=state,
                    target_branch=metadata.target_branch,
                    conflicts=conflicts,
                    commits_to_rebase=0,  # TODO: Calculate
                    commits_applied=0,  # TODO: Calculate
                )
            )

        return stacks

    def get_stack_info(self, stack_path: Path) -> StackInfo | None:
        """Get detailed information about a stack.

        Args:
            stack_path: Path to the stack worktree

        Returns:
            StackInfo or None if not a valid stack
        """
        if not stack_path.exists():
            return None

        metadata = self._load_metadata(stack_path)
        if metadata is None:
            return None

        rebase_status = self.git_ops.get_rebase_status(stack_path)
        state = self._determine_state(stack_path, rebase_status, metadata)

        branch = self.git_ops.get_current_branch(stack_path)
        if branch is None:
            return None

        return StackInfo(
            branch_name=branch,
            stack_path=stack_path,
            created_at=datetime.fromisoformat(metadata.created_at),
            state=state,
            target_branch=metadata.target_branch,
            conflicts=rebase_status.get("conflicts", []),
            commits_to_rebase=0,
            commits_applied=0,
        )

    def update_stack_state(
        self,
        stack_path: Path,
        new_state: StackState,
    ) -> None:
        """Update the state of a rebase stack.

        Args:
            stack_path: Path to the stack
            new_state: New state to set
        """
        metadata = self._load_metadata(stack_path)
        if metadata is None:
            return

        updated_metadata = StackMetadata(
            branch_name=metadata.branch_name,
            target_branch=metadata.target_branch,
            created_at=metadata.created_at,
            original_commit=metadata.original_commit,
            state=new_state.value,
        )

        self._save_metadata(stack_path, updated_metadata)

    def stack_exists(self, repo_root: Path, branch: str) -> bool:
        """Check if a rebase stack exists for the branch.

        Args:
            repo_root: Repository root directory
            branch: Branch name

        Returns:
            True if stack exists
        """
        stack_path = self._get_stack_path(repo_root, branch)
        return stack_path.exists()

    # Private helper methods

    def _get_stack_path(self, repo_root: Path, branch: str) -> Path:
        """Get the stack path for a branch."""
        # Sanitize branch name for filesystem
        safe_branch = branch.replace("/", "-")
        return repo_root.parent / f".rebase-stack-{safe_branch}"

    def _save_metadata(self, stack_path: Path, metadata: StackMetadata) -> None:
        """Save metadata to the stack directory."""
        metadata_file = stack_path / ".rebase-stack-metadata"

        data = {
            "branch_name": metadata.branch_name,
            "target_branch": metadata.target_branch,
            "created_at": metadata.created_at,
            "original_commit": metadata.original_commit,
            "state": metadata.state,
        }

        import json

        metadata_file.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8",
        )

    def _load_metadata(self, stack_path: Path) -> StackMetadata | None:
        """Load metadata from the stack directory."""
        metadata_file = stack_path / ".rebase-stack-metadata"

        if not metadata_file.exists():
            return None

        import json

        data = json.loads(metadata_file.read_text(encoding="utf-8"))

        return StackMetadata(
            branch_name=data["branch_name"],
            target_branch=data["target_branch"],
            created_at=data["created_at"],
            original_commit=data["original_commit"],
            state=data["state"],
        )

    def _get_commit_sha(self, cwd: Path) -> str:
        """Get current commit SHA."""
        import subprocess

        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )

        return result.stdout.strip()

    def _determine_state(
        self,
        stack_path: Path,
        rebase_status: dict,
        metadata: StackMetadata,
    ) -> StackState:
        """Determine current state of the stack."""
        # Check saved state first
        try:
            saved_state = StackState(metadata.state)
        except ValueError:
            saved_state = StackState.CREATED

        # If rebase is in progress, override with current status
        if rebase_status.get("in_progress"):
            if len(rebase_status.get("conflicts", [])) > 0:
                return StackState.CONFLICTED
            return StackState.IN_PROGRESS

        # Otherwise use saved state
        return saved_state
```

### 3. Integration with Existing GitOps

The stack manager uses GitOps methods from PR 1:

- `add_worktree()` - Create stack worktree
- `remove_worktree()` - Delete stack
- `list_worktrees()` - Find stacks
- `get_rebase_status()` - Check stack state
- `get_current_branch()` - Get stack branch

## Testing Strategy

### Integration Tests

Create `tests/core/test_rebase_stack_ops.py`:

```python
"""Tests for rebase stack management."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from workstack.core.rebase_stack_ops import (
    RebaseStackOps,
    StackInfo,
    StackMetadata,
    StackState,
)


@pytest.fixture
def stack_ops(real_git_ops):
    """Create a RebaseStackOps instance."""
    return RebaseStackOps(real_git_ops)


def test_create_stack(stack_ops, test_repo):
    """Test creating a rebase stack."""
    stack_path = stack_ops.create_stack(
        test_repo,
        "feature-branch",
        "main",
    )

    assert stack_path.exists()
    assert stack_path.name == ".rebase-stack-feature-branch"

    # Verify metadata
    metadata_file = stack_path / ".rebase-stack-metadata"
    assert metadata_file.exists()

    data = json.loads(metadata_file.read_text())
    assert data["branch_name"] == "feature-branch"
    assert data["target_branch"] == "main"
    assert data["state"] == "created"


def test_cleanup_stack(stack_ops, test_repo):
    """Test removing a rebase stack."""
    # Create stack
    stack_path = stack_ops.create_stack(test_repo, "feature", "main")
    assert stack_path.exists()

    # Cleanup
    stack_ops.cleanup_stack(test_repo, "feature")
    assert not stack_path.exists()


def test_list_stacks(stack_ops, test_repo):
    """Test listing active stacks."""
    # Create multiple stacks
    stack_ops.create_stack(test_repo, "feature1", "main")
    stack_ops.create_stack(test_repo, "feature2", "main")

    stacks = stack_ops.list_stacks(test_repo)

    assert len(stacks) == 2
    branch_names = {s.branch_name for s in stacks}
    assert "feature1" in branch_names
    assert "feature2" in branch_names


def test_stack_exists(stack_ops, test_repo):
    """Test checking if stack exists."""
    assert not stack_ops.stack_exists(test_repo, "feature")

    stack_ops.create_stack(test_repo, "feature", "main")
    assert stack_ops.stack_exists(test_repo, "feature")


def test_get_stack_info(stack_ops, test_repo):
    """Test getting stack information."""
    stack_path = stack_ops.create_stack(test_repo, "feature", "main")

    info = stack_ops.get_stack_info(stack_path)

    assert info is not None
    assert info.branch_name == "feature"
    assert info.target_branch == "main"
    assert info.state == StackState.CREATED


def test_update_stack_state(stack_ops, test_repo):
    """Test updating stack state."""
    stack_path = stack_ops.create_stack(test_repo, "feature", "main")

    stack_ops.update_stack_state(stack_path, StackState.RESOLVED)

    info = stack_ops.get_stack_info(stack_path)
    assert info is not None
    assert info.state == StackState.RESOLVED


def test_concurrent_stacks(stack_ops, test_repo):
    """Test multiple stacks can exist simultaneously."""
    stack1 = stack_ops.create_stack(test_repo, "feature1", "main")
    stack2 = stack_ops.create_stack(test_repo, "feature2", "main")

    assert stack1.exists()
    assert stack2.exists()
    assert stack1 != stack2

    stacks = stack_ops.list_stacks(test_repo)
    assert len(stacks) == 2


def test_recreate_stack(stack_ops, test_repo):
    """Test recreating a stack removes the old one."""
    stack_path1 = stack_ops.create_stack(test_repo, "feature", "main")
    original_commit = stack_ops._load_metadata(stack_path1).original_commit

    # Make a commit in the original branch
    # ... git operations ...

    # Recreate stack
    stack_path2 = stack_ops.create_stack(test_repo, "feature", "main")
    new_commit = stack_ops._load_metadata(stack_path2).original_commit

    assert stack_path1 == stack_path2
    assert original_commit != new_commit


def test_sanitize_branch_names(stack_ops, test_repo):
    """Test branch names with slashes are sanitized."""
    stack_path = stack_ops.create_stack(
        test_repo,
        "feature/my-work",
        "main",
    )

    assert "feature-my-work" in str(stack_path)
    assert "/" not in stack_path.name


def test_cleanup_nonexistent_stack(stack_ops, test_repo):
    """Test cleaning up a stack that doesn't exist."""
    # Should not raise an error
    stack_ops.cleanup_stack(test_repo, "nonexistent")
```

## Acceptance Criteria

- [ ] Can create rebase stacks as isolated worktrees
- [ ] Can cleanup stacks completely
- [ ] Can list all active stacks
- [ ] Metadata is persisted and loaded correctly
- [ ] Multiple concurrent stacks work independently
- [ ] Stack state transitions are tracked
- [ ] Branch names are sanitized for filesystem
- [ ] Integration tests cover all operations
- [ ] Test coverage ≥90% for new code
- [ ] Code follows workstack standards
- [ ] Pyright passes with no errors
- [ ] All existing tests still pass

## Code Review Checklist

- [ ] Uses LBYL for file operations (check exists() first)
- [ ] Proper JSON encoding/decoding with utf-8
- [ ] Path operations use pathlib.Path
- [ ] All subprocess calls use check=True appropriately
- [ ] Type hints use Python 3.13+ syntax
- [ ] ABC used instead of Protocol
- [ ] Absolute imports only
- [ ] Maximum 4 levels of indentation
- [ ] Dataclasses are frozen where appropriate

## Migration Notes

This PR only adds new functionality, no breaking changes.

## Usage Example (for PR 3)

```python
# This shows how PR 3 will use the stack manager

from workstack.core.rebase_stack_ops import RebaseStackOps, StackState

stack_ops = RebaseStackOps(git_ops)

# Create a stack for rebasing
stack_path = stack_ops.create_stack(
    repo_root,
    branch="feature-auth",
    target_branch="main",
)

# Perform rebase in the stack
# ... rebase operations ...

# Update state as rebase progresses
stack_ops.update_stack_state(stack_path, StackState.RESOLVED)

# List all active stacks
stacks = stack_ops.list_stacks(repo_root)
for stack in stacks:
    print(f"{stack.branch_name}: {stack.state}")

# Cleanup when done
stack_ops.cleanup_stack(repo_root, "feature-auth")
```

## Next Steps

After this PR is merged:

1. Create feature branch for PR 3: `feature/stacked-rebase-pr3`
2. Implement CLI commands using the stack manager
3. Build preview functionality on top of stack infrastructure

## References

- [Master Plan](STACKED_REBASE_MASTER_PLAN.md)
- [Previous: PR 1](STACKED_REBASE_PR1_GIT_OPERATIONS.md)
- [Next: PR 3](STACKED_REBASE_PR3_BASIC_CLI.md)
- [Coding Standards](../../CLAUDE.md)
