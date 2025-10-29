"""Tests for list command."""

from unittest.mock import patch

from click.testing import CliRunner

from dot_agent_kit.cli import cli
from dot_agent_kit.models import ConflictPolicy, InstalledKit, ProjectConfig, RegistryEntry


def test_list_no_config() -> None:
    """Test list command when no dot-agent.toml exists."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        # Mock registry to have some available kits
        with patch("dot_agent_kit.commands.list.load_registry") as mock_registry:
            with patch("dot_agent_kit.commands.list.load_project_config") as mock_config:
                mock_config.return_value = None
                mock_registry.return_value = [
                    RegistryEntry(
                        kit_id="test-kit",
                        name="Test Kit",
                        description="A test kit",
                        source="test-kit",
                        author="tester",
                        tags=["testing"],
                    )
                ]

                result = runner.invoke(cli, ["list"])

                assert result.exit_code == 0
                assert "No kits installed" in result.output
                assert "Available kits (1)" in result.output
                assert "Test Kit [AVAILABLE]" in result.output


def test_list_with_installed_kits() -> None:
    """Test list command with installed kits."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        config = ProjectConfig(
            version="1",
            default_conflict_policy=ConflictPolicy.ERROR,
            kits={
                "test-kit": InstalledKit(
                    kit_id="test-kit",
                    version="1.0.0",
                    source="test-kit",
                    installed_at="2024-01-01T00:00:00",
                    artifacts=["agents/test.md"],
                )
            },
        )

        with patch("dot_agent_kit.commands.list.load_registry") as mock_registry:
            with patch("dot_agent_kit.commands.list.load_project_config") as mock_config:
                mock_config.return_value = config
                mock_registry.return_value = [
                    RegistryEntry(
                        kit_id="test-kit",
                        name="Test Kit",
                        description="A test kit",
                        source="test-kit",
                    ),
                    RegistryEntry(
                        kit_id="another-kit",
                        name="Another Kit",
                        description="Another test kit",
                        source="another-kit",
                    ),
                ]

                result = runner.invoke(cli, ["list"])

                assert result.exit_code == 0
                assert "Installed kits (1)" in result.output
                assert "test-kit (v1.0.0)" in result.output
                assert "Available kits (1)" in result.output
                assert "Another Kit [AVAILABLE]" in result.output
                # Installed kit should not appear in available section
                assert "Test Kit [AVAILABLE]" not in result.output


def test_list_no_available_kits() -> None:
    """Test list command when all kits are installed."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        config = ProjectConfig(
            version="1",
            default_conflict_policy=ConflictPolicy.ERROR,
            kits={
                "test-kit": InstalledKit(
                    kit_id="test-kit",
                    version="1.0.0",
                    source="test-kit",
                    installed_at="2024-01-01T00:00:00",
                    artifacts=["agents/test.md"],
                )
            },
        )

        with patch("dot_agent_kit.commands.list.load_registry") as mock_registry:
            with patch("dot_agent_kit.commands.list.load_project_config") as mock_config:
                mock_config.return_value = config
                mock_registry.return_value = [
                    RegistryEntry(
                        kit_id="test-kit",
                        name="Test Kit",
                        description="A test kit",
                        source="test-kit",
                    )
                ]

                result = runner.invoke(cli, ["list"])

                assert result.exit_code == 0
                assert "Installed kits (1)" in result.output
                assert "test-kit (v1.0.0)" in result.output
                assert "Available kits (0)" not in result.output


def test_ls_alias() -> None:
    """Test ls alias works identically to list."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        with patch("dot_agent_kit.commands.list.load_registry") as mock_registry:
            with patch("dot_agent_kit.commands.list.load_project_config") as mock_config:
                mock_config.return_value = None
                mock_registry.return_value = []

                result_list = runner.invoke(cli, ["list"])
                result_ls = runner.invoke(cli, ["ls"])

                assert result_list.exit_code == 0
                assert result_ls.exit_code == 0
                assert result_list.output == result_ls.output
