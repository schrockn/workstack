"""Tests for list command."""

from unittest.mock import patch

from click.testing import CliRunner

from dot_agent_kit.cli import cli
from dot_agent_kit.models import ConflictPolicy, InstalledKit, KitManifest, ProjectConfig


def test_list_with_bundled_kit() -> None:
    """Test list command with bundled kit."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        with patch("dot_agent_kit.commands.list._get_bundled_kits") as mock_bundled:
            with patch("dot_agent_kit.commands.list.load_project_config") as mock_config:
                mock_config.return_value = None
                mock_bundled.return_value = ["dev-runners-da-kit"]

                result = runner.invoke(cli, ["list"])

                assert result.exit_code == 0
                assert "dev-runners-da-kit [BUNDLED]" in result.output
                assert "No kits installed" not in result.output


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

        with patch("dot_agent_kit.commands.list._get_bundled_kits") as mock_bundled:
            with patch("dot_agent_kit.commands.list.load_project_config") as mock_config:
                mock_config.return_value = config
                mock_bundled.return_value = []

                result = runner.invoke(cli, ["list"])

                assert result.exit_code == 0
                assert "test-kit [INSTALLED]" in result.output


def test_list_no_kits() -> None:
    """Test list command when no kits are available."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        with patch("dot_agent_kit.commands.list._get_bundled_kits") as mock_bundled:
            with patch("dot_agent_kit.commands.list.load_project_config") as mock_config:
                mock_config.return_value = None
                mock_bundled.return_value = []

                result = runner.invoke(cli, ["list"])

                assert result.exit_code == 0
                assert "No kits available" in result.output


def test_ls_alias() -> None:
    """Test ls alias works identically to list."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        with patch("dot_agent_kit.commands.list._get_bundled_kits") as mock_bundled:
            with patch("dot_agent_kit.commands.list.load_project_config") as mock_config:
                mock_config.return_value = None
                mock_bundled.return_value = []

                result_list = runner.invoke(cli, ["list"])
                result_ls = runner.invoke(cli, ["ls"])

                assert result_list.exit_code == 0
                assert result_ls.exit_code == 0
                assert result_list.output == result_ls.output


def test_list_with_artifacts_flag() -> None:
    """Test list command with --artifacts flag shows artifact details."""
    from pathlib import Path
    from unittest.mock import MagicMock

    runner = CliRunner()

    with runner.isolated_filesystem():
        manifest = KitManifest(
            name="test-kit",
            version="1.0.0",
            description="A test kit",
            artifacts={
                "agent": ["agents/pytest-runner.md", "agents/ruff-runner.md"],
                "command": ["commands/test-cmd.md"],
            },
        )

        mock_path = MagicMock(spec=Path)

        with patch("dot_agent_kit.commands.list._get_bundled_kits") as mock_bundled:
            with patch("dot_agent_kit.commands.list.load_project_config") as mock_config:
                with patch("dot_agent_kit.commands.list.load_kit_manifest") as mock_manifest:
                    with patch(
                        "dot_agent_kit.commands.list._get_bundled_manifest_path"
                    ) as mock_get_path:
                        mock_config.return_value = None
                        mock_bundled.return_value = ["test-kit"]
                        mock_manifest.return_value = manifest
                        mock_get_path.return_value = mock_path

                        result = runner.invoke(cli, ["list", "--artifacts"])

                        assert result.exit_code == 0
                        assert "test-kit [BUNDLED]" in result.output
                        assert "agent: pytest-runner" in result.output
                        assert "agent: ruff-runner" in result.output
                        assert "command: test-cmd" in result.output


def test_list_bundled_and_installed() -> None:
    """Test list command shows both bundled and installed kits."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        config = ProjectConfig(
            version="1",
            default_conflict_policy=ConflictPolicy.ERROR,
            kits={
                "installed-kit": InstalledKit(
                    kit_id="installed-kit",
                    version="1.0.0",
                    source="installed-kit",
                    installed_at="2024-01-01T00:00:00",
                    artifacts=["agents/test.md"],
                )
            },
        )

        with patch("dot_agent_kit.commands.list._get_bundled_kits") as mock_bundled:
            with patch("dot_agent_kit.commands.list.load_project_config") as mock_config:
                mock_config.return_value = config
                mock_bundled.return_value = ["bundled-kit"]

                result = runner.invoke(cli, ["list"])

                assert result.exit_code == 0
                assert "bundled-kit [BUNDLED]" in result.output
                assert "installed-kit [INSTALLED]" in result.output
