"""Pytest configuration and fixtures for dot-agent tests."""

import pytest
import yaml


@pytest.fixture
def tmp_project(tmp_path):
    """Create a temporary project directory."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Create .claude directory
    claude_dir = project_dir / ".claude"
    claude_dir.mkdir()
    (claude_dir / "commands").mkdir()
    (claude_dir / "skills").mkdir()

    return project_dir


@pytest.fixture
def sample_kit_package(tmp_path):
    """Create a sample kit package for testing."""
    package_dir = tmp_path / "test_kit"
    package_dir.mkdir()

    # Create kit.yaml
    kit_manifest = {
        "kit_id": "test-dot-agent-kit",
        "version": "1.0.0",
        "description": "Test kit",
        "artifacts": [
            {"source": "commands/test.md", "dest": "commands/test.md", "type": "command"}
        ],
    }

    with open(package_dir / "kit.yaml", "w") as f:
        yaml.safe_dump(kit_manifest, f)

    # Create artifact
    commands_dir = package_dir / "commands"
    commands_dir.mkdir()

    artifact_content = """<!-- dot-agent-kit:
kit_id: test-dot-agent-kit
version: 1.0.0
type: command
-->

# Test Command

This is a test command.
"""

    with open(commands_dir / "test.md", "w") as f:
        f.write(artifact_content)

    return package_dir


@pytest.fixture
def mock_package_installed(monkeypatch, sample_kit_package):
    """Mock a package being installed."""

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

    # Need to patch at the module level where they are used
    monkeypatch.setattr("dot_agent_kit.utils.packaging.is_package_installed", mock_is_installed)
    monkeypatch.setattr("dot_agent_kit.utils.packaging.get_package_version", mock_get_version)
    monkeypatch.setattr("dot_agent_kit.utils.packaging.get_package_path", mock_get_path)

    # Also patch at the source level where they are used
    monkeypatch.setattr("dot_agent_kit.sources.standalone.is_package_installed", mock_is_installed)
    monkeypatch.setattr("dot_agent_kit.sources.standalone.get_package_path", mock_get_path)
