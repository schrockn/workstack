"""Tests for source resolver functionality."""

from dot_agent_kit.models.registry import Registry, RegistryEntry
from dot_agent_kit.sources.resolver import SourceResolver
from dot_agent_kit.sources.standalone import StandaloneSource


def test_resolve_from_registry_uses_explicit_package_name(monkeypatch):
    """Test that registry resolver uses explicit package_name from registry entry."""
    # This simulates a real scenario where the package name differs from the GitHub repo slug
    # For example: GitHub repo "my-org/my-repo" but package is "my-org-my-repo"

    registry_entry = RegistryEntry(
        name="example-kit",
        url="https://github.com/my-org/my-repo-slug",
        description="Example kit",
        package_name="my-org-my-repo",  # Explicit package name differs from repo slug
    )

    registry = Registry(entries=[registry_entry], version="1.0.0")

    # Mock the registry loading
    def mock_load_bundled_registry():
        return registry

    monkeypatch.setattr(
        "dot_agent_kit.sources.resolver.load_bundled_registry", mock_load_bundled_registry
    )

    # Mock package availability check
    def mock_is_installed(package_name):
        # Should check for "my-org-my-repo", not "my-repo-slug"
        return package_name == "my-org-my-repo"

    monkeypatch.setattr("dot_agent_kit.utils.packaging.is_package_installed", mock_is_installed)
    monkeypatch.setattr("dot_agent_kit.sources.standalone.is_package_installed", mock_is_installed)

    resolver = SourceResolver()
    source = resolver.resolve_from_registry("example-kit")

    # This test will FAIL until we thread package_name through resolver
    # Expected: source uses "my-org-my-repo" from registry
    # Actual: source uses "my-repo-slug" derived from GitHub URL
    assert source is not None, "Should find installed package"
    assert isinstance(source, StandaloneSource)
    assert source.package_name == "my-org-my-repo", (
        f"Should use explicit package_name from registry, "
        f"not derive from URL. Got: {source.package_name}"
    )


def test_resolve_from_registry_not_installed_shows_correct_package_name(monkeypatch, capsys):
    """Test that registry resolver shows correct package name in install instructions."""
    registry_entry = RegistryEntry(
        name="example-kit",
        url="https://github.com/my-org/special-repo",
        description="Example kit",
        package_name="my-special-kit-package",  # Different from repo name
    )

    registry = Registry(entries=[registry_entry], version="1.0.0")

    def mock_load_bundled_registry():
        return registry

    monkeypatch.setattr(
        "dot_agent_kit.sources.resolver.load_bundled_registry", mock_load_bundled_registry
    )

    # Package not installed
    def mock_is_installed(package_name):
        return False

    monkeypatch.setattr("dot_agent_kit.utils.packaging.is_package_installed", mock_is_installed)
    monkeypatch.setattr("dot_agent_kit.sources.standalone.is_package_installed", mock_is_installed)

    resolver = SourceResolver()
    source = resolver.resolve_from_registry("example-kit")

    # Should return None and show install instructions
    assert source is None

    # Check that the GitHub URL is shown (for installation)
    captured = capsys.readouterr()
    assert "https://github.com/my-org/special-repo" in captured.err


def test_resolve_from_github_direct():
    """Test resolving directly from GitHub URL."""
    resolver = SourceResolver()

    # This will return None (not installed) but should use correct package name
    github_url = "https://github.com/example/my-kit"
    source = resolver.resolve_from_github(github_url)

    # Not installed, so returns None
    assert source is None


def test_resolve_from_package():
    """Test resolving from package name directly."""
    resolver = SourceResolver()
    source = resolver.resolve_from_package("test-package")

    assert isinstance(source, StandaloneSource)
    assert source.package_name == "test-package"


def test_resolve_from_registry_kit_not_found(monkeypatch, capsys):
    """Test error message when kit is not in registry."""
    registry = Registry(entries=[], version="1.0.0")

    def mock_load_bundled_registry():
        return registry

    monkeypatch.setattr(
        "dot_agent_kit.sources.resolver.load_bundled_registry", mock_load_bundled_registry
    )

    resolver = SourceResolver()
    source = resolver.resolve_from_registry("nonexistent-kit")

    assert source is None
    captured = capsys.readouterr()
    assert "Kit not found in registry" in captured.err
    assert "nonexistent-kit" in captured.err
