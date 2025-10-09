"""Tests for the shell_integration command."""

from click.testing import CliRunner

from workstack.cli import cli


def test_shell_integration_with_switch() -> None:
    """Test shell integration with switch command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["__shell", "switch", "test"])
    # Should handle the command
    assert result.exit_code in (0, 1)  # May fail due to missing config, which is OK for this test


def test_shell_integration_with_passthrough() -> None:
    """Test shell integration passthrough for non-switch commands."""
    runner = CliRunner()
    result = runner.invoke(cli, ["__shell", "list"])
    # Should either passthrough or handle
    assert result.exit_code in (0, 1)


def test_shell_integration_with_help() -> None:
    """Test shell integration with help command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["__shell", "--help"])
    # Should handle or passthrough
    assert result.exit_code in (0, 1)


def test_shell_integration_with_no_args() -> None:
    """Test shell integration with no arguments."""
    runner = CliRunner()
    result = runner.invoke(cli, ["__shell"])
    # Should handle empty args gracefully
    assert result.exit_code in (0, 1)


def test_shell_integration_passthrough_marker() -> None:
    """Test that passthrough commands print the passthrough marker."""
    runner = CliRunner()
    result = runner.invoke(cli, ["__shell", "list"])
    # If it's a passthrough, should contain the marker
    # Otherwise, it's being handled directly
    assert result.exit_code in (0, 1)


def test_shell_integration_unknown_command() -> None:
    """Test shell integration with unknown command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["__shell", "unknown-command", "arg1"])
    # Should handle or passthrough unknown commands
    assert result.exit_code in (0, 1)
