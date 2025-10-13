"""Fake global config operations for testing.

FakeGlobalConfigOps is an in-memory implementation that accepts pre-configured state
in its constructor. All state is held in memory - no filesystem access.
"""

from pathlib import Path

from workstack.core.global_config_ops import _UNCHANGED, GlobalConfigOps, _UnchangedType


class FakeGlobalConfigOps(GlobalConfigOps):
    """In-memory fake implementation - no filesystem access.

    All state is held in memory. Constructor accepts optional initial field values.
    This class has NO filesystem operations - all state is in-memory only.
    """

    def __init__(
        self,
        *,
        workstacks_root: Path | None = None,
        use_graphite: bool = False,
        shell_setup_complete: bool = False,
        show_pr_info: bool = True,
        show_pr_checks: bool = False,
        rebase_use_stacks: bool = True,
        rebase_auto_test: bool = False,
        rebase_preserve_stacks: bool = False,
        rebase_conflict_tool: str = "vimdiff",
        rebase_stack_location: str = ".rebase-stack",
        exists: bool = True,
        config_path: Path | None = None,
    ) -> None:
        """Create fake with optional pre-configured state.

        Args:
            workstacks_root: Initial workstacks root. If None and exists=True, raises
                           FileNotFoundError on getter calls (invalid state).
            use_graphite: Initial graphite preference (default: False)
            shell_setup_complete: Initial shell setup status (default: False)
            show_pr_info: Initial PR info display preference (default: True)
            show_pr_checks: Initial CI check display preference (default: False)
            rebase_use_stacks: Always use rebase stacks (default: True)
            rebase_auto_test: Auto-run tests after conflicts (default: False)
            rebase_preserve_stacks: Keep stacks after applying (default: False)
            rebase_conflict_tool: Conflict resolution tool (default: "vimdiff")
            rebase_stack_location: Stack directory prefix (default: ".rebase-stack")
            exists: Whether config "exists". If False, getters raise FileNotFoundError.
            config_path: Path to report in error messages and get_path().
                        Defaults to /fake/config.toml for testing.

        Example:
            # Config that exists with specific values
            >>> fake = FakeGlobalConfigOps(
            ...     workstacks_root=Path("/tmp/workstacks"),
            ...     use_graphite=True,
            ...     shell_setup_complete=False,
            ... )
            >>> fake.get_workstacks_root()  # Returns Path("/tmp/workstacks")

            # Config that doesn't exist
            >>> fake = FakeGlobalConfigOps(exists=False)
            >>> fake.get_workstacks_root()  # Raises FileNotFoundError
        """
        self._workstacks_root = workstacks_root
        self._use_graphite = use_graphite
        self._shell_setup_complete = shell_setup_complete
        self._show_pr_info = show_pr_info
        self._show_pr_checks = show_pr_checks
        self._rebase_use_stacks = rebase_use_stacks
        self._rebase_auto_test = rebase_auto_test
        self._rebase_preserve_stacks = rebase_preserve_stacks
        self._rebase_conflict_tool = rebase_conflict_tool
        self._rebase_stack_location = rebase_stack_location
        self._exists = exists
        self._path = config_path if config_path is not None else Path("/fake/config.toml")

    def get_workstacks_root(self) -> Path:
        if not self._exists:
            raise FileNotFoundError(f"Global config not found at {self._path}")
        if self._workstacks_root is None:
            raise ValueError(f"Missing 'workstacks_root' in {self._path}")
        return self._workstacks_root

    def get_use_graphite(self) -> bool:
        if not self._exists:
            raise FileNotFoundError(f"Global config not found at {self._path}")
        return self._use_graphite

    def get_shell_setup_complete(self) -> bool:
        if not self._exists:
            raise FileNotFoundError(f"Global config not found at {self._path}")
        return self._shell_setup_complete

    def get_show_pr_info(self) -> bool:
        if not self._exists:
            raise FileNotFoundError(f"Global config not found at {self._path}")
        return self._show_pr_info

    def get_show_pr_checks(self) -> bool:
        if not self._exists:
            raise FileNotFoundError(f"Global config not found at {self._path}")
        return self._show_pr_checks

    def get_rebase_use_stacks(self) -> bool:
        if not self._exists:
            raise FileNotFoundError(f"Global config not found at {self._path}")
        return self._rebase_use_stacks

    def get_rebase_auto_test(self) -> bool:
        if not self._exists:
            raise FileNotFoundError(f"Global config not found at {self._path}")
        return self._rebase_auto_test

    def get_rebase_preserve_stacks(self) -> bool:
        if not self._exists:
            raise FileNotFoundError(f"Global config not found at {self._path}")
        return self._rebase_preserve_stacks

    def get_rebase_conflict_tool(self) -> str:
        if not self._exists:
            raise FileNotFoundError(f"Global config not found at {self._path}")
        return self._rebase_conflict_tool

    def get_rebase_stack_location(self) -> str:
        if not self._exists:
            raise FileNotFoundError(f"Global config not found at {self._path}")
        return self._rebase_stack_location

    def set(
        self,
        *,
        workstacks_root: Path | _UnchangedType = _UNCHANGED,
        use_graphite: bool | _UnchangedType = _UNCHANGED,
        shell_setup_complete: bool | _UnchangedType = _UNCHANGED,
        show_pr_info: bool | _UnchangedType = _UNCHANGED,
        show_pr_checks: bool | _UnchangedType = _UNCHANGED,
        rebase_use_stacks: bool | _UnchangedType = _UNCHANGED,
        rebase_auto_test: bool | _UnchangedType = _UNCHANGED,
        rebase_preserve_stacks: bool | _UnchangedType = _UNCHANGED,
        rebase_conflict_tool: str | _UnchangedType = _UNCHANGED,
        rebase_stack_location: str | _UnchangedType = _UNCHANGED,
    ) -> None:
        """Update config fields in memory (not filesystem).

        Creates config if it doesn't exist (sets _exists=True).
        """
        # Check if at least one field is being updated
        if (
            isinstance(workstacks_root, _UnchangedType)
            and isinstance(use_graphite, _UnchangedType)
            and isinstance(shell_setup_complete, _UnchangedType)
            and isinstance(show_pr_info, _UnchangedType)
            and isinstance(show_pr_checks, _UnchangedType)
            and isinstance(rebase_use_stacks, _UnchangedType)
            and isinstance(rebase_auto_test, _UnchangedType)
            and isinstance(rebase_preserve_stacks, _UnchangedType)
            and isinstance(rebase_conflict_tool, _UnchangedType)
            and isinstance(rebase_stack_location, _UnchangedType)
        ):
            raise ValueError("At least one field must be provided")

        # Handle new config creation
        if not self._exists:
            if isinstance(workstacks_root, _UnchangedType):
                raise ValueError("workstacks_root must be provided for new config")
            self._workstacks_root = workstacks_root
            self._use_graphite = False if isinstance(use_graphite, _UnchangedType) else use_graphite
            self._shell_setup_complete = (
                False if isinstance(shell_setup_complete, _UnchangedType) else shell_setup_complete
            )
            self._show_pr_info = True if isinstance(show_pr_info, _UnchangedType) else show_pr_info
            self._show_pr_checks = (
                False if isinstance(show_pr_checks, _UnchangedType) else show_pr_checks
            )
            self._rebase_use_stacks = (
                True if isinstance(rebase_use_stacks, _UnchangedType) else rebase_use_stacks
            )
            self._rebase_auto_test = (
                False if isinstance(rebase_auto_test, _UnchangedType) else rebase_auto_test
            )
            self._rebase_preserve_stacks = (
                False
                if isinstance(rebase_preserve_stacks, _UnchangedType)
                else rebase_preserve_stacks
            )
            self._rebase_conflict_tool = (
                "vimdiff"
                if isinstance(rebase_conflict_tool, _UnchangedType)
                else rebase_conflict_tool
            )
            self._rebase_stack_location = (
                ".rebase-stack"
                if isinstance(rebase_stack_location, _UnchangedType)
                else rebase_stack_location
            )
            self._exists = True
            return

        # Update existing config
        if not isinstance(workstacks_root, _UnchangedType):
            self._workstacks_root = workstacks_root

        if not isinstance(use_graphite, _UnchangedType):
            self._use_graphite = use_graphite

        if not isinstance(shell_setup_complete, _UnchangedType):
            self._shell_setup_complete = shell_setup_complete

        if not isinstance(show_pr_info, _UnchangedType):
            self._show_pr_info = show_pr_info

        if not isinstance(show_pr_checks, _UnchangedType):
            self._show_pr_checks = show_pr_checks

        if not isinstance(rebase_use_stacks, _UnchangedType):
            self._rebase_use_stacks = rebase_use_stacks

        if not isinstance(rebase_auto_test, _UnchangedType):
            self._rebase_auto_test = rebase_auto_test

        if not isinstance(rebase_preserve_stacks, _UnchangedType):
            self._rebase_preserve_stacks = rebase_preserve_stacks

        if not isinstance(rebase_conflict_tool, _UnchangedType):
            self._rebase_conflict_tool = rebase_conflict_tool

        if not isinstance(rebase_stack_location, _UnchangedType):
            self._rebase_stack_location = rebase_stack_location

    def exists(self) -> bool:
        return self._exists

    def get_path(self) -> Path:
        return self._path
