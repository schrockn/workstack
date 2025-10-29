"""Tests for the sync-kit command."""

from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from workstack_dev.commands.sync_kit.command import sync_kit_command, validate_namespace_pattern


def get_bundle_dir(base_path: Path, kit_name: str) -> Path:
    """Get the bundle directory path for a kit.

    Args:
        base_path: The base project path (usually tmp_path in tests)
        kit_name: The name of the kit

    Returns:
        Path to the kit's bundle directory
    """
    return (
        base_path
        / "packages"
        / "dot-agent-kit"
        / "src"
        / "dot_agent_kit"
        / "data"
        / "kits"
        / kit_name
    )


class TestNamespaceValidation:
    """Test namespace pattern validation."""

    def test_valid_agent_namespace(self):
        """Test valid agent namespace pattern."""
        is_valid, error = validate_namespace_pattern("agents/devrun/runner.md", "devrun")
        assert is_valid is True
        assert error is None

    def test_valid_skill_namespace(self):
        """Test valid skill namespace pattern."""
        is_valid, error = validate_namespace_pattern("skills/devrun/make/SKILL.md", "devrun")
        assert is_valid is True
        assert error is None

    def test_invalid_too_shallow(self):
        """Test invalid pattern that's too shallow."""
        is_valid, error = validate_namespace_pattern("agents/runner.md", "devrun")
        assert is_valid is False
        assert "too shallow" in error

    def test_invalid_wrong_namespace(self):
        """Test invalid pattern with wrong namespace."""
        is_valid, error = validate_namespace_pattern("skills/pytest/SKILL.md", "devrun")
        assert is_valid is False
        assert "not namespaced correctly" in error
        assert "skills/devrun/" in error


