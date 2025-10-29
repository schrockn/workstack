"""Tests for list command."""

from pathlib import Path

from pytest import CaptureFixture

from dot_agent_kit.commands.list import _list_kits
from dot_agent_kit.io import create_default_config
from dot_agent_kit.models import ConflictPolicy, InstalledKit, KitManifest, ProjectConfig
from dot_agent_kit.sources import KitSource, ResolvedKit


class FakeKitSource(KitSource):
    """Fake kit source for testing."""

    def __init__(
        self, available_kits: list[str], manifests: dict[str, KitManifest] | None = None
    ) -> None:
        """Initialize fake source.

        Args:
            available_kits: List of kit IDs this source provides
            manifests: Optional mapping of kit_id -> manifest for artifact display
        """
        self._available_kits = available_kits
        self._manifests = manifests or {}

    def can_resolve(self, source: str) -> bool:
        """Check if kit is available."""
        return source in self._available_kits

    def resolve(self, source: str) -> ResolvedKit:
        """Resolve kit (for artifact display)."""
        if source not in self._available_kits:
            raise ValueError(f"Kit not available: {source}")

        # Create a fake manifest path for testing
        fake_path = Path(f"/fake/{source}/kit.yaml")

        return ResolvedKit(
            kit_id=source,
            source_type="fake",
            source=source,
            manifest_path=fake_path,
            artifacts_base=fake_path.parent,
        )

    def list_available(self) -> list[str]:
        """List available kits."""
        return self._available_kits


def test_list_with_bundled_kit(capsys: CaptureFixture[str]) -> None:
    """Test list command with bundled kit."""
    fake_source = FakeKitSource(available_kits=["dev-runners-da-kit"])

    _list_kits(
        show_artifacts=False,
        config=create_default_config(),
        manifests={},
        sources=[fake_source],
    )

    captured = capsys.readouterr()
    assert "dev-runners-da-kit [BUNDLED]" in captured.out
    assert "No kits available" not in captured.out


def test_list_with_installed_kits(capsys: CaptureFixture[str]) -> None:
    """Test list command with installed kits."""
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

    fake_source = FakeKitSource(available_kits=[])

    _list_kits(show_artifacts=False, config=config, manifests={}, sources=[fake_source])

    captured = capsys.readouterr()
    assert "test-kit [INSTALLED]" in captured.out


def test_list_no_kits(capsys: CaptureFixture[str]) -> None:
    """Test list command when no kits are available."""
    fake_source = FakeKitSource(available_kits=[])

    _list_kits(
        show_artifacts=False,
        config=create_default_config(),
        manifests={},
        sources=[fake_source],
    )

    captured = capsys.readouterr()
    assert "No kits available" in captured.out


def test_list_with_artifacts_flag(capsys: CaptureFixture[str]) -> None:
    """Test list command with --artifacts flag shows artifact details."""
    manifest = KitManifest(
        name="test-kit",
        version="1.0.0",
        description="A test kit",
        artifacts={
            "agent": ["agents/pytest-runner.md", "agents/ruff-runner.md"],
            "command": ["commands/test-cmd.md"],
        },
    )

    fake_source = FakeKitSource(available_kits=["test-kit"], manifests={"test-kit": manifest})

    _list_kits(
        show_artifacts=True,
        config=create_default_config(),
        manifests={"test-kit": manifest},
        sources=[fake_source],
    )

    captured = capsys.readouterr()
    assert "test-kit [BUNDLED]" in captured.out
    assert "agent: pytest-runner" in captured.out
    assert "agent: ruff-runner" in captured.out
    assert "command: test-cmd" in captured.out


def test_list_bundled_and_installed(capsys: CaptureFixture[str]) -> None:
    """Test list command shows both bundled and installed kits."""
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

    fake_source = FakeKitSource(available_kits=["bundled-kit"])

    _list_kits(show_artifacts=False, config=config, manifests={}, sources=[fake_source])

    captured = capsys.readouterr()
    assert "bundled-kit [BUNDLED]" in captured.out
    assert "installed-kit [INSTALLED]" in captured.out
