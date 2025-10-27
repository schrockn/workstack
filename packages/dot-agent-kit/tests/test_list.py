"""Tests for list command functionality."""

import json

from click.testing import CliRunner

from dot_agent_kit.cli import cli


def test_list_no_kits_installed():
    """Test listing when no kits are installed."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["list"])

        assert result.exit_code == 0
        # Should show registry entries
        assert "gt-dot-agent-kit" in result.output
        assert "workstack-dot-agent-kit" in result.output
        # Should show table headers
        assert "STATUS" in result.output
        assert "NAME" in result.output
        assert "VERSION" in result.output


def test_list_json_output():
    """Test JSON output format."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["list", "--json"])

        assert result.exit_code == 0

        # Parse JSON output
        kits = json.loads(result.output)

        # Should be a list of kit info
        assert isinstance(kits, list)
        assert len(kits) > 0

        # Check structure of first kit
        kit = kits[0]
        assert "name" in kit
        assert "version" in kit
        assert "description" in kit
        assert "installed" in kit
        assert "url" in kit


def test_list_alias_ls():
    """Test that ls alias works."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["ls"])

        assert result.exit_code == 0
        # Should show same output as list
        assert "gt-dot-agent-kit" in result.output


def test_list_with_installed_kit(tmp_project, mock_package_installed):
    """Test listing with an installed kit."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=str(tmp_project)):
        # First install a kit
        runner.invoke(cli, ["init", "--package", "test-dot-agent-kit"])

        # Now list
        result = runner.invoke(cli, ["list"])

        assert result.exit_code == 0
        # The bundled registry kits should still appear
        assert "gt-dot-agent-kit" in result.output
        # Test kit should appear (though not in registry)
        assert "test-dot-agent-kit" in result.output


def test_list_json_with_installed_kit(tmp_project, mock_package_installed):
    """Test JSON output with installed kit."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=str(tmp_project)):
        # Install a kit
        runner.invoke(cli, ["init", "--package", "test-dot-agent-kit"])

        # List as JSON
        result = runner.invoke(cli, ["list", "--json"])

        assert result.exit_code == 0

        kits = json.loads(result.output)

        # Find the installed kit
        installed_kits = [k for k in kits if k["installed"]]
        assert len(installed_kits) > 0

        # Check that test kit is marked as installed
        test_kit = next((k for k in kits if k["name"] == "test-dot-agent-kit"), None)
        assert test_kit is not None
        assert test_kit["installed"] is True