class TestSyncKitCommand:
    """Test sync-kit command functionality."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project structure for testing."""
        # Create project structure
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        # Create agents and skills directories
        (claude_dir / "agents" / "testkit").mkdir(parents=True)
        (claude_dir / "skills" / "testkit" / "test-skill").mkdir(parents=True)

        # Create test files in .claude/
        agent_file = claude_dir / "agents" / "testkit" / "test-agent.md"
        agent_file.write_text("# Test Agent")

        skill_file = claude_dir / "skills" / "testkit" / "test-skill" / "SKILL.md"
        skill_file.write_text("# Test Skill")

        # Create bundle structure
        bundle_dir = get_bundle_dir(tmp_path, "testkit")
        bundle_dir.mkdir(parents=True)

        # Create manifest (using singular keys as per KitManifest model)
        manifest = {
            "name": "testkit",
            "version": "1.0.0",
            "artifacts": {
                "agent": ["agents/testkit/test-agent.md"],
                "skill": ["skills/testkit/test-skill/SKILL.md"],
            },
        }

        manifest_file = bundle_dir / "kit.yaml"
        manifest_file.write_text(yaml.dump(manifest))

        return tmp_path

    def test_successful_sync(self, temp_project, monkeypatch):
        """Test successful sync of artifacts."""
        monkeypatch.chdir(temp_project)
        runner = CliRunner()
        result = runner.invoke(sync_kit_command, ["testkit"])

        assert result.exit_code == 0
        assert "Syncing kit: testkit" in result.output
        assert "2 artifacts synced successfully" in result.output

        # Check that files were copied
        bundle_dir = get_bundle_dir(temp_project, "testkit")
        agent_dest = bundle_dir / "agents" / "testkit" / "test-agent.md"
        skill_dest = bundle_dir / "skills" / "testkit" / "test-skill" / "SKILL.md"

        assert agent_dest.exists()
        assert skill_dest.exists()
        assert agent_dest.read_text() == "# Test Agent"
        assert skill_dest.read_text() == "# Test Skill"

    def test_dry_run_mode(self, temp_project, monkeypatch):
        """Test dry-run mode doesn't modify files."""
        monkeypatch.chdir(temp_project)
        runner = CliRunner()
        result = runner.invoke(sync_kit_command, ["testkit", "--dry-run"])

        assert result.exit_code == 0
        assert "Syncing kit: testkit (DRY RUN)" in result.output
        assert "Would sync:" in result.output
        assert "agents/testkit/test-agent.md" in result.output
        assert "2 artifacts would be synced (no changes made)" in result.output

        # Check that files were NOT copied
        bundle_dir = get_bundle_dir(temp_project, "testkit")
        agent_dest = bundle_dir / "agents" / "testkit" / "test-agent.md"
        skill_dest = bundle_dir / "skills" / "testkit" / "test-skill" / "SKILL.md"

        assert not agent_dest.exists()
        assert not skill_dest.exists()

    def test_verbose_mode(self, temp_project, monkeypatch):
        """Test verbose mode shows detailed output."""
        monkeypatch.chdir(temp_project)
        runner = CliRunner()
        result = runner.invoke(sync_kit_command, ["testkit", "--verbose", "--dry-run"])

        assert result.exit_code == 0
        assert "Bundle path:" in result.output
        assert "Loading manifest: kit.yaml" in result.output
        assert "Validating namespace patterns..." in result.output
        assert "✓ agents/testkit/test-agent.md (valid)" in result.output

    def test_missing_kit(self, temp_project, monkeypatch):
        """Test error when kit doesn't exist."""
        monkeypatch.chdir(temp_project)
        runner = CliRunner()
        result = runner.invoke(sync_kit_command, ["nonexistent"])

        assert result.exit_code == 1
        assert "Error: Kit 'nonexistent' not found" in result.output

    def test_missing_manifest(self, temp_project, monkeypatch):
        """Test error when manifest doesn't exist."""
        monkeypatch.chdir(temp_project)

        # Create kit directory without manifest
        bundle_dir = get_bundle_dir(temp_project, "nokit")
        bundle_dir.mkdir(parents=True)

        runner = CliRunner()
        result = runner.invoke(sync_kit_command, ["nokit"])

        assert result.exit_code == 1
        assert "Error: Manifest not found" in result.output

    def test_namespace_validation_failure(self, temp_project, monkeypatch):
        """Test sync is blocked when namespace validation fails."""
        monkeypatch.chdir(temp_project)

        # Update manifest with invalid namespace patterns
        bundle_dir = get_bundle_dir(temp_project, "testkit")
        manifest = {
            "name": "testkit",
            "version": "1.0.0",
            "artifacts": {
                "agent": ["agents/runner.md"],  # Missing namespace
                "skill": ["skills/pytest/SKILL.md"],  # Wrong namespace
            },
        }
        manifest_file = bundle_dir / "kit.yaml"
        manifest_file.write_text(yaml.dump(manifest))

        runner = CliRunner()
        result = runner.invoke(sync_kit_command, ["testkit"])

        assert result.exit_code == 1
        assert "Error: Kit 'testkit' does not follow required namespace pattern" in result.output
        assert "too shallow" in result.output
        assert "not namespaced correctly" in result.output
        assert "Sync aborted" in result.output

    def test_missing_source_file(self, temp_project, monkeypatch):
        """Test warning when source file is missing."""
        monkeypatch.chdir(temp_project)

        # Add a missing file to the manifest
        bundle_dir = get_bundle_dir(temp_project, "testkit")
        manifest = {
            "name": "testkit",
            "version": "1.0.0",
            "artifacts": {
                "agent": [
                    "agents/testkit/test-agent.md",
                    "agents/testkit/missing-agent.md",  # This doesn't exist
                ],
                "skill": ["skills/testkit/test-skill/SKILL.md"],
            },
        }
        manifest_file = bundle_dir / "kit.yaml"
        manifest_file.write_text(yaml.dump(manifest))

        runner = CliRunner()
        result = runner.invoke(sync_kit_command, ["testkit"])

        # Should partially succeed with warning about missing file
        assert result.exit_code == 1
        assert "source not found" in result.output
        assert "2 artifacts synced successfully, 1 failed" in result.output

    def test_invalid_yaml(self, temp_project, monkeypatch):
        """Test error handling for invalid YAML in manifest."""
        monkeypatch.chdir(temp_project)

        bundle_dir = get_bundle_dir(temp_project, "testkit")
        manifest_file = bundle_dir / "kit.yaml"
        manifest_file.write_text("invalid: yaml: content: [unclosed")

        runner = CliRunner()
        result = runner.invoke(sync_kit_command, ["testkit"])

        assert result.exit_code == 1
        assert "Error: Invalid manifest YAML" in result.output
