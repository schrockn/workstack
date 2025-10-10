"""Tests for command loader."""

from pathlib import Path

import click
import pytest

from devclikit.exceptions import CommandLoadError
from devclikit.loader import load_commands


def test_load_commands_empty_directory(tmp_path: Path) -> None:
    """Test loading from empty commands directory."""
    commands_dir = tmp_path / "commands"
    commands_dir.mkdir()

    commands = load_commands(commands_dir)

    assert commands == {}


def test_load_commands_nonexistent_directory(tmp_path: Path) -> None:
    """Test loading from nonexistent directory returns empty dict."""
    commands_dir = tmp_path / "nonexistent"

    commands = load_commands(commands_dir)

    assert commands == {}


def test_load_commands_nonexistent_strict(tmp_path: Path) -> None:
    """Test strict mode raises error for nonexistent directory."""
    commands_dir = tmp_path / "nonexistent"

    with pytest.raises(CommandLoadError):
        load_commands(commands_dir, strict=True)


def test_load_commands_single_command(tmp_path: Path) -> None:
    """Test loading a single command."""
    commands_dir = tmp_path / "commands"
    cmd_dir = commands_dir / "test"
    cmd_dir.mkdir(parents=True)

    (cmd_dir / "command.py").write_text(
        """
import click

@click.command()
def command():
    '''Test command'''
    pass
""",
        encoding="utf-8",
    )

    commands = load_commands(commands_dir)

    assert "test" in commands
    assert isinstance(commands["test"], click.Command)
    assert commands["test"].help == "Test command"


def test_load_commands_multiple_commands(tmp_path: Path) -> None:
    """Test loading multiple commands."""
    commands_dir = tmp_path / "commands"

    # Create first command
    cmd1_dir = commands_dir / "cmd1"
    cmd1_dir.mkdir(parents=True)
    (cmd1_dir / "command.py").write_text(
        """
import click

@click.command(name="cmd1")
def command():
    pass
""",
        encoding="utf-8",
    )

    # Create second command
    cmd2_dir = commands_dir / "cmd2"
    cmd2_dir.mkdir(parents=True)
    (cmd2_dir / "command.py").write_text(
        """
import click

@click.command(name="cmd2")
def command():
    pass
""",
        encoding="utf-8",
    )

    commands = load_commands(commands_dir)

    assert len(commands) == 2
    assert "cmd1" in commands
    assert "cmd2" in commands


def test_load_commands_skips_hidden_directories(tmp_path: Path) -> None:
    """Test that hidden directories are skipped."""
    commands_dir = tmp_path / "commands"

    # Create hidden directory
    hidden_dir = commands_dir / "_hidden"
    hidden_dir.mkdir(parents=True)
    (hidden_dir / "command.py").write_text(
        """
import click

@click.command()
def command():
    pass
""",
        encoding="utf-8",
    )

    commands = load_commands(commands_dir)

    assert "_hidden" not in commands


def test_load_commands_skips_files(tmp_path: Path) -> None:
    """Test that files in commands directory are skipped."""
    commands_dir = tmp_path / "commands"
    commands_dir.mkdir()

    # Create a file instead of directory
    (commands_dir / "not_a_dir.py").write_text("# Not a command", encoding="utf-8")

    commands = load_commands(commands_dir)

    assert "not_a_dir" not in commands


def test_load_commands_no_command_py(tmp_path: Path) -> None:
    """Test that directories without command.py are skipped."""
    commands_dir = tmp_path / "commands"
    cmd_dir = commands_dir / "incomplete"
    cmd_dir.mkdir(parents=True)

    # Create script.py but no command.py
    (cmd_dir / "script.py").write_text("# Script", encoding="utf-8")

    commands = load_commands(commands_dir)

    assert "incomplete" not in commands


def test_load_commands_broken_module(tmp_path: Path) -> None:
    """Test that broken modules are skipped with warning."""
    commands_dir = tmp_path / "commands"
    cmd_dir = commands_dir / "broken"
    cmd_dir.mkdir(parents=True)

    (cmd_dir / "command.py").write_text(
        """
import nonexistent_module  # Will fail
""",
        encoding="utf-8",
    )

    # Should not raise, just skip the broken command
    commands = load_commands(commands_dir)

    assert "broken" not in commands


def test_load_commands_broken_module_strict(tmp_path: Path) -> None:
    """Test strict mode raises error for broken modules."""
    commands_dir = tmp_path / "commands"
    cmd_dir = commands_dir / "broken"
    cmd_dir.mkdir(parents=True)

    (cmd_dir / "command.py").write_text(
        """
import nonexistent_module
""",
        encoding="utf-8",
    )

    with pytest.raises(CommandLoadError):
        load_commands(commands_dir, strict=True)


def test_load_commands_uses_directory_name(tmp_path: Path) -> None:
    """Test that directory name is used (not command.name)."""
    commands_dir = tmp_path / "commands"
    cmd_dir = commands_dir / "my_command"
    cmd_dir.mkdir(parents=True)

    (cmd_dir / "command.py").write_text(
        """
import click

@click.command(name="custom-name")
def command():
    pass
""",
        encoding="utf-8",
    )

    commands = load_commands(commands_dir)

    # Directory name is preferred, with underscores converted to hyphens
    assert "my-command" in commands
    assert "custom-name" not in commands


def test_load_commands_converts_underscores_to_hyphens(tmp_path: Path) -> None:
    """Test that directory names with underscores become hyphenated."""
    commands_dir = tmp_path / "commands"
    cmd_dir = commands_dir / "my_command"
    cmd_dir.mkdir(parents=True)

    (cmd_dir / "command.py").write_text(
        """
import click

@click.command()  # No explicit name
def command():
    pass
""",
        encoding="utf-8",
    )

    commands = load_commands(commands_dir)

    assert "my-command" in commands
