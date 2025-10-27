"""Tests for package introspection utilities."""

from unittest.mock import MagicMock


from dot_agent_kit.utils.packaging import (
    get_package_path,
    get_package_version,
    is_package_installed,
)


def test_get_package_path_with_data_only_package(monkeypatch, tmp_path):
    """Test that get_package_path works with data-only packages (no __init__.py)."""
    # This simulates packages like dev-runners-da-kit that only ship data files
    # via force-include, with no Python modules (packages = [])

    package_name = "dev-runners-da-kit"
    package_root = tmp_path / "dev_runners_da_kit_data"
    package_root.mkdir()

    # Create kit.yaml (the primary artifact)
    (package_root / "kit.yaml").write_text("kit_id: dev-runners\nversion: 0.1.0\n")

    # Create agents directory
    agents_dir = package_root / "agents"
    agents_dir.mkdir()
    (agents_dir / "pytest-runner.md").write_text("# Pytest Runner\n")

    # Mock importlib.util.find_spec to return None (no importable module)
    def mock_find_spec(name):
        return None

    monkeypatch.setattr("importlib.util.find_spec", mock_find_spec)

    # Mock importlib.metadata.distribution to return a distribution with only data files
    mock_dist = MagicMock()
    mock_dist.files = [
        MagicMock(name="kit.yaml", locate=lambda: package_root / "kit.yaml"),
        MagicMock(
            name="agents/pytest-runner.md",
            locate=lambda: package_root / "agents" / "pytest-runner.md",
        ),
    ]

    def mock_distribution(name):
        if name == package_name:
            return mock_dist
        raise ImportError(f"No distribution found for {name}")

    monkeypatch.setattr("importlib.metadata.distribution", mock_distribution)

    # Call get_package_path
    result = get_package_path(package_name)

    # This test will FAIL until we add fallback logic for data-only packages
    # Expected: returns package_root (parent of kit.yaml)
    # Actual: returns None (no __init__.py found)
    assert result is not None, "get_package_path should support data-only packages"
    assert result == package_root
    assert (result / "kit.yaml").exists()


def test_get_package_path_with_traditional_package(monkeypatch, tmp_path):
    """Test that get_package_path still works with traditional Python packages."""
    package_name = "traditional-kit"
    package_root = tmp_path / "traditional_kit"
    package_root.mkdir()
    (package_root / "__init__.py").write_text("# Package init")
    (package_root / "kit.yaml").write_text("kit_id: traditional\n")

    # Mock importlib.util.find_spec to return a valid spec
    mock_spec = MagicMock()
    mock_spec.origin = str(package_root / "__init__.py")

    def mock_find_spec(name):
        if name == "traditional_kit":
            return mock_spec
        return None

    monkeypatch.setattr("importlib.util.find_spec", mock_find_spec)

    result = get_package_path(package_name)
    assert result == package_root


def test_get_package_path_with_no_kit_yaml(monkeypatch, tmp_path):
    """Test that get_package_path returns None when kit.yaml is not found."""
    package_name = "no-kit-yaml"

    # Mock importlib.util.find_spec to return None
    monkeypatch.setattr("importlib.util.find_spec", lambda name: None)

    # Mock distribution with no kit.yaml
    mock_dist = MagicMock()
    mock_dist.files = [
        MagicMock(name="README.md", locate=lambda: tmp_path / "README.md"),
    ]

    def mock_distribution(name):
        if name == package_name:
            return mock_dist
        raise ImportError(f"No distribution found for {name}")

    monkeypatch.setattr("importlib.metadata.distribution", mock_distribution)

    result = get_package_path(package_name)
    assert result is None


def test_is_package_installed():
    """Test checking if a package is installed."""
    # This is a basic smoke test - we can't test against real packages
    # without making tests dependent on environment
    result = is_package_installed("definitely-not-installed-package-xyz")
    assert result is False


def test_get_package_version_not_installed():
    """Test getting version of non-installed package."""
    result = get_package_version("definitely-not-installed-package-xyz")
    assert result is None
