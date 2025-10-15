"""Tests for create-agents-symlinks command."""

from pathlib import Path

from click.testing import CliRunner

from workstack_dev.cli import cli
from workstack_dev.commands.create_agents_symlinks import command


def test_is_git_repo_root_with_git_dir() -> None:
    """Test is_git_repo_root returns True when .git exists."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a .git directory
        git_dir = Path.cwd() / ".git"
        git_dir.mkdir()

        assert command.is_git_repo_root(Path.cwd())


def test_is_git_repo_root_without_git_dir() -> None:
    """Test is_git_repo_root returns False when .git doesn't exist."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        assert not command.is_git_repo_root(Path.cwd())


def test_is_git_repo_root_with_git_file() -> None:
    """Test is_git_repo_root returns False when .git is a file."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create .git as a file (not a directory)
        git_file = Path.cwd() / ".git"
        git_file.write_text("gitdir: ../somewhere", encoding="utf-8")

        assert not command.is_git_repo_root(Path.cwd())


def test_create_symlink_for_claude_md_creates_new_symlink() -> None:
    """Test creating a new symlink when AGENTS.md doesn't exist."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a CLAUDE.md file
        claude_md = Path.cwd() / "CLAUDE.md"
        claude_md.write_text("# Project instructions", encoding="utf-8")

        # Create symlink
        status = command.create_symlink_for_claude_md(claude_md, dry_run=False)

        assert status == "created"
        agents_md = Path.cwd() / "AGENTS.md"
        assert agents_md.exists()
        assert agents_md.is_symlink()
        assert agents_md.readlink() == Path("CLAUDE.md")


def test_create_symlink_for_claude_md_dry_run() -> None:
    """Test dry run mode doesn't create symlink."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a CLAUDE.md file
        claude_md = Path.cwd() / "CLAUDE.md"
        claude_md.write_text("# Project instructions", encoding="utf-8")

        # Try to create symlink in dry-run mode
        status = command.create_symlink_for_claude_md(claude_md, dry_run=True)

        assert status == "created"
        agents_md = Path.cwd() / "AGENTS.md"
        assert not agents_md.exists()


def test_create_symlink_for_claude_md_skips_correct_symlink() -> None:
    """Test skipping when AGENTS.md already points to CLAUDE.md."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a CLAUDE.md file
        claude_md = Path.cwd() / "CLAUDE.md"
        claude_md.write_text("# Project instructions", encoding="utf-8")

        # Create correct symlink
        agents_md = Path.cwd() / "AGENTS.md"
        agents_md.symlink_to("CLAUDE.md")

        # Should skip
        status = command.create_symlink_for_claude_md(claude_md, dry_run=False)

        assert status == "skipped_correct"
        assert agents_md.is_symlink()
        assert agents_md.readlink() == Path("CLAUDE.md")


def test_create_symlink_for_claude_md_skips_regular_file() -> None:
    """Test skipping when AGENTS.md exists as regular file."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a CLAUDE.md file
        claude_md = Path.cwd() / "CLAUDE.md"
        claude_md.write_text("# Project instructions", encoding="utf-8")

        # Create AGENTS.md as regular file
        agents_md = Path.cwd() / "AGENTS.md"
        agents_md.write_text("# Different content", encoding="utf-8")

        # Should skip
        status = command.create_symlink_for_claude_md(claude_md, dry_run=False)

        assert status == "skipped_exists"
        assert agents_md.exists()
        assert not agents_md.is_symlink()


def test_create_symlink_for_claude_md_skips_wrong_symlink() -> None:
    """Test skipping when AGENTS.md points to something else."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create files
        claude_md = Path.cwd() / "CLAUDE.md"
        claude_md.write_text("# Project instructions", encoding="utf-8")
        other_file = Path.cwd() / "OTHER.md"
        other_file.write_text("# Other content", encoding="utf-8")

        # Create symlink to OTHER.md
        agents_md = Path.cwd() / "AGENTS.md"
        agents_md.symlink_to("OTHER.md")

        # Should skip
        status = command.create_symlink_for_claude_md(claude_md, dry_run=False)

        assert status == "skipped_exists"
        assert agents_md.is_symlink()
        assert agents_md.readlink() == Path("OTHER.md")


def test_create_agents_symlinks_finds_multiple_files() -> None:
    """Test finding and creating symlinks for multiple CLAUDE.md files."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        repo_root = Path.cwd()

        # Create multiple CLAUDE.md files
        (repo_root / "CLAUDE.md").write_text("# Root", encoding="utf-8")
        (repo_root / "sub1").mkdir()
        (repo_root / "sub1" / "CLAUDE.md").write_text("# Sub1", encoding="utf-8")
        (repo_root / "sub2").mkdir()
        (repo_root / "sub2" / "CLAUDE.md").write_text("# Sub2", encoding="utf-8")

        created, skipped = command.create_agents_symlinks(repo_root, dry_run=False, verbose=False)

        assert created == 3
        assert skipped == 0
        assert (repo_root / "AGENTS.md").is_symlink()
        assert (repo_root / "sub1" / "AGENTS.md").is_symlink()
        assert (repo_root / "sub2" / "AGENTS.md").is_symlink()


def test_create_agents_symlinks_idempotent() -> None:
    """Test running twice is idempotent."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        repo_root = Path.cwd()

        # Create CLAUDE.md file
        (repo_root / "CLAUDE.md").write_text("# Root", encoding="utf-8")

        # First run
        created1, skipped1 = command.create_agents_symlinks(repo_root, dry_run=False, verbose=False)
        assert created1 == 1
        assert skipped1 == 0

        # Second run
        created2, skipped2 = command.create_agents_symlinks(repo_root, dry_run=False, verbose=False)
        assert created2 == 0
        assert skipped2 == 1


def test_create_agents_symlinks_no_claude_files() -> None:
    """Test behavior when no CLAUDE.md files exist."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        repo_root = Path.cwd()

        created, skipped = command.create_agents_symlinks(repo_root, dry_run=False, verbose=False)

        assert created == 0
        assert skipped == 0


def test_cli_help() -> None:
    """Test create-agents-symlinks help output."""
    runner = CliRunner()
    result = runner.invoke(cli, ["create-agents-symlinks", "--help"])
    assert result.exit_code == 0
    assert "Create AGENTS.md symlinks" in result.output
    assert "--dry-run" in result.output
    assert "--verbose" in result.output


def test_cli_not_in_git_repo() -> None:
    """Test error when not in git repository root."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # No .git directory
        result = runner.invoke(cli, ["create-agents-symlinks"])
        # Script execution fails, CLI should exit with non-zero code
        assert result.exit_code == 1
