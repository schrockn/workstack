"""Tests for the sync-kit command."""

from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from workstack_dev.commands.sync_kit.command import sync_kit_command


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

    def test_sync_all_dev_kits(self, tmp_path, monkeypatch):
        """Test syncing all kits marked with sync_source: workstack-dev."""
        monkeypatch.chdir(tmp_path)

        # Create .claude directory with artifacts for multiple kits
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        # Kit 1: devkit
        (claude_dir / "agents" / "devkit").mkdir(parents=True)
        (claude_dir / "agents" / "devkit" / "agent.md").write_text("# Dev Agent")

        # Kit 2: testkit
        (claude_dir / "skills" / "testkit").mkdir(parents=True)
        (claude_dir / "skills" / "testkit" / "SKILL.md").write_text("# Test Skill")

        # Create bundle structure for both kits
        devkit_bundle = get_bundle_dir(tmp_path, "devkit")
        devkit_bundle.mkdir(parents=True)
        (devkit_bundle / "kit.yaml").write_text(
            yaml.dump(
                {
                    "name": "devkit",
                    "version": "1.0.0",
                    "sync_source": "workstack-dev",
                    "artifacts": {"agent": ["agents/devkit/agent.md"]},
                }
            )
        )

        testkit_bundle = get_bundle_dir(tmp_path, "testkit")
        testkit_bundle.mkdir(parents=True)
        (testkit_bundle / "kit.yaml").write_text(
            yaml.dump(
                {
                    "name": "testkit",
                    "version": "1.0.0",
                    "sync_source": "workstack-dev",
                    "artifacts": {"skill": ["skills/testkit/SKILL.md"]},
                }
            )
        )

        # Run sync without kit_name argument
        runner = CliRunner()
        result = runner.invoke(sync_kit_command, [])

        assert result.exit_code == 0
        assert "Syncing 2 kit(s): devkit, testkit" in result.output
        assert "Syncing kit: devkit" in result.output
        assert "Syncing kit: testkit" in result.output
        assert "All 2 kit(s) synced successfully" in result.output

        # Verify files were synced
        assert (devkit_bundle / "agents" / "devkit" / "agent.md").exists()
        assert (testkit_bundle / "skills" / "testkit" / "SKILL.md").exists()

    def test_sync_all_kits_skips_non_dev_kits(self, tmp_path, monkeypatch):
        """Test that syncing all kits only syncs those with sync_source: workstack-dev."""
        monkeypatch.chdir(tmp_path)

        # Create .claude directory
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        # Create bundle structure with dev and non-dev kits
        devkit_bundle = get_bundle_dir(tmp_path, "devkit")
        devkit_bundle.mkdir(parents=True)
        (devkit_bundle / "kit.yaml").write_text(
            yaml.dump(
                {
                    "name": "devkit",
                    "version": "1.0.0",
                    "sync_source": "workstack-dev",
                    "artifacts": {"agent": ["agents/devkit/agent.md"]},
                }
            )
        )

        otherkit_bundle = get_bundle_dir(tmp_path, "otherkit")
        otherkit_bundle.mkdir(parents=True)
        (otherkit_bundle / "kit.yaml").write_text(
            yaml.dump(
                {
                    "name": "otherkit",
                    "version": "1.0.0",
                    "sync_source": "external-source",  # Different source
                    "artifacts": {"skill": ["skills/otherkit/SKILL.md"]},
                }
            )
        )

        # Create agent file for devkit
        (claude_dir / "agents" / "devkit").mkdir(parents=True)
        (claude_dir / "agents" / "devkit" / "agent.md").write_text("# Dev Agent")

        # Run sync without kit_name argument
        runner = CliRunner()
        result = runner.invoke(sync_kit_command, [])

        assert result.exit_code == 0
        assert "Syncing 1 kit(s): devkit" in result.output
        assert "devkit" in result.output
        assert "otherkit" not in result.output

    def test_sync_all_kits_dry_run(self, tmp_path, monkeypatch):
        """Test dry-run mode when syncing all kits."""
        monkeypatch.chdir(tmp_path)

        # Create .claude directory
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        (claude_dir / "agents" / "devkit").mkdir(parents=True)
        (claude_dir / "agents" / "devkit" / "agent.md").write_text("# Dev Agent")

        # Create bundle structure
        devkit_bundle = get_bundle_dir(tmp_path, "devkit")
        devkit_bundle.mkdir(parents=True)
        (devkit_bundle / "kit.yaml").write_text(
            yaml.dump(
                {
                    "name": "devkit",
                    "version": "1.0.0",
                    "sync_source": "workstack-dev",
                    "artifacts": {"agent": ["agents/devkit/agent.md"]},
                }
            )
        )

        # Run dry-run sync without kit_name argument
        runner = CliRunner()
        result = runner.invoke(sync_kit_command, ["--dry-run"])

        assert result.exit_code == 0
        assert "Found 1 kit(s) to sync: devkit" in result.output
        assert "(DRY RUN)" in result.output
        assert "1 artifacts would be synced (no changes made)" in result.output

        # Verify files were NOT synced
        assert not (devkit_bundle / "agents" / "devkit" / "agent.md").exists()

    def test_sync_all_kits_no_dev_kits(self, tmp_path, monkeypatch):
        """Test error when no kits have sync_source: workstack-dev."""
        monkeypatch.chdir(tmp_path)

        # Create bundle structure with no dev kits
        otherkit_bundle = get_bundle_dir(tmp_path, "otherkit")
        otherkit_bundle.mkdir(parents=True)
        (otherkit_bundle / "kit.yaml").write_text(
            yaml.dump(
                {
                    "name": "otherkit",
                    "version": "1.0.0",
                    "sync_source": "external-source",
                    "artifacts": {},
                }
            )
        )

        # Run sync without kit_name argument
        runner = CliRunner()
        result = runner.invoke(sync_kit_command, [])

        assert result.exit_code == 1
        assert "No kits found with sync_source: workstack-dev" in result.output

    def test_check_mode_files_in_sync(self, temp_project, monkeypatch):
        """Test check mode when files are in sync."""
        monkeypatch.chdir(temp_project)
        runner = CliRunner()

        # First sync the files
        result = runner.invoke(sync_kit_command, ["testkit"])
        assert result.exit_code == 0

        # Now check - should succeed
        result = runner.invoke(sync_kit_command, ["testkit", "--check"])
        assert result.exit_code == 0
        assert "Checking kit: testkit" in result.output
        assert "All 2 artifact(s) are in sync" in result.output

    def test_check_mode_files_out_of_sync(self, temp_project, monkeypatch):
        """Test check mode when files are out of sync."""
        monkeypatch.chdir(temp_project)
        runner = CliRunner()

        # First sync the files
        result = runner.invoke(sync_kit_command, ["testkit"])
        assert result.exit_code == 0

        # Modify a source file
        claude_dir = temp_project / ".claude"
        agent_file = claude_dir / "agents" / "testkit" / "test-agent.md"
        agent_file.write_text("# Modified Test Agent")

        # Now check - should fail
        result = runner.invoke(sync_kit_command, ["testkit", "--check"])
        assert result.exit_code == 1
        assert "Checking kit: testkit" in result.output
        assert "content differs" in result.output
        assert "Check failed: 1 artifact(s) out of sync" in result.output

    def test_check_mode_destination_missing(self, temp_project, monkeypatch):
        """Test check mode when destination file is missing."""
        monkeypatch.chdir(temp_project)
        runner = CliRunner()

        # Run check without syncing first - destination files don't exist
        result = runner.invoke(sync_kit_command, ["testkit", "--check"])
        assert result.exit_code == 1
        assert "destination not found" in result.output
        assert "Check failed: 2 artifact(s) out of sync" in result.output

    def test_check_mode_verbose(self, temp_project, monkeypatch):
        """Test check mode with verbose output."""
        monkeypatch.chdir(temp_project)
        runner = CliRunner()

        # First sync the files
        result = runner.invoke(sync_kit_command, ["testkit"])
        assert result.exit_code == 0

        # Check with verbose flag
        result = runner.invoke(sync_kit_command, ["testkit", "--check", "--verbose"])
        assert result.exit_code == 0
        assert "Checking if artifacts are in sync..." in result.output
        assert "✓ agents/testkit/test-agent.md" in result.output
        assert "✓ skills/testkit/test-skill/SKILL.md" in result.output

    def test_check_and_dry_run_conflict(self, temp_project, monkeypatch):
        """Test that --check and --dry-run cannot be used together."""
        monkeypatch.chdir(temp_project)
        runner = CliRunner()

        result = runner.invoke(sync_kit_command, ["testkit", "--check", "--dry-run"])
        assert result.exit_code == 1
        assert "--check and --dry-run cannot be used together" in result.output

    def test_check_all_kits_in_sync(self, tmp_path, monkeypatch):
        """Test check mode for all kits when in sync."""
        monkeypatch.chdir(tmp_path)

        # Create .claude directory with artifacts
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        (claude_dir / "agents" / "devkit").mkdir(parents=True)
        (claude_dir / "agents" / "devkit" / "agent.md").write_text("# Dev Agent")

        # Create bundle structure
        devkit_bundle = get_bundle_dir(tmp_path, "devkit")
        devkit_bundle.mkdir(parents=True)
        (devkit_bundle / "kit.yaml").write_text(
            yaml.dump(
                {
                    "name": "devkit",
                    "version": "1.0.0",
                    "sync_source": "workstack-dev",
                    "artifacts": {"agent": ["agents/devkit/agent.md"]},
                }
            )
        )

        # First sync
        runner = CliRunner()
        result = runner.invoke(sync_kit_command, [])
        assert result.exit_code == 0

        # Now check all kits
        result = runner.invoke(sync_kit_command, ["--check"])
        assert result.exit_code == 0
        assert "Checking 1 kit(s): devkit" in result.output
        assert "All 1 artifact(s) are in sync" in result.output

    def test_check_all_kits_out_of_sync(self, tmp_path, monkeypatch):
        """Test check mode for all kits when out of sync."""
        monkeypatch.chdir(tmp_path)

        # Create .claude directory with artifacts
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        (claude_dir / "agents" / "devkit").mkdir(parents=True)
        (claude_dir / "agents" / "devkit" / "agent.md").write_text("# Dev Agent")

        # Create bundle structure
        devkit_bundle = get_bundle_dir(tmp_path, "devkit")
        devkit_bundle.mkdir(parents=True)
        (devkit_bundle / "kit.yaml").write_text(
            yaml.dump(
                {
                    "name": "devkit",
                    "version": "1.0.0",
                    "sync_source": "workstack-dev",
                    "artifacts": {"agent": ["agents/devkit/agent.md"]},
                }
            )
        )

        # First sync
        runner = CliRunner()
        result = runner.invoke(sync_kit_command, [])
        assert result.exit_code == 0

        # Modify source
        (claude_dir / "agents" / "devkit" / "agent.md").write_text("# Modified Dev Agent")

        # Now check all kits - should fail
        result = runner.invoke(sync_kit_command, ["--check"])
        assert result.exit_code == 1
        assert "content differs" in result.output
