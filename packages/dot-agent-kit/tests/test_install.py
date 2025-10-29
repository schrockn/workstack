"""Tests for kit installation."""

from pathlib import Path

import pytest

from dot_agent_kit.models import ConflictPolicy
from dot_agent_kit.operations.install import install_kit
from dot_agent_kit.sources import ResolvedKit


def test_install_kit_basic(tmp_project: Path) -> None:
    """Test basic kit installation."""
    # Create mock kit
    kit_dir = tmp_project / "mock_kit"
    kit_dir.mkdir()

    manifest = kit_dir / "kit.yaml"
    manifest.write_text(
        "name: test-kit\n"
        "version: 1.0.0\n"
        "description: Test\n"
        "artifacts:\n"
        "  agent:\n"
        "    - agents/test-agent.md\n",
        encoding="utf-8",
    )

    agents_dir = kit_dir / "agents"
    agents_dir.mkdir()
    (agents_dir / "test-agent.md").write_text("# Test Agent", encoding="utf-8")

    # Mock resolution
    resolved = ResolvedKit(
        kit_id="test-kit",
        source_type="package",
        source="test-kit",
        manifest_path=manifest,
        artifacts_base=kit_dir,
    )

    # Install
    installed = install_kit(resolved, tmp_project)

    # Verify
    assert installed.kit_id == "test-kit"
    assert installed.version == "1.0.0"
    assert len(installed.artifacts) == 1

    agent_path = tmp_project / ".claude" / "agents" / "test-agent.md"
    assert agent_path.exists()

    content = agent_path.read_text(encoding="utf-8")
    assert "dot-agent-kit:" in content
    assert "# Test Agent" in content


def test_install_kit_conflict(tmp_project: Path) -> None:
    """Test installation fails on conflict with ERROR policy."""
    # Create existing artifact
    claude_dir = tmp_project / ".claude"
    claude_dir.mkdir()
    agents_dir = claude_dir / "agents"
    agents_dir.mkdir()
    (agents_dir / "test-agent.md").write_text("Existing", encoding="utf-8")

    # Create mock kit
    kit_dir = tmp_project / "mock_kit"
    kit_dir.mkdir()

    manifest = kit_dir / "kit.yaml"
    manifest.write_text(
        "name: test-kit\n"
        "version: 1.0.0\n"
        "description: Test\n"
        "artifacts:\n"
        "  agent:\n"
        "    - agents/test-agent.md\n",
        encoding="utf-8",
    )

    agents_source = kit_dir / "agents"
    agents_source.mkdir()
    (agents_source / "test-agent.md").write_text("# New Agent", encoding="utf-8")

    resolved = ResolvedKit(
        kit_id="test-kit",
        source_type="package",
        source="test-kit",
        manifest_path=manifest,
        artifacts_base=kit_dir,
    )

    # Try to install - should fail with ERROR policy
    with pytest.raises(FileExistsError, match="Artifact already exists"):
        install_kit(resolved, tmp_project, ConflictPolicy.ERROR)


def test_install_kit_creates_directories(tmp_project: Path) -> None:
    """Test installation creates .claude directory structure."""
    # Create mock kit
    kit_dir = tmp_project / "mock_kit"
    kit_dir.mkdir()

    manifest = kit_dir / "kit.yaml"
    manifest.write_text(
        "name: test-kit\n"
        "version: 1.0.0\n"
        "description: Test\n"
        "artifacts:\n"
        "  command:\n"
        "    - commands/test-command.md\n",
        encoding="utf-8",
    )

    commands_dir = kit_dir / "commands"
    commands_dir.mkdir()
    (commands_dir / "test-command.md").write_text("# Test Command", encoding="utf-8")

    resolved = ResolvedKit(
        kit_id="test-kit",
        source_type="package",
        source="test-kit",
        manifest_path=manifest,
        artifacts_base=kit_dir,
    )

    # Install
    install_kit(resolved, tmp_project)

    # Verify directories created
    assert (tmp_project / ".claude").exists()
    assert (tmp_project / ".claude" / "commands").exists()
    assert (tmp_project / ".claude" / "commands" / "test-command.md").exists()
