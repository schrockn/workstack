"""Integration tests for ShellOps."""

import os
from pathlib import Path
from unittest.mock import patch

from workstack.core.shell_ops import RealShellOps


def test_real_shell_ops_detect_shell_with_env():
    """Test shell detection with mocked environment variable."""
    with patch.dict(os.environ, {"SHELL": "/bin/zsh"}):
        ops = RealShellOps()
        result = ops.detect_shell()

        assert result is not None
        shell_name, rc_file = result
        assert shell_name == "zsh"
        assert rc_file == Path.home() / ".zshrc"


def test_real_shell_ops_detect_shell_bash():
    """Test shell detection for bash."""
    with patch.dict(os.environ, {"SHELL": "/usr/bin/bash"}):
        ops = RealShellOps()
        result = ops.detect_shell()

        assert result is not None
        shell_name, rc_file = result
        assert shell_name == "bash"
        assert rc_file == Path.home() / ".bashrc"


def test_real_shell_ops_detect_shell_fish():
    """Test shell detection for fish."""
    with patch.dict(os.environ, {"SHELL": "/usr/local/bin/fish"}):
        ops = RealShellOps()
        result = ops.detect_shell()

        assert result is not None
        shell_name, rc_file = result
        assert shell_name == "fish"
        assert rc_file == Path.home() / ".config" / "fish" / "config.fish"


def test_real_shell_ops_detect_shell_no_env():
    """Test shell detection when SHELL environment variable is not set."""
    with patch.dict(os.environ, {}, clear=True):
        ops = RealShellOps()
        result = ops.detect_shell()

        assert result is None


def test_real_shell_ops_detect_shell_unsupported():
    """Test shell detection for unsupported shell."""
    with patch.dict(os.environ, {"SHELL": "/bin/ksh"}):
        ops = RealShellOps()
        result = ops.detect_shell()

        assert result is None


def test_real_shell_ops_get_installed_tool_path():
    """Test checking if a tool is installed."""
    ops = RealShellOps()

    # Check for a tool that should always exist on Unix systems
    result = ops.get_installed_tool_path("sh")
    assert result is not None  # sh should always exist

    # Check for a tool that likely doesn't exist
    result = ops.get_installed_tool_path("nonexistent-tool-xyz-123")
    assert result is None


def test_real_shell_ops_get_installed_tool_path_python():
    """Test checking if Python is installed."""
    ops = RealShellOps()

    # Python should be available (we're running Python tests!)
    result = ops.get_installed_tool_path("python3")
    if result is None:
        # Try just "python" on some systems
        result = ops.get_installed_tool_path("python")

    assert result is not None  # Some form of Python should be found
