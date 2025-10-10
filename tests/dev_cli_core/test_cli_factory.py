"""Tests for CLI factory."""

from pathlib import Path

import click
from click.testing import CliRunner

from dev_cli_core.cli_factory import create_cli


def test_create_cli_basic(tmp_path: Path) -> None:
    """Test creating a basic CLI."""
    commands_dir = tmp_path / "commands"
    commands_dir.mkdir()

    cli = create_cli(
        name="test-cli",
        description="Test CLI",
        commands_dir=commands_dir,
    )

    assert isinstance(cli, click.Group)
    assert cli.name == "test-cli"
    assert cli.help == "Test CLI"


def test_create_cli_with_version(tmp_path: Path) -> None:
    """Test CLI with version command."""
    commands_dir = tmp_path / "commands"
    commands_dir.mkdir()

    cli = create_cli(
        name="test-cli",
        description="Test CLI",
        commands_dir=commands_dir,
        version="1.0.0",
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["version"])

    assert result.exit_code == 0
    assert "1.0.0" in result.output


def test_create_cli_loads_commands(tmp_path: Path) -> None:
    """Test that CLI loads commands from directory."""
    commands_dir = tmp_path / "commands"
    cmd_dir = commands_dir / "test"
    cmd_dir.mkdir(parents=True)

    (cmd_dir / "command.py").write_text(
        """
import click

@click.command()
def command():
    '''Test command'''
    click.echo("Test executed")
""",
        encoding="utf-8",
    )

    cli = create_cli(
        name="test-cli",
        description="Test CLI",
        commands_dir=commands_dir,
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["test"])

    assert result.exit_code == 0
    assert "Test executed" in result.output


def test_create_cli_with_completion(tmp_path: Path) -> None:
    """Test that completion commands are added."""
    commands_dir = tmp_path / "commands"
    commands_dir.mkdir()

    cli = create_cli(
        name="test-cli",
        description="Test CLI",
        commands_dir=commands_dir,
        add_completion=True,
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["completion", "--help"])

    assert result.exit_code == 0
    assert "completion" in result.output


def test_create_cli_without_completion(tmp_path: Path) -> None:
    """Test CLI without completion commands."""
    commands_dir = tmp_path / "commands"
    commands_dir.mkdir()

    cli = create_cli(
        name="test-cli",
        description="Test CLI",
        commands_dir=commands_dir,
        add_completion=False,
    )

    # Completion command should not exist
    assert "completion" not in [cmd.name for cmd in cli.commands.values()]


def test_create_cli_help_text(tmp_path: Path) -> None:
    """Test CLI help text."""
    commands_dir = tmp_path / "commands"
    commands_dir.mkdir()

    cli = create_cli(
        name="test-cli",
        description="Test CLI for testing",
        commands_dir=commands_dir,
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "Test CLI for testing" in result.output


def test_create_cli_with_context_settings(tmp_path: Path) -> None:
    """Test CLI with custom context settings."""
    commands_dir = tmp_path / "commands"
    commands_dir.mkdir()

    cli = create_cli(
        name="test-cli",
        description="Test CLI",
        commands_dir=commands_dir,
        context_settings={"help_option_names": ["-h", "--help"]},
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["-h"])

    assert result.exit_code == 0
    assert "Test CLI" in result.output
