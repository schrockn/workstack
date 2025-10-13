"""Fake implementation of ShellOps for testing.

This fake enables testing shell-dependent functionality without
requiring specific shell configurations or installed tools.
"""

from pathlib import Path

from workstack.core.shell_ops import ShellOps


class FakeShellOps(ShellOps):
    """In-memory fake implementation of shell operations.

    Constructor Injection:
    - All state is provided via constructor parameters
    - No mutations occur (immutable after construction)

    When to Use:
    - Testing shell-dependent commands (e.g., init, shell setup)
    - Simulating different shell environments (bash, zsh, fish)
    - Testing behavior when tools are/aren't installed

    Examples:
        # Test with bash shell detected
        >>> shell_ops = FakeShellOps(
        ...     detected_shell=("bash", Path.home() / ".bashrc")
        ... )
        >>> result = shell_ops.detect_shell()
        >>> assert result == ("bash", Path.home() / ".bashrc")

        # Test with tool installed
        >>> shell_ops = FakeShellOps(
        ...     installed_tools={"gt": "/usr/local/bin/gt"}
        ... )
        >>> gt_path = shell_ops.check_tool_installed("gt")
        >>> assert gt_path == "/usr/local/bin/gt"

        # Test with no shell detected
        >>> shell_ops = FakeShellOps(detected_shell=None)
        >>> result = shell_ops.detect_shell()
        >>> assert result is None
    """

    def __init__(
        self,
        *,
        detected_shell: tuple[str, Path] | None = None,
        installed_tools: dict[str, str] | None = None,
    ) -> None:
        """Initialize fake with predetermined shell and tool availability.

        Args:
            detected_shell: Shell to return from detect_shell(), or None if no shell
                should be detected. Format: (shell_name, rc_file_path)
            installed_tools: Mapping of tool name to executable path. Tools not in
                this mapping will return None from check_tool_installed()
        """
        self._detected_shell = detected_shell
        self._installed_tools = installed_tools or {}

    def detect_shell(self) -> tuple[str, Path] | None:
        """Return the shell configured at construction time."""
        return self._detected_shell

    def check_tool_installed(self, tool_name: str) -> str | None:
        """Return the tool path if configured, None otherwise."""
        return self._installed_tools.get(tool_name)
