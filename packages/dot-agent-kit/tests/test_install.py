"""Tests for kit installation functionality."""

from pathlib import Path

from click.testing import CliRunner

from dot_agent_kit.cli import cli
from dot_agent_kit.io.state import load_project_config


def test_init_standalone_package(tmp_project, mock_package_installed):
    """Test installing a standalone kit package."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=str(tmp_project)):
        result = runner.invoke(cli, ["init", "--package", "test-dot-agent-kit"])

        # Debug output
        if result.exit_code != 0:
            print(f"Exit code: {result.exit_code}")
            print(f"Output: {result.output}")
            print(f"Exception: {result.exception}")

        assert result.exit_code == 0
        assert "Installed test-dot-agent-kit" in result.output

        # Check that files were installed
        commands_dir = Path(".claude/commands")
        assert (commands_dir / "test.md").exists()

        # Check configuration was saved
        config = load_project_config()
        assert "test-dot-agent-kit" in config.kits
        kit = config.kits["test-dot-agent-kit"]
        assert kit.version == "1.0.0"
        assert "commands/test.md" in kit.artifacts


def test_init_package_not_installed(tmp_project):
    """Test error when package is not installed."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=str(tmp_project)):
        result = runner.invoke(cli, ["init", "--package", "nonexistent-kit"])

        assert result.exit_code == 1
        assert "Package not installed" in result.output
        assert "uv pip install" in result.output


def test_init_with_conflicts(tmp_project, mock_package_installed):
    """Test handling file conflicts during installation."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=str(tmp_project)):
        # Create conflicting file
        commands_dir = Path(".claude/commands")
        commands_dir.mkdir(parents=True)
        (commands_dir / "test.md").write_text("existing content")

        # Try to install without force
        result = runner.invoke(cli, ["init", "--package", "test-dot-agent-kit"])
        assert result.exit_code == 1
        assert "File conflicts detected" in result.output

        # Install with force
        result = runner.invoke(cli, ["init", "--package", "test-dot-agent-kit", "--force"])
        assert result.exit_code == 0

        # Check file was overwritten
        content = (commands_dir / "test.md").read_text()
        assert "Test Command" in content
