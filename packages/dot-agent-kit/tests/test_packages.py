"""Tests for the package system."""

from pathlib import Path
from tempfile import TemporaryDirectory

from dot_agent_kit.packages.manager import PackageManager
from dot_agent_kit.packages.registry import ToolRegistry


def test_package_manager_discover_empty():
    """Test package discovery in empty directory."""
    with TemporaryDirectory() as tmpdir:
        agent_dir = Path(tmpdir) / ".agent"
        agent_dir.mkdir()

        manager = PackageManager(agent_dir)
        packages = manager.discover_packages()
        assert packages == {}


def test_package_manager_discover_packages():
    """Test package discovery with packages."""
    with TemporaryDirectory() as tmpdir:
        agent_dir = Path(tmpdir) / ".agent"
        packages_dir = agent_dir / "packages"
        packages_dir.mkdir(parents=True)

        # Create a simple package
        pkg_dir = packages_dir / "test_package"
        pkg_dir.mkdir()
        (pkg_dir / "README.md").write_text("# Test Package", encoding="utf-8")

        # Create a tool package
        tools_dir = packages_dir / "tools"
        tools_dir.mkdir()
        gt_dir = tools_dir / "gt"
        gt_dir.mkdir()
        (gt_dir / "gt.md").write_text("# GT Tool", encoding="utf-8")

        manager = PackageManager(agent_dir)
        packages = manager.discover_packages()

        assert "test_package" in packages
        assert "tools/gt" in packages
        assert packages["test_package"].namespace is None
        assert packages["tools/gt"].namespace == "tools"


def test_tool_registry_initialization():
    """Test tool registry initialization."""
    with TemporaryDirectory() as tmpdir:
        agent_dir = Path(tmpdir) / ".agent"
        agent_dir.mkdir()

        registry = ToolRegistry(agent_dir)
        assert registry.agent_dir == agent_dir


def test_tool_registry_detect_tool_mention():
    """Test tool mention detection."""
    with TemporaryDirectory() as tmpdir:
        agent_dir = Path(tmpdir) / ".agent"
        agent_dir.mkdir()

        registry = ToolRegistry(agent_dir)
        registry.register_cli_mapping("gt", "tools/gt")
        registry.register_cli_mapping("gh", "tools/gh")

        detected = registry.detect_tool_mention("I used gt to create a stack")
        assert "gt" in detected

        detected = registry.detect_tool_mention("Use gh pr create to make a PR")
        assert "gh" in detected

        detected = registry.detect_tool_mention("This has no tool mentions")
        assert len(detected) == 0
