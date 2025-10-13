"""Rebase stack management operations.

This module provides infrastructure for managing rebase stacks (temporary worktrees
used for safe rebasing). It provides stack lifecycle management, state tracking,
and isolation guarantees.

Architecture:
- StackState: Enum defining the lifecycle states of a rebase stack
- StackInfo: Runtime information about a stack
- StackMetadata: Persistent metadata stored in the stack directory
- RebaseStackOps: Main class for managing rebase stacks
"""

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from workstack.core.gitops import GitOps
from workstack.core.global_config_ops import GlobalConfigOps

DEFAULT_STACK_LOCATION = ".rebase-stack"
STACK_BRANCH_PREFIX = "workstack/rebase-stack-"


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


class RebaseStackOps:
    """Operations for managing rebase stacks.

    Rebase stacks are temporary worktrees where rebases are performed
    in isolation before being applied to the actual branch.
    """

    def __init__(
        self,
        git_ops: GitOps,
        global_config_ops: GlobalConfigOps | None = None,
    ) -> None:
        """Initialize with a GitOps instance.

        Args:
            git_ops: GitOps instance for git operations
        """
        self.git_ops = git_ops
        self._global_config_ops = global_config_ops
        self._stack_location = self._resolve_stack_location()

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

        The stack is created as a git worktree under the configured stack
        location (default: <repo_root>/../.rebase-stack-<branch>/).
        """
        stack_path = self._get_stack_path(repo_root, branch)
        stack_branch = self._get_stack_branch_name(branch)

        # Remove existing stack if present
        if stack_path.exists():
            self.cleanup_stack(repo_root, branch)
        else:
            # Ensure leftover stack branches from previous runs are removed
            self._delete_branch_if_exists(repo_root, stack_branch)

        stack_path.parent.mkdir(parents=True, exist_ok=True)

        # Create worktree for the branch
        self.git_ops.add_worktree(
            repo_root=repo_root,
            path=stack_path,
            branch=stack_branch,
            ref=branch,
            create_branch=True,
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
        stack_branch = self._get_stack_branch_name(branch)

        if stack_path.exists():
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

        # Remove stack branch if it still exists
        self._delete_branch_if_exists(repo_root, stack_branch)

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
            metadata = self._load_metadata(wt.path)
            if metadata is None:
                continue

            expected_path = self._get_stack_path(repo_root, metadata.branch_name)
            if wt.path.resolve() != expected_path:
                continue

            # Get current rebase status
            rebase_status = self.git_ops.get_rebase_status(wt.path)
            conflicts = rebase_status.get("conflicts", [])

            # Determine state
            state = self._determine_state(wt.path, rebase_status, metadata)

            stacks.append(
                StackInfo(
                    branch_name=metadata.branch_name,
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

        return StackInfo(
            branch_name=metadata.branch_name,
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

    def _resolve_stack_location(self) -> str:
        """Resolve stack location prefix from config."""
        if self._global_config_ops is None:
            return DEFAULT_STACK_LOCATION

        try:
            location = self._global_config_ops.get_rebase_stack_location()
        except FileNotFoundError:
            return DEFAULT_STACK_LOCATION

        if not location or location.strip() == "":
            return DEFAULT_STACK_LOCATION

        return location.strip()

    def _get_stack_branch_name(self, branch: str) -> str:
        """Generate a unique stack branch name for the given branch."""
        safe_branch = branch.replace("/", "-")
        return f"{STACK_BRANCH_PREFIX}{safe_branch}"

    def _delete_branch_if_exists(self, repo_root: Path, branch: str) -> None:
        """Delete branch if it exists, ignoring errors when absent."""
        if branch == "":
            return

        if not self._branch_exists(repo_root, branch):
            return

        subprocess.run(
            ["git", "branch", "-D", branch],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )

    def _branch_exists(self, repo_root: Path, branch: str) -> bool:
        """Check if a git branch exists."""
        result = subprocess.run(
            ["git", "show-ref", "--verify", f"refs/heads/{branch}"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0

    def _get_stack_path(self, repo_root: Path, branch: str) -> Path:
        """Get the stack path for a branch."""
        safe_branch = branch.replace("/", "-")

        location = self._stack_location.strip()
        if not location:
            location = DEFAULT_STACK_LOCATION

        location_path = Path(location)
        if location_path.is_absolute() or len(location_path.parts) > 1:
            if location_path.is_absolute():
                base_dir = location_path
            else:
                base_dir = repo_root.parent / location_path
            return (base_dir / safe_branch).resolve()

        separator = "" if location.endswith(("-", "_")) else "-"
        directory_name = f"{location}{separator}{safe_branch}"
        return (repo_root.parent / directory_name).resolve()

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

        metadata_file.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8",
        )

    def _load_metadata(self, stack_path: Path) -> StackMetadata | None:
        """Load metadata from the stack directory."""
        metadata_file = stack_path / ".rebase-stack-metadata"

        if not metadata_file.exists():
            return None

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
        rebase_status: dict[str, Any],
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
