"""Tests for kit sync functionality."""

from pathlib import Path

from click.testing import CliRunner

from dot_agent_kit.cli import cli
from dot_agent_kit.io.state import load_project_config


def test_sync_kit_with_updates(tmp_project, mock_package_installed, monkeypatch):
    """Test syncing a kit when updates are available."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=str(tmp_project)):
        # First, install the kit at version 1.0.0
        result = runner.invoke(cli, ["init", "--package", "test-dot-agent-kit"])
        assert result.exit_code == 0

        # Verify file exists
        commands_dir = Path(".claude/commands")
        test_file = commands_dir / "test.md"
        assert test_file.exists()
        test_file.read_text()

        # Mock that a new version is available and has different content
        def mock_get_version_updated(package_name):
            if package_name == "test-dot-agent-kit":
                return "1.1.0"  # New version
            return None

        monkeypatch.setattr(
            "dot_agent_kit.utils.packaging.get_package_version", mock_get_version_updated
        )
        monkeypatch.setattr(
            "dot_agent_kit.operations.sync.get_package_version", mock_get_version_updated
        )

        # Run sync - this should succeed and overwrite the file
        result = runner.invoke(cli, ["sync"])

        # This test will FAIL until we fix the sync conflict policy
        # Expected: sync succeeds and updates files
        # Actual: raises FileExistsError due to ConflictPolicy.ERROR
        assert result.exit_code == 0, f"Sync failed: {result.output}"
        assert "Updated test-dot-agent-kit" in result.output

        # Verify kit was updated in config
        config = load_project_config()
        kit = config.kits["test-dot-agent-kit"]
        assert kit.version == "1.1.0"


def test_sync_overwrites_existing_files(tmp_project, mock_package_installed, monkeypatch):
    """Test that sync properly overwrites existing artifact files."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=str(tmp_project)):
        # Install initial version
        result = runner.invoke(cli, ["init", "--package", "test-dot-agent-kit"])
        assert result.exit_code == 0

        commands_dir = Path(".claude/commands")
        test_file = commands_dir / "test.md"

        # Manually modify the file to simulate local changes
        test_file.write_text("# Modified Content\n\nThis was changed locally.")

        # Mock new version available
        def mock_get_version_updated(package_name):
            if package_name == "test-dot-agent-kit":
                return "1.1.0"
            return None

        monkeypatch.setattr(
            "dot_agent_kit.utils.packaging.get_package_version", mock_get_version_updated
        )
        monkeypatch.setattr(
            "dot_agent_kit.operations.sync.get_package_version", mock_get_version_updated
        )

        # Run sync
        result = runner.invoke(cli, ["sync"])

        # This test will FAIL until sync uses OVERWRITE policy
        # The file should be overwritten with package content
        assert result.exit_code == 0
        content = test_file.read_text()
        assert "Test Command" in content  # Package content restored
        assert "Modified Content" not in content  # Local changes overwritten


def test_sync_with_no_updates(tmp_project, mock_package_installed):
    """Test syncing when no updates are available."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=str(tmp_project)):
        # Install kit
        result = runner.invoke(cli, ["init", "--package", "test-dot-agent-kit"])
        assert result.exit_code == 0

        # Sync with same version
        result = runner.invoke(cli, ["sync"])
        assert result.exit_code == 0
        assert "up to date" in result.output


def test_sync_respects_config_default_policy(tmp_project, sample_kit_package, monkeypatch):
    """Test that regular config operations respect the default ERROR policy."""
    # This test verifies that changing sync to use OVERWRITE doesn't break
    # the normal installation conflict detection behavior

    def mock_is_installed(package_name):
        return package_name == "test-dot-agent-kit"

    def mock_get_version(package_name):
        if package_name == "test-dot-agent-kit":
            return "1.0.0"
        return None

    def mock_get_path(package_name):
        if package_name == "test-dot-agent-kit" or package_name == "test_dot_agent_kit":
            return sample_kit_package
        return None

    monkeypatch.setattr("dot_agent_kit.utils.packaging.is_package_installed", mock_is_installed)
    monkeypatch.setattr("dot_agent_kit.utils.packaging.get_package_version", mock_get_version)
    monkeypatch.setattr("dot_agent_kit.utils.packaging.get_package_path", mock_get_path)
    monkeypatch.setattr("dot_agent_kit.sources.standalone.is_package_installed", mock_is_installed)
    monkeypatch.setattr("dot_agent_kit.sources.standalone.get_package_path", mock_get_path)

    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=str(tmp_project)):
        # Create conflicting file
        commands_dir = Path(".claude/commands")
        commands_dir.mkdir(parents=True, exist_ok=True)
        (commands_dir / "test.md").write_text("existing content")

        # Try to install without force - should fail
        result = runner.invoke(cli, ["init", "--package", "test-dot-agent-kit"])
        assert result.exit_code == 1
        assert "File conflicts detected" in result.output
