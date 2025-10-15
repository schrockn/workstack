"""Tests for link-dot-agent-resources command."""

import importlib.util
import sys
from pathlib import Path

from click.testing import CliRunner

from workstack_dev.cli import cli

# Import the script module dynamically since it's a PEP 723 script
_script_dir = (
    Path(__file__).parent.parent / "src" / "workstack_dev" / "commands" / "link_dot_agent_resources"
)
sys.path.insert(0, str(_script_dir))

spec = importlib.util.spec_from_file_location(
    "link_dot_agent_resources_script", _script_dir / "script.py"
)
if spec is None or spec.loader is None:
    raise ImportError("Failed to load script module")
script = importlib.util.module_from_spec(spec)
spec.loader.exec_module(script)


def test_get_symlink_status_missing() -> None:
    """Test status when file doesn't exist."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        symlink_path = Path.cwd() / "missing.md"
        target_path = Path.cwd() / "target.md"
        target_path.write_text("content", encoding="utf-8")

        status = script.get_symlink_status(symlink_path, target_path)
        assert status == "missing"


def test_get_symlink_status_regular_file() -> None:
    """Test status when path is a regular file."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        symlink_path = Path.cwd() / "file.md"
        symlink_path.write_text("content", encoding="utf-8")
        target_path = Path.cwd() / "target.md"
        target_path.write_text("content", encoding="utf-8")

        status = script.get_symlink_status(symlink_path, target_path)
        assert status == "regular_file"


def test_get_symlink_status_valid_symlink() -> None:
    """Test status when symlink is valid."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        target_path = Path.cwd() / "target.md"
        target_path.write_text("content", encoding="utf-8")
        symlink_path = Path.cwd() / "link.md"
        symlink_path.symlink_to("target.md")

        status = script.get_symlink_status(symlink_path, target_path)
        assert status == "symlink_valid"


def test_get_symlink_status_broken_symlink() -> None:
    """Test status when symlink is broken."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        symlink_path = Path.cwd() / "link.md"
        symlink_path.symlink_to("nonexistent.md")
        target_path = Path.cwd() / "target.md"

        status = script.get_symlink_status(symlink_path, target_path)
        assert status == "symlink_broken"


def test_create_symlink_new() -> None:
    """Test creating a new symlink."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        target_path = Path.cwd() / "target.md"
        target_path.write_text("content", encoding="utf-8")
        symlink_path = Path.cwd() / "link.md"

        script.create_symlink(symlink_path, target_path, force=False, dry_run=False)

        assert symlink_path.is_symlink()
        assert symlink_path.exists()
        assert symlink_path.read_text(encoding="utf-8") == "content"


def test_create_symlink_dry_run() -> None:
    """Test creating symlink in dry-run mode."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        target_path = Path.cwd() / "target.md"
        target_path.write_text("content", encoding="utf-8")
        symlink_path = Path.cwd() / "link.md"

        script.create_symlink(symlink_path, target_path, force=False, dry_run=True)

        assert not symlink_path.exists()


def test_create_symlink_replaces_matching_regular_file() -> None:
    """Test replacing regular file with matching content."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        target_path = Path.cwd() / "target.md"
        target_path.write_text("content", encoding="utf-8")
        symlink_path = Path.cwd() / "link.md"
        symlink_path.write_text("content", encoding="utf-8")

        script.create_symlink(symlink_path, target_path, force=False, dry_run=False)

        assert symlink_path.is_symlink()
        assert symlink_path.read_text(encoding="utf-8") == "content"


def test_create_symlink_fails_on_content_mismatch() -> None:
    """Test failure when regular file has different content."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        target_path = Path.cwd() / "target.md"
        target_path.write_text("target content", encoding="utf-8")
        symlink_path = Path.cwd() / "link.md"
        symlink_path.write_text("different content", encoding="utf-8")

        try:
            script.create_symlink(symlink_path, target_path, force=False, dry_run=False)
            raise AssertionError("Should have raised SystemExit")
        except SystemExit as e:
            assert e.code == 1


