"""E2E tests for rebase commands."""

import subprocess
from pathlib import Path

from click.testing import CliRunner

from tests.fakes.github_ops import FakeGitHubOps
from tests.fakes.global_config_ops import FakeGlobalConfigOps
from tests.fakes.graphite_ops import FakeGraphiteOps
from workstack.cli.cli import cli
from workstack.core.context import WorkstackContext
from workstack.core.gitops import RealGitOps
from workstack.core.rebase_stack_ops import RebaseStackOps


def init_git_repo(repo_path: Path, default_branch: str = "main") -> None:
    """Initialize a git repository with initial commit."""
    subprocess.run(
        ["git", "init", "-b", default_branch],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    # Create initial commit
    test_file = repo_path / "README.md"
    test_file.write_text("# Test Repository\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "README.md"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )


def test_rebase_preview_clean(tmp_path: Path) -> None:
    """Test preview with no conflicts."""
    runner = CliRunner()

    # Setup repo with branches
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    # Create a feature branch with a commit
    subprocess.run(
        ["git", "checkout", "-b", "feature"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    feature_file = repo / "feature.txt"
    feature_file.write_text("feature work\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "feature.txt"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Add feature"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    # Go back to main
    subprocess.run(
        ["git", "checkout", "main"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    # Create context with real git ops
    test_ctx = WorkstackContext(
        git_ops=RealGitOps(),
        global_config_ops=FakeGlobalConfigOps(
            workstacks_root=tmp_path / "workstacks",
            use_graphite=False,
        ),
        github_ops=FakeGitHubOps(),
        graphite_ops=FakeGraphiteOps(),
        dry_run=False,
    )

    # Run preview from within the repo directory
    with runner.isolated_filesystem(temp_dir=repo):
        result = runner.invoke(
            cli,
            ["rebase", "preview", "feature"],
            obj=test_ctx,
            catch_exceptions=False,
        )

    assert result.exit_code == 0
    assert "Rebase completed cleanly" in result.output
    assert "workstack rebase apply" in result.output


def test_rebase_preview_with_conflicts(tmp_path: Path) -> None:
    """Test preview with conflicts."""
    runner = CliRunner()

    # Setup repo with conflicting branches
    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    # Modify file in main
    readme = repo / "README.md"
    readme.write_text("# Main Branch\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "README.md"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Update README in main"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    # Go back to before the commit
    subprocess.run(
        ["git", "checkout", "HEAD~1"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    # Create feature branch with conflicting change
    subprocess.run(
        ["git", "checkout", "-b", "feature"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    readme.write_text("# Feature Branch\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "README.md"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Update README in feature"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    # Go back to main
    subprocess.run(
        ["git", "checkout", "main"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    # Create context
    test_ctx = WorkstackContext(
        git_ops=RealGitOps(),
        global_config_ops=FakeGlobalConfigOps(
            workstacks_root=tmp_path / "workstacks",
            use_graphite=False,
        ),
        github_ops=FakeGitHubOps(),
        graphite_ops=FakeGraphiteOps(),
        dry_run=False,
    )

    # Run preview from within the repo directory
    with runner.isolated_filesystem(temp_dir=repo):
        result = runner.invoke(
            cli,
            ["rebase", "preview", "feature"],
            obj=test_ctx,
            catch_exceptions=False,
        )

    assert result.exit_code == 0
    assert "Conflicts detected" in result.output
    assert "README.md" in result.output
    assert "workstack rebase resolve" in result.output


def test_rebase_status_no_stacks(tmp_path: Path) -> None:
    """Test status when no stacks exist."""
    runner = CliRunner()

    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    test_ctx = WorkstackContext(
        git_ops=RealGitOps(),
        global_config_ops=FakeGlobalConfigOps(
            workstacks_root=tmp_path / "workstacks",
            use_graphite=False,
        ),
        github_ops=FakeGitHubOps(),
        graphite_ops=FakeGraphiteOps(),
        dry_run=False,
    )

    with runner.isolated_filesystem(temp_dir=repo):
        result = runner.invoke(
            cli,
            ["rebase", "status"],
            obj=test_ctx,
            catch_exceptions=False,
        )

    assert result.exit_code == 0
    assert "No active rebase stacks" in result.output


def test_rebase_status_with_stacks(tmp_path: Path) -> None:
    """Test status with active stacks."""
    runner = CliRunner()

    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    # Create a feature branch
    subprocess.run(
        ["git", "checkout", "-b", "feature"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    feature_file = repo / "feature.txt"
    feature_file.write_text("feature\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "feature.txt"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Add feature"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "checkout", "main"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    # Create a stack manually
    git_ops = RealGitOps()
    stack_ops = RebaseStackOps(git_ops, FakeGlobalConfigOps())
    stack_ops.create_stack(repo, "feature", "main")

    test_ctx = WorkstackContext(
        git_ops=git_ops,
        global_config_ops=FakeGlobalConfigOps(
            workstacks_root=tmp_path / "workstacks",
            use_graphite=False,
        ),
        github_ops=FakeGitHubOps(),
        graphite_ops=FakeGraphiteOps(),
        dry_run=False,
    )

    with runner.isolated_filesystem(temp_dir=repo):
        result = runner.invoke(
            cli,
            ["rebase", "status"],
            obj=test_ctx,
            catch_exceptions=False,
        )

    assert result.exit_code == 0
    assert "Active rebase stacks" in result.output
    assert "feature" in result.output


def test_rebase_abort(tmp_path: Path) -> None:
    """Test aborting a rebase stack."""
    runner = CliRunner()

    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    # Create a feature branch
    subprocess.run(
        ["git", "checkout", "-b", "feature"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "checkout", "main"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    # Create a stack
    git_ops = RealGitOps()
    stack_ops = RebaseStackOps(git_ops, FakeGlobalConfigOps())
    stack_ops.create_stack(repo, "feature", "main")

    test_ctx = WorkstackContext(
        git_ops=git_ops,
        global_config_ops=FakeGlobalConfigOps(
            workstacks_root=tmp_path / "workstacks",
            use_graphite=False,
        ),
        github_ops=FakeGitHubOps(),
        graphite_ops=FakeGraphiteOps(),
        dry_run=False,
    )

    # Abort the stack
    with runner.isolated_filesystem(temp_dir=repo):
        result = runner.invoke(
            cli,
            ["rebase", "abort", "feature"],
            obj=test_ctx,
            catch_exceptions=False,
        )

    assert result.exit_code == 0
    assert "cleaned up" in result.output

    # Verify stack is gone
    with runner.isolated_filesystem(temp_dir=repo):
        result = runner.invoke(
            cli,
            ["rebase", "status"],
            obj=test_ctx,
            catch_exceptions=False,
        )
    assert "No active rebase stacks" in result.output


def test_rebase_abort_without_branch_uses_current(tmp_path: Path) -> None:
    """Test abort without branch argument uses current branch."""
    runner = CliRunner()

    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    # Create feature branch
    subprocess.run(
        ["git", "checkout", "-b", "feature"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    # Go back to main to allow worktree creation
    subprocess.run(
        ["git", "checkout", "main"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    # Create a stack for feature
    git_ops = RealGitOps()
    stack_ops = RebaseStackOps(git_ops, FakeGlobalConfigOps())
    stack_ops.create_stack(repo, "feature", "main")

    test_ctx = WorkstackContext(
        git_ops=git_ops,
        global_config_ops=FakeGlobalConfigOps(
            workstacks_root=tmp_path / "workstacks",
            use_graphite=False,
        ),
        github_ops=FakeGitHubOps(),
        graphite_ops=FakeGraphiteOps(),
        dry_run=False,
    )

    # Abort without branch argument while on main (tests default to current branch main)
    with runner.isolated_filesystem(temp_dir=repo):
        result = runner.invoke(
            cli,
            ["rebase", "abort"],
            obj=test_ctx,
            catch_exceptions=False,
        )

    # Since we're on main and there's no stack for main, we should get a "no stack" message
    assert result.exit_code == 0
    assert "No rebase stack" in result.output


def test_rebase_status_specific_branch(tmp_path: Path) -> None:
    """Test status command with specific branch."""
    runner = CliRunner()

    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    # Create feature branch
    subprocess.run(
        ["git", "checkout", "-b", "feature"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "checkout", "main"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    # Create a stack
    git_ops = RealGitOps()
    stack_ops = RebaseStackOps(git_ops, FakeGlobalConfigOps())
    stack_ops.create_stack(repo, "feature", "main")

    test_ctx = WorkstackContext(
        git_ops=git_ops,
        global_config_ops=FakeGlobalConfigOps(
            workstacks_root=tmp_path / "workstacks",
            use_graphite=False,
        ),
        github_ops=FakeGitHubOps(),
        graphite_ops=FakeGraphiteOps(),
        dry_run=False,
    )

    # Check status of specific branch
    with runner.isolated_filesystem(temp_dir=repo):
        result = runner.invoke(
            cli,
            ["rebase", "status", "feature"],
            obj=test_ctx,
            catch_exceptions=False,
        )

    assert result.exit_code == 0
    assert "feature" in result.output
    assert "created" in result.output.lower()


def test_rebase_abort_nonexistent_stack(tmp_path: Path) -> None:
    """Test aborting a stack that doesn't exist."""
    runner = CliRunner()

    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    test_ctx = WorkstackContext(
        git_ops=RealGitOps(),
        global_config_ops=FakeGlobalConfigOps(
            workstacks_root=tmp_path / "workstacks",
            use_graphite=False,
        ),
        github_ops=FakeGitHubOps(),
        graphite_ops=FakeGraphiteOps(),
        dry_run=False,
    )

    with runner.isolated_filesystem(temp_dir=repo):
        result = runner.invoke(
            cli,
            ["rebase", "abort", "nonexistent"],
            obj=test_ctx,
            catch_exceptions=False,
        )

    assert result.exit_code == 0
    assert "No rebase stack to abort" in result.output


def test_rebase_apply_clean_stack(tmp_path: Path) -> None:
    """Test applying a clean rebase stack."""
    runner = CliRunner()

    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    # Create a feature branch with a commit
    subprocess.run(
        ["git", "checkout", "-b", "feature"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    feature_file = repo / "feature.txt"
    feature_file.write_text("feature work\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "feature.txt"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Add feature"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "checkout", "main"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    git_ops = RealGitOps()
    test_ctx = WorkstackContext(
        git_ops=git_ops,
        global_config_ops=FakeGlobalConfigOps(
            workstacks_root=tmp_path / "workstacks",
            use_graphite=False,
        ),
        github_ops=FakeGitHubOps(),
        graphite_ops=FakeGraphiteOps(),
        dry_run=False,
    )

    # Preview rebase to create stack
    with runner.isolated_filesystem(temp_dir=repo):
        result = runner.invoke(
            cli,
            ["rebase", "preview", "feature"],
            obj=test_ctx,
            catch_exceptions=False,
        )
    assert result.exit_code == 0

    # Apply the rebase (use --force since rebase dir might exist)
    with runner.isolated_filesystem(temp_dir=repo):
        result = runner.invoke(
            cli,
            ["rebase", "apply", "feature", "--force"],
            obj=test_ctx,
            catch_exceptions=False,
        )

    assert result.exit_code == 0, (
        f"Expected exit code 0, got {result.exit_code}. Output:\n{result.output}"
    )
    assert "Rebase applied successfully" in result.output
    assert "rebased successfully" in result.output


def test_rebase_apply_no_stack(tmp_path: Path) -> None:
    """Test applying when no stack exists."""
    runner = CliRunner()

    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    test_ctx = WorkstackContext(
        git_ops=RealGitOps(),
        global_config_ops=FakeGlobalConfigOps(
            workstacks_root=tmp_path / "workstacks",
            use_graphite=False,
        ),
        github_ops=FakeGitHubOps(),
        graphite_ops=FakeGraphiteOps(),
        dry_run=False,
    )

    with runner.isolated_filesystem(temp_dir=repo):
        result = runner.invoke(
            cli,
            ["rebase", "apply", "nonexistent"],
            obj=test_ctx,
            catch_exceptions=False,
        )

    assert result.exit_code == 1
    assert "No rebase stack to apply" in result.output


def test_rebase_apply_with_force_flag(tmp_path: Path) -> None:
    """Test applying with --force flag skips safety checks."""
    runner = CliRunner()

    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    # Create a feature branch
    subprocess.run(
        ["git", "checkout", "-b", "feature"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    feature_file = repo / "feature.txt"
    feature_file.write_text("feature\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "feature.txt"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Add feature"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "checkout", "main"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    git_ops = RealGitOps()
    test_ctx = WorkstackContext(
        git_ops=git_ops,
        global_config_ops=FakeGlobalConfigOps(
            workstacks_root=tmp_path / "workstacks",
            use_graphite=False,
        ),
        github_ops=FakeGitHubOps(),
        graphite_ops=FakeGraphiteOps(),
        dry_run=False,
    )

    # Preview to create stack
    with runner.isolated_filesystem(temp_dir=repo):
        runner.invoke(
            cli,
            ["rebase", "preview", "feature"],
            obj=test_ctx,
            catch_exceptions=False,
        )

    # Apply with --force
    with runner.isolated_filesystem(temp_dir=repo):
        result = runner.invoke(
            cli,
            ["rebase", "apply", "feature", "--force"],
            obj=test_ctx,
            catch_exceptions=False,
        )

    assert result.exit_code == 0
    assert "Pre-flight checks" not in result.output
    assert "Rebase applied successfully" in result.output


def test_rebase_compare(tmp_path: Path) -> None:
    """Test comparing branch with rebase stack."""
    runner = CliRunner()

    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    # Create feature branch
    subprocess.run(
        ["git", "checkout", "-b", "feature"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    feature_file = repo / "feature.txt"
    feature_file.write_text("feature\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "feature.txt"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Add feature"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "checkout", "main"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    git_ops = RealGitOps()
    test_ctx = WorkstackContext(
        git_ops=git_ops,
        global_config_ops=FakeGlobalConfigOps(
            workstacks_root=tmp_path / "workstacks",
            use_graphite=False,
        ),
        github_ops=FakeGitHubOps(),
        graphite_ops=FakeGraphiteOps(),
        dry_run=False,
    )

    # Create stack
    with runner.isolated_filesystem(temp_dir=repo):
        runner.invoke(
            cli,
            ["rebase", "preview", "feature"],
            obj=test_ctx,
            catch_exceptions=False,
        )

    # Compare
    with runner.isolated_filesystem(temp_dir=repo):
        result = runner.invoke(
            cli,
            ["rebase", "compare", "feature"],
            obj=test_ctx,
            catch_exceptions=False,
        )

    assert result.exit_code == 0
    assert "Comparing feature with rebase stack" in result.output
    assert "Current:" in result.output
    assert "Rebased:" in result.output


def test_rebase_compare_no_stack(tmp_path: Path) -> None:
    """Test compare when no stack exists."""
    runner = CliRunner()

    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    test_ctx = WorkstackContext(
        git_ops=RealGitOps(),
        global_config_ops=FakeGlobalConfigOps(
            workstacks_root=tmp_path / "workstacks",
            use_graphite=False,
        ),
        github_ops=FakeGitHubOps(),
        graphite_ops=FakeGraphiteOps(),
        dry_run=False,
    )

    with runner.isolated_filesystem(temp_dir=repo):
        result = runner.invoke(
            cli,
            ["rebase", "compare", "nonexistent"],
            obj=test_ctx,
            catch_exceptions=False,
        )

    assert result.exit_code == 1
    assert "No rebase stack" in result.output


def test_rebase_resolve_no_conflicts(tmp_path: Path) -> None:
    """Test resolve when there are no conflicts."""
    runner = CliRunner()

    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    # Create feature branch with no conflicts
    subprocess.run(
        ["git", "checkout", "-b", "feature"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    feature_file = repo / "feature.txt"
    feature_file.write_text("feature\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "feature.txt"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Add feature"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "checkout", "main"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    git_ops = RealGitOps()
    test_ctx = WorkstackContext(
        git_ops=git_ops,
        global_config_ops=FakeGlobalConfigOps(
            workstacks_root=tmp_path / "workstacks",
            use_graphite=False,
        ),
        github_ops=FakeGitHubOps(),
        graphite_ops=FakeGraphiteOps(),
        dry_run=False,
    )

    # Create stack with preview
    with runner.isolated_filesystem(temp_dir=repo):
        runner.invoke(
            cli,
            ["rebase", "preview", "feature"],
            obj=test_ctx,
            catch_exceptions=False,
        )

    # Try to resolve (should say no conflicts)
    with runner.isolated_filesystem(temp_dir=repo):
        result = runner.invoke(
            cli,
            ["rebase", "resolve", "feature"],
            obj=test_ctx,
            catch_exceptions=False,
        )

    assert result.exit_code == 0
    assert "No conflicts to resolve" in result.output


def test_rebase_resolve_no_stack(tmp_path: Path) -> None:
    """Test resolve when no stack exists."""
    runner = CliRunner()

    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    test_ctx = WorkstackContext(
        git_ops=RealGitOps(),
        global_config_ops=FakeGlobalConfigOps(
            workstacks_root=tmp_path / "workstacks",
            use_graphite=False,
        ),
        github_ops=FakeGitHubOps(),
        graphite_ops=FakeGraphiteOps(),
        dry_run=False,
    )

    with runner.isolated_filesystem(temp_dir=repo):
        result = runner.invoke(
            cli,
            ["rebase", "resolve", "nonexistent"],
            obj=test_ctx,
            catch_exceptions=False,
        )

    assert result.exit_code == 1
    assert "No rebase stack" in result.output


def test_rebase_test_with_passing_tests(tmp_path: Path) -> None:
    """Test running tests that pass in a rebase stack."""
    runner = CliRunner()

    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    # Create feature branch
    subprocess.run(
        ["git", "checkout", "-b", "feature"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    # Add a test file that will pass
    test_file = repo / "test_example.py"
    test_file.write_text("def test_pass(): assert True\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "test_example.py"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Add test"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "checkout", "main"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    git_ops = RealGitOps()
    test_ctx = WorkstackContext(
        git_ops=git_ops,
        global_config_ops=FakeGlobalConfigOps(
            workstacks_root=tmp_path / "workstacks",
            use_graphite=False,
        ),
        github_ops=FakeGitHubOps(),
        graphite_ops=FakeGraphiteOps(),
        dry_run=False,
    )

    # Preview to create stack
    with runner.isolated_filesystem(temp_dir=repo):
        runner.invoke(
            cli,
            ["rebase", "preview", "feature"],
            obj=test_ctx,
            catch_exceptions=False,
        )

    # Run tests with explicit command
    with runner.isolated_filesystem(temp_dir=repo):
        result = runner.invoke(
            cli,
            ["rebase", "test", "feature", "--command", "echo 'Tests passed'"],
            obj=test_ctx,
            catch_exceptions=False,
        )

    assert result.exit_code == 0
    assert "Tests passed!" in result.output
    assert "workstack rebase apply" in result.output


def test_rebase_test_with_failing_tests(tmp_path: Path) -> None:
    """Test running tests that fail in a rebase stack."""
    runner = CliRunner()

    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    # Create feature branch
    subprocess.run(
        ["git", "checkout", "-b", "feature"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    feature_file = repo / "feature.txt"
    feature_file.write_text("feature\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "feature.txt"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Add feature"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "checkout", "main"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    git_ops = RealGitOps()
    test_ctx = WorkstackContext(
        git_ops=git_ops,
        global_config_ops=FakeGlobalConfigOps(
            workstacks_root=tmp_path / "workstacks",
            use_graphite=False,
        ),
        github_ops=FakeGitHubOps(),
        graphite_ops=FakeGraphiteOps(),
        dry_run=False,
    )

    # Preview to create stack
    with runner.isolated_filesystem(temp_dir=repo):
        runner.invoke(
            cli,
            ["rebase", "preview", "feature"],
            obj=test_ctx,
            catch_exceptions=False,
        )

    # Run tests that fail (exit code 1)
    with runner.isolated_filesystem(temp_dir=repo):
        result = runner.invoke(
            cli,
            ["rebase", "test", "feature", "--command", "sh -c 'exit 1'"],
            obj=test_ctx,
            catch_exceptions=False,
        )

    assert result.exit_code == 1
    assert "Tests failed" in result.output
    assert "Exit code: 1" in result.output


def test_rebase_test_auto_detects_pytest(tmp_path: Path) -> None:
    """Test auto-detection of pytest test command."""
    runner = CliRunner()

    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    # Create feature branch with pytest.ini
    subprocess.run(
        ["git", "checkout", "-b", "feature"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    pytest_ini = repo / "pytest.ini"
    pytest_ini.write_text("[pytest]\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "pytest.ini"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Add pytest config"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "checkout", "main"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    git_ops = RealGitOps()
    test_ctx = WorkstackContext(
        git_ops=git_ops,
        global_config_ops=FakeGlobalConfigOps(
            workstacks_root=tmp_path / "workstacks",
            use_graphite=False,
        ),
        github_ops=FakeGitHubOps(),
        graphite_ops=FakeGraphiteOps(),
        dry_run=False,
    )

    # Preview to create stack
    with runner.isolated_filesystem(temp_dir=repo):
        runner.invoke(
            cli,
            ["rebase", "preview", "feature"],
            obj=test_ctx,
            catch_exceptions=False,
        )

    # Run tests without specifying command (should auto-detect)
    with runner.isolated_filesystem(temp_dir=repo):
        result = runner.invoke(
            cli,
            ["rebase", "test", "feature"],
            obj=test_ctx,
            catch_exceptions=False,
        )

    # Should detect pytest but fail because pytest isn't installed
    # or succeed if it is installed
    assert "Detected test command: pytest" in result.output


def test_rebase_test_no_command_detected(tmp_path: Path) -> None:
    """Test error when no test command can be detected."""
    runner = CliRunner()

    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    # Create feature branch with no test markers
    subprocess.run(
        ["git", "checkout", "-b", "feature"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    feature_file = repo / "feature.txt"
    feature_file.write_text("feature\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "feature.txt"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Add feature"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "checkout", "main"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    git_ops = RealGitOps()
    test_ctx = WorkstackContext(
        git_ops=git_ops,
        global_config_ops=FakeGlobalConfigOps(
            workstacks_root=tmp_path / "workstacks",
            use_graphite=False,
        ),
        github_ops=FakeGitHubOps(),
        graphite_ops=FakeGraphiteOps(),
        dry_run=False,
    )

    # Preview to create stack
    with runner.isolated_filesystem(temp_dir=repo):
        runner.invoke(
            cli,
            ["rebase", "preview", "feature"],
            obj=test_ctx,
            catch_exceptions=False,
        )

    # Try to run tests without command
    with runner.isolated_filesystem(temp_dir=repo):
        result = runner.invoke(
            cli,
            ["rebase", "test", "feature"],
            obj=test_ctx,
            catch_exceptions=False,
        )

    assert result.exit_code == 1
    assert "No test command detected" in result.output
    assert "Specify with --command" in result.output


def test_rebase_test_no_stack(tmp_path: Path) -> None:
    """Test running tests when no stack exists."""
    runner = CliRunner()

    repo = tmp_path / "repo"
    repo.mkdir()
    init_git_repo(repo, "main")

    test_ctx = WorkstackContext(
        git_ops=RealGitOps(),
        global_config_ops=FakeGlobalConfigOps(
            workstacks_root=tmp_path / "workstacks",
            use_graphite=False,
        ),
        github_ops=FakeGitHubOps(),
        graphite_ops=FakeGraphiteOps(),
        dry_run=False,
    )

    with runner.isolated_filesystem(temp_dir=repo):
        result = runner.invoke(
            cli,
            ["rebase", "test", "nonexistent"],
            obj=test_ctx,
            catch_exceptions=False,
        )

    assert result.exit_code == 1
    assert "No rebase stack for nonexistent" in result.output
