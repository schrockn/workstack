"""Tests for registry search functionality."""

from click.testing import CliRunner

from dot_agent_kit.cli import cli


def test_search_found():
    """Test searching for kits that exist in the registry."""
    runner = CliRunner()
    result = runner.invoke(cli, ["search", "graphite"])

    assert result.exit_code == 0
    assert "gt-dot-agent-kit" in result.output
    assert "github.com/dagsterlabs/gt-dot-agent-kit" in result.output


def test_search_not_found():
    """Test searching for kits that don't exist."""
    runner = CliRunner()
    result = runner.invoke(cli, ["search", "nonexistentkit"])

    assert result.exit_code == 1
    assert "No kits found" in result.output


def test_search_partial_match():
    """Test searching with partial keyword match."""
    runner = CliRunner()
    result = runner.invoke(cli, ["search", "work"])

    assert result.exit_code == 0
    assert "workstack-dot-agent-kit" in result.output
