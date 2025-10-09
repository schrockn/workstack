"""Integration tests for dev CLI commands."""

from click.testing import CliRunner

from workstack.dev_cli.__main__ import cli


def test_clean_cache_help() -> None:
    """Test clean-cache help output."""
    runner = CliRunner()
    result = runner.invoke(cli, ["clean-cache", "--help"])
    assert result.exit_code == 0
    assert "Clean all cache directories" in result.output


def test_publish_to_pypi_help() -> None:
    """Test publish-to-pypi help output."""
    runner = CliRunner()
    result = runner.invoke(cli, ["publish-to-pypi", "--help"])
    assert result.exit_code == 0
    assert "Publish workstack package to PyPI" in result.output


def test_create_agents_symlinks_help() -> None:
    """Test create-agents-symlinks help output."""
    runner = CliRunner()
    result = runner.invoke(cli, ["create-agents-symlinks", "--help"])
    assert result.exit_code == 0
    assert "Create AGENTS.md symlinks" in result.output


def test_cli_help_shows_commands() -> None:
    """Test that CLI help shows available commands."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "clean-cache" in result.output
    assert "publish-to-pypi" in result.output
    assert "create-agents-symlinks" in result.output