def test_create_symlink_force_overwrites_different_content() -> None:
    """Test force mode overwrites different content."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        target_path = Path.cwd() / "target.md"
        target_path.write_text("target content", encoding="utf-8")
        symlink_path = Path.cwd() / "link.md"
        symlink_path.write_text("different content", encoding="utf-8")

        script.create_symlink(symlink_path, target_path, force=True, dry_run=False)

        assert symlink_path.is_symlink()
        assert symlink_path.read_text(encoding="utf-8") == "target content"


def test_create_symlink_skips_valid_symlink() -> None:
    """Test skipping when symlink is already valid."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        target_path = Path.cwd() / "target.md"
        target_path.write_text("content", encoding="utf-8")
        symlink_path = Path.cwd() / "link.md"
        symlink_path.symlink_to("target.md")

        # Should not raise
        script.create_symlink(symlink_path, target_path, force=False, dry_run=False)

        assert symlink_path.is_symlink()


def test_create_symlink_replaces_broken_symlink() -> None:
    """Test replacing broken symlink."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        target_path = Path.cwd() / "target.md"
        target_path.write_text("content", encoding="utf-8")
        symlink_path = Path.cwd() / "link.md"
        symlink_path.symlink_to("nonexistent.md")

        script.create_symlink(symlink_path, target_path, force=False, dry_run=False)

        assert symlink_path.is_symlink()
        assert symlink_path.exists()
        assert symlink_path.read_text(encoding="utf-8") == "content"


def test_remove_symlink_converts_to_regular_file() -> None:
    """Test removing symlink and restoring content."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        target_path = Path.cwd() / "target.md"
        target_path.write_text("content", encoding="utf-8")
        symlink_path = Path.cwd() / "link.md"
        symlink_path.symlink_to("target.md")

        script.remove_symlink(symlink_path, dry_run=False)

        assert not symlink_path.is_symlink()
        assert symlink_path.is_file()
        assert symlink_path.read_text(encoding="utf-8") == "content"


def test_remove_symlink_dry_run() -> None:
    """Test removing symlink in dry-run mode."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        target_path = Path.cwd() / "target.md"
        target_path.write_text("content", encoding="utf-8")
        symlink_path = Path.cwd() / "link.md"
        symlink_path.symlink_to("target.md")

        script.remove_symlink(symlink_path, dry_run=True)

        assert symlink_path.is_symlink()


def test_remove_symlink_skips_regular_file() -> None:
    """Test skipping regular file."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        symlink_path = Path.cwd() / "file.md"
        symlink_path.write_text("content", encoding="utf-8")

        # Should not raise
        script.remove_symlink(symlink_path, dry_run=False)

        assert not symlink_path.is_symlink()
        assert symlink_path.is_file()


def test_remove_symlink_removes_broken_symlink() -> None:
    """Test removing broken symlink."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        symlink_path = Path.cwd() / "link.md"
        symlink_path.symlink_to("nonexistent.md")

        script.remove_symlink(symlink_path, dry_run=False)

        assert not symlink_path.exists()


def test_verify_symlinks_all_valid() -> None:
    """Test verify with all valid symlinks."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        target1 = Path.cwd() / "target1.md"
        target1.write_text("content1", encoding="utf-8")
        link1 = Path.cwd() / "link1.md"
        link1.symlink_to("target1.md")

        target2 = Path.cwd() / "target2.md"
        target2.write_text("content2", encoding="utf-8")
        link2 = Path.cwd() / "link2.md"
        link2.symlink_to("target2.md")

        mapping = {link1: target1, link2: target2}
        issues = script.verify_symlinks(mapping)

        assert len(issues) == 0


