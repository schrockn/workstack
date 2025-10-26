import tempfile
from pathlib import Path

from mdstack.models import Scope
from mdstack.package_detection import detect_package_root


def test_detect_package_root_with_pyproject_toml():
    """Test detection when pyproject.toml exists with source and test dirs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create pyproject.toml
        pyproject_content = """
[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
"""
        (tmpdir_path / "pyproject.toml").write_text(pyproject_content, encoding="utf-8")

        # Create directories
        (tmpdir_path / "src").mkdir()
        (tmpdir_path / "tests").mkdir()
        (tmpdir_path / "CLAUDE.md").write_text("# Test", encoding="utf-8")

        # Create scope
        scope = Scope.create(
            path=tmpdir_path,
            claude_md_path=tmpdir_path / "CLAUDE.md",
            mdstack_dir=tmpdir_path / ".mdstack",
        )

        # Detect package root
        layout = detect_package_root(scope.path)

        assert layout is not None
        assert len(layout.source_dirs) == 1
        assert layout.source_dirs[0] == tmpdir_path / "src"
        assert len(layout.test_dirs) == 1
        assert layout.test_dirs[0] == tmpdir_path / "tests"


def test_detect_package_root_defaults_to_src_tests():
    """Test that defaults to src/ and tests/ when not specified."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create minimal pyproject.toml (no tool sections)
        pyproject_content = """
[project]
name = "test-package"
version = "0.1.0"
"""
        (tmpdir_path / "pyproject.toml").write_text(pyproject_content, encoding="utf-8")

        # Create directories
        (tmpdir_path / "src").mkdir()
        (tmpdir_path / "tests").mkdir()
        (tmpdir_path / "CLAUDE.md").write_text("# Test", encoding="utf-8")

        # Create scope
        scope = Scope.create(
            path=tmpdir_path,
            claude_md_path=tmpdir_path / "CLAUDE.md",
            mdstack_dir=tmpdir_path / ".mdstack",
        )

        # Detect package root
        layout = detect_package_root(scope.path)

        assert layout is not None
        assert len(layout.source_dirs) == 1
        assert layout.source_dirs[0] == tmpdir_path / "src"
        assert len(layout.test_dirs) == 1
        assert layout.test_dirs[0] == tmpdir_path / "tests"


def test_detect_package_root_no_pyproject():
    """Test that returns None when no pyproject.toml."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create CLAUDE.md but no pyproject.toml
        (tmpdir_path / "CLAUDE.md").write_text("# Test", encoding="utf-8")

        # Create scope
        scope = Scope.create(
            path=tmpdir_path,
            claude_md_path=tmpdir_path / "CLAUDE.md",
            mdstack_dir=tmpdir_path / ".mdstack",
        )

        # Detect package root
        layout = detect_package_root(scope.path)

        assert layout is None


def test_detect_package_root_directories_dont_exist():
    """Test that filters out non-existent directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create pyproject.toml specifying src and tests
        pyproject_content = """
[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
"""
        (tmpdir_path / "pyproject.toml").write_text(pyproject_content, encoding="utf-8")

        # Don't create directories
        (tmpdir_path / "CLAUDE.md").write_text("# Test", encoding="utf-8")

        # Create scope
        scope = Scope.create(
            path=tmpdir_path,
            claude_md_path=tmpdir_path / "CLAUDE.md",
            mdstack_dir=tmpdir_path / ".mdstack",
        )

        # Detect package root
        layout = detect_package_root(scope.path)

        # Should return None because no directories exist
        assert layout is None


def test_detect_package_root_only_src_exists():
    """Test that works when only src/ exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create pyproject.toml
        pyproject_content = """
[tool.setuptools.packages.find]
where = ["src"]
"""
        (tmpdir_path / "pyproject.toml").write_text(pyproject_content, encoding="utf-8")

        # Create only src directory
        (tmpdir_path / "src").mkdir()
        (tmpdir_path / "CLAUDE.md").write_text("# Test", encoding="utf-8")

        # Create scope
        scope = Scope.create(
            path=tmpdir_path,
            claude_md_path=tmpdir_path / "CLAUDE.md",
            mdstack_dir=tmpdir_path / ".mdstack",
        )

        # Detect package root
        layout = detect_package_root(scope.path)

        assert layout is not None
        assert len(layout.source_dirs) == 1
        assert layout.source_dirs[0] == tmpdir_path / "src"
        assert len(layout.test_dirs) == 0  # No test directory


def test_detect_package_root_multiple_source_dirs():
    """Test handling of multiple source directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create pyproject.toml with multiple source dirs
        pyproject_content = """
[tool.setuptools.packages.find]
where = ["src", "lib"]
"""
        (tmpdir_path / "pyproject.toml").write_text(pyproject_content, encoding="utf-8")

        # Create directories
        (tmpdir_path / "src").mkdir()
        (tmpdir_path / "lib").mkdir()
        (tmpdir_path / "CLAUDE.md").write_text("# Test", encoding="utf-8")

        # Create scope
        scope = Scope.create(
            path=tmpdir_path,
            claude_md_path=tmpdir_path / "CLAUDE.md",
            mdstack_dir=tmpdir_path / ".mdstack",
        )

        # Detect package root
        layout = detect_package_root(scope.path)

        assert layout is not None
        assert len(layout.source_dirs) == 2
        assert tmpdir_path / "src" in layout.source_dirs
        assert tmpdir_path / "lib" in layout.source_dirs