def test_verify_symlinks_with_issues() -> None:
    """Test verify with various issues."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Valid symlink
        target1 = Path.cwd() / "target1.md"
        target1.write_text("content1", encoding="utf-8")
        link1 = Path.cwd() / "link1.md"
        link1.symlink_to("target1.md")

        # Regular file
        link2 = Path.cwd() / "link2.md"
        link2.write_text("content2", encoding="utf-8")
        target2 = Path.cwd() / "target2.md"

        # Broken symlink
        link3 = Path.cwd() / "link3.md"
        link3.symlink_to("nonexistent.md")
        target3 = Path.cwd() / "target3.md"

        # Missing
        link4 = Path.cwd() / "link4.md"
        target4 = Path.cwd() / "target4.md"

        mapping = {link1: target1, link2: target2, link3: target3, link4: target4}
        issues = script.verify_symlinks(mapping)

        assert len(issues) == 3
        assert any("link2.md" in issue and "regular file" in issue for issue in issues)
        assert any("link3.md" in issue and "broken" in issue for issue in issues)
        assert any("link4.md" in issue and "missing" in issue for issue in issues)


def test_get_tool_files_mapping() -> None:
    """Test getting tool files mapping."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        repo_root = Path.cwd()

        # Create git repo
        (repo_root / ".git").mkdir()

        # Create package structure
        package_tools = (
            repo_root
            / "packages"
            / "dot-agent-kit"
            / "src"
            / "dot_agent_kit"
            / "resources"
            / "tools"
        )
        package_tools.mkdir(parents=True)
        (package_tools / "gt.md").write_text("gt content", encoding="utf-8")
        (package_tools / "gh.md").write_text("gh content", encoding="utf-8")
        (package_tools / "workstack.md").write_text("workstack content", encoding="utf-8")

        # Create .agent/tools directory
        agent_tools = repo_root / ".agent" / "tools"
        agent_tools.mkdir(parents=True)

        mapping = script.get_tool_files_mapping(repo_root)

        assert len(mapping) == 3
        assert (agent_tools / "gt.md") in mapping
        assert (agent_tools / "gh.md") in mapping
        assert (agent_tools / "workstack.md") in mapping
        assert mapping[agent_tools / "gt.md"] == package_tools / "gt.md"


def test_integration_create_and_verify() -> None:
    """Integration test: create symlinks and verify."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        repo_root = Path.cwd()

        # Create git repo
        (repo_root / ".git").mkdir()

        # Create package structure
        package_tools = (
            repo_root
            / "packages"
            / "dot-agent-kit"
            / "src"
            / "dot_agent_kit"
            / "resources"
            / "tools"
        )
        package_tools.mkdir(parents=True)
        (package_tools / "gt.md").write_text("gt content", encoding="utf-8")
        (package_tools / "gh.md").write_text("gh content", encoding="utf-8")

        # Create .agent/tools with regular files
        agent_tools = repo_root / ".agent" / "tools"
        agent_tools.mkdir(parents=True)
        (agent_tools / "gt.md").write_text("gt content", encoding="utf-8")
        (agent_tools / "gh.md").write_text("gh content", encoding="utf-8")

        # Get mapping
        mapping = script.get_tool_files_mapping(repo_root)

        # Create symlinks
        for symlink_path, target_path in mapping.items():
            script.create_symlink(symlink_path, target_path, force=False, dry_run=False)

        # Verify all valid
        issues = script.verify_symlinks(mapping)
        assert len(issues) == 0

        # Check symlinks work
        assert (agent_tools / "gt.md").is_symlink()
        assert (agent_tools / "gt.md").read_text(encoding="utf-8") == "gt content"


def test_integration_create_remove_create() -> None:
    """Integration test: create, remove, create cycle."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        repo_root = Path.cwd()

        # Create git repo and structure
        (repo_root / ".git").mkdir()
        package_tools = (
            repo_root
            / "packages"
            / "dot-agent-kit"
            / "src"
            / "dot_agent_kit"
            / "resources"
            / "tools"
        )
        package_tools.mkdir(parents=True)
        (package_tools / "gt.md").write_text("gt content", encoding="utf-8")

        agent_tools = repo_root / ".agent" / "tools"
        agent_tools.mkdir(parents=True)
        (agent_tools / "gt.md").write_text("gt content", encoding="utf-8")

        mapping = script.get_tool_files_mapping(repo_root)

        # Create symlinks
        for symlink_path, target_path in mapping.items():
            script.create_symlink(symlink_path, target_path, force=False, dry_run=False)

        assert (agent_tools / "gt.md").is_symlink()

        # Remove symlinks
        for symlink_path in mapping.keys():
            script.remove_symlink(symlink_path, dry_run=False)

        assert not (agent_tools / "gt.md").is_symlink()
        assert (agent_tools / "gt.md").is_file()
        assert (agent_tools / "gt.md").read_text(encoding="utf-8") == "gt content"

        # Create again
        for symlink_path, target_path in mapping.items():
            script.create_symlink(symlink_path, target_path, force=False, dry_run=False)

        assert (agent_tools / "gt.md").is_symlink()


def test_cli_help() -> None:
    """Test link-dot-agent-resources help output."""
    runner = CliRunner()
    result = runner.invoke(cli, ["link-dot-agent-resources", "--help"])
    assert result.exit_code == 0
    assert "Manage symlinks" in result.output
    assert "--create" in result.output
    assert "--remove" in result.output
    assert "--verify" in result.output
