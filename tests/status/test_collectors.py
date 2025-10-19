"""Unit tests for status collectors."""

import json
import subprocess
from pathlib import Path

from tests.fakes.context import create_test_context
from tests.fakes.github_ops import FakeGitHubOps
from tests.fakes.gitops import FakeGitOps
from tests.fakes.global_config_ops import FakeGlobalConfigOps
from tests.fakes.graphite_ops import FakeGraphiteOps
from workstack.core.github_ops import PullRequestInfo
from workstack.status.collectors.git import GitStatusCollector
from workstack.status.collectors.github import GitHubPRCollector
from workstack.status.collectors.graphite import GraphiteStackCollector
from workstack.status.collectors.plan import PlanFileCollector


def _create_graphite_cache(repo_root: Path, branches_data: list[tuple[str, dict]]) -> None:
    """Helper to create .graphite_cache_persist file for testing.

    Args:
        repo_root: Repository root path
        branches_data: List of (branch_name, metadata_dict) tuples
            metadata_dict can contain:
            - "parentBranchName": str | None
            - "children": list[str]
            - "validationResult": "TRUNK" (optional, marks trunk)

    Example:
        _create_graphite_cache(repo_root, [
            ("main", {"validationResult": "TRUNK", "children": ["feature-1"]}),
            ("feature-1", {"parentBranchName": "main", "children": ["feature-2"]}),
            ("feature-2", {"parentBranchName": "feature-1", "children": []}),
        ])
    """
    git_dir = repo_root / ".git"
    git_dir.mkdir(parents=True, exist_ok=True)

    cache_file = git_dir / ".graphite_cache_persist"

    branches = []
    for branch_name, metadata in branches_data:
        branches.append([branch_name, metadata])

    cache_data = {"branches": branches}
    cache_file.write_text(json.dumps(cache_data), encoding="utf-8")


def _init_git_repo(repo_path: Path, branch: str = "main") -> None:
    """Helper to initialize a git repository for integration tests.

    Args:
        repo_path: Path to initialize repo in
        branch: Initial branch name (default: "main")
    """
    subprocess.run(["git", "init", "-b", branch], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)

    (repo_path / "README.md").write_text("# Test Repo", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True)


def test_git_collector_clean_worktree(tmp_path: Path) -> None:
    """Test GitStatusCollector with clean worktree."""
    ctx = create_test_context()
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()

    collector = GitStatusCollector()

    # Note: This will return None since there's no real git repo
    # For proper testing, we'd need a real git integration test
    result = collector.collect(ctx, worktree_path, tmp_path)

    # In this fake setup, result will be None
    assert result is None


def test_git_collector_is_available(tmp_path: Path) -> None:
    """Test GitStatusCollector availability check."""
    ctx = create_test_context()
    existing_path = tmp_path / "exists"
    existing_path.mkdir()
    nonexistent_path = tmp_path / "does_not_exist"

    collector = GitStatusCollector()

    assert collector.is_available(ctx, existing_path) is True
    assert collector.is_available(ctx, nonexistent_path) is False


def test_plan_collector_with_existing_plan(tmp_path: Path) -> None:
    """Test PlanFileCollector with existing plan file."""
    ctx = create_test_context()
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()

    plan_path = worktree_path / ".PLAN.md"
    plan_content = """# Test Plan
## Introduction
This is a test plan file.
It has multiple lines.
Line five is here."""
    plan_path.write_text(plan_content, encoding="utf-8")

    collector = PlanFileCollector()
    result = collector.collect(ctx, worktree_path, tmp_path)

    assert result is not None
    assert result.exists is True
    assert result.path == plan_path
    assert result.line_count == 5
    assert len(result.first_lines) == 5
    assert result.first_lines[0] == "# Test Plan"
    assert result.first_lines[4] == "Line five is here."


def test_plan_collector_with_short_plan(tmp_path: Path) -> None:
    """Test PlanFileCollector with plan file shorter than 5 lines."""
    ctx = create_test_context()
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()

    plan_path = worktree_path / ".PLAN.md"
    plan_content = """# Short Plan
Just two lines."""
    plan_path.write_text(plan_content, encoding="utf-8")

    collector = PlanFileCollector()
    result = collector.collect(ctx, worktree_path, tmp_path)

    assert result is not None
    assert result.exists is True
    assert result.line_count == 2
    assert len(result.first_lines) == 2
    assert result.first_lines[0] == "# Short Plan"
    assert result.first_lines[1] == "Just two lines."


def test_plan_collector_no_plan_file(tmp_path: Path) -> None:
    """Test PlanFileCollector when plan file doesn't exist."""
    ctx = create_test_context()
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()

    collector = PlanFileCollector()
    result = collector.collect(ctx, worktree_path, tmp_path)

    assert result is not None
    assert result.exists is False
    assert result.path is None
    assert result.line_count == 0
    assert len(result.first_lines) == 0


def test_plan_collector_is_available(tmp_path: Path) -> None:
    """Test PlanFileCollector availability check."""
    ctx = create_test_context()
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()

    collector = PlanFileCollector()

    # No plan file
    assert collector.is_available(ctx, worktree_path) is False

    # Create plan file
    (worktree_path / ".PLAN.md").write_text("# Plan", encoding="utf-8")
    assert collector.is_available(ctx, worktree_path) is True


def test_plan_collector_generates_summary(tmp_path: Path) -> None:
    """Test PlanFileCollector generates summary from non-header lines."""
    ctx = create_test_context()
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()

    plan_path = worktree_path / ".PLAN.md"
    plan_content = """# Header

This is the first summary line.
This is the second summary line.
More content follows."""
    plan_path.write_text(plan_content, encoding="utf-8")

    collector = PlanFileCollector()
    result = collector.collect(ctx, worktree_path, tmp_path)

    assert result is not None
    assert result.summary is not None
    assert "first summary line" in result.summary
    assert "second summary line" in result.summary


def test_plan_collector_truncates_long_summary(tmp_path: Path) -> None:
    """Test PlanFileCollector truncates very long summaries."""
    ctx = create_test_context()
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()

    plan_path = worktree_path / ".PLAN.md"
    long_line = "a" * 150  # 150 characters
    plan_path.write_text(long_line, encoding="utf-8")

    collector = PlanFileCollector()
    result = collector.collect(ctx, worktree_path, tmp_path)

    assert result is not None
    assert result.summary is not None
    assert len(result.summary) == 100  # Truncated to 100 chars
    assert result.summary.endswith("...")


def test_graphite_collector_name() -> None:
    """Test GraphiteStackCollector name property."""
    collector = GraphiteStackCollector()
    assert collector.name == "stack"


def test_graphite_collector_is_available_graphite_disabled(tmp_path: Path) -> None:
    """Test is_available() returns False when Graphite disabled in config."""
    config_ops = FakeGlobalConfigOps(exists=True, use_graphite=False)
    ctx = create_test_context(global_config_ops=config_ops)

    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()

    collector = GraphiteStackCollector()
    assert collector.is_available(ctx, worktree_path) is False


def test_graphite_collector_is_available_worktree_not_exists(tmp_path: Path) -> None:
    """Test is_available() returns False when worktree doesn't exist."""
    config_ops = FakeGlobalConfigOps(exists=True, use_graphite=True)
    ctx = create_test_context(global_config_ops=config_ops)

    nonexistent_path = tmp_path / "does_not_exist"

    collector = GraphiteStackCollector()
    assert collector.is_available(ctx, nonexistent_path) is False


def test_graphite_collector_is_available_success(tmp_path: Path) -> None:
    """Test is_available() returns True when Graphite enabled and worktree exists."""
    config_ops = FakeGlobalConfigOps(exists=True, use_graphite=True)
    ctx = create_test_context(global_config_ops=config_ops)

    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()

    collector = GraphiteStackCollector()
    assert collector.is_available(ctx, worktree_path) is True


def test_graphite_collector_collect_no_branch(tmp_path: Path) -> None:
    """Test collect() returns None when get_current_branch returns None."""
    git_ops = FakeGitOps(current_branches={})
    ctx = create_test_context(git_ops=git_ops)

    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    collector = GraphiteStackCollector()
    result = collector.collect(ctx, worktree_path, repo_root)

    assert result is None


def test_graphite_collector_collect_stack_not_found(tmp_path: Path) -> None:
    """Test collect() returns None when get_branch_stack returns None."""
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    git_ops = FakeGitOps(
        current_branches={worktree_path: "feature"}, git_common_dirs={repo_root: repo_root / ".git"}
    )
    ctx = create_test_context(git_ops=git_ops)

    collector = GraphiteStackCollector()
    result = collector.collect(ctx, worktree_path, repo_root)

    assert result is None


def test_graphite_collector_collect_branch_not_in_stack(tmp_path: Path) -> None:
    """Test collect() returns None when branch exists but not in returned stack."""
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    git_ops = FakeGitOps(
        current_branches={worktree_path: "feature-orphan"},
        git_common_dirs={repo_root: repo_root / ".git"},
    )
    ctx = create_test_context(git_ops=git_ops)

    _create_graphite_cache(
        repo_root,
        [
            ("main", {"validationResult": "TRUNK", "children": ["feature-1"]}),
            ("feature-1", {"parentBranchName": "main", "children": []}),
        ],
    )

    collector = GraphiteStackCollector()
    result = collector.collect(ctx, worktree_path, repo_root)

    assert result is None


def test_graphite_collector_collect_trunk_branch(tmp_path: Path) -> None:
    """Test collect() returns StackPosition for branch at trunk (first in stack)."""
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    git_ops = FakeGitOps(
        current_branches={worktree_path: "main"}, git_common_dirs={repo_root: repo_root / ".git"}
    )
    ctx = create_test_context(git_ops=git_ops)

    _create_graphite_cache(
        repo_root,
        [
            ("main", {"validationResult": "TRUNK", "children": ["feature-1"]}),
            ("feature-1", {"parentBranchName": "main", "children": []}),
        ],
    )

    collector = GraphiteStackCollector()
    result = collector.collect(ctx, worktree_path, repo_root)

    assert result is not None
    assert result.is_trunk is True
    assert result.parent_branch is None
    assert result.current_branch == "main"
    assert len(result.children_branches) == 1
    assert result.children_branches[0] == "feature-1"


def test_graphite_collector_collect_middle_branch(tmp_path: Path) -> None:
    """Test collect() returns StackPosition for branch in middle of stack."""
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    git_ops = FakeGitOps(
        current_branches={worktree_path: "feature-2"},
        git_common_dirs={repo_root: repo_root / ".git"},
    )
    ctx = create_test_context(git_ops=git_ops)

    _create_graphite_cache(
        repo_root,
        [
            ("main", {"validationResult": "TRUNK", "children": ["feature-1"]}),
            ("feature-1", {"parentBranchName": "main", "children": ["feature-2"]}),
            ("feature-2", {"parentBranchName": "feature-1", "children": ["feature-3"]}),
            ("feature-3", {"parentBranchName": "feature-2", "children": []}),
        ],
    )

    collector = GraphiteStackCollector()
    result = collector.collect(ctx, worktree_path, repo_root)

    assert result is not None
    assert result.is_trunk is False
    assert result.parent_branch == "feature-1"
    assert result.children_branches == ["feature-3"]
    assert result.current_branch == "feature-2"


def test_graphite_collector_collect_leaf_branch(tmp_path: Path) -> None:
    """Test collect() returns StackPosition for branch at end of stack (no children)."""
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    git_ops = FakeGitOps(
        current_branches={worktree_path: "feature-3"},
        git_common_dirs={repo_root: repo_root / ".git"},
    )
    ctx = create_test_context(git_ops=git_ops)

    _create_graphite_cache(
        repo_root,
        [
            ("main", {"validationResult": "TRUNK", "children": ["feature-1"]}),
            ("feature-1", {"parentBranchName": "main", "children": ["feature-2"]}),
            ("feature-2", {"parentBranchName": "feature-1", "children": ["feature-3"]}),
            ("feature-3", {"parentBranchName": "feature-2", "children": []}),
        ],
    )

    collector = GraphiteStackCollector()
    result = collector.collect(ctx, worktree_path, repo_root)

    assert result is not None
    assert result.is_trunk is False
    assert result.parent_branch == "feature-2"
    assert result.children_branches == []
    assert result.current_branch == "feature-3"


def test_git_collector_name() -> None:
    """Test GitStatusCollector name property."""
    collector = GitStatusCollector()
    assert collector.name == "git"


def test_git_collector_file_status_clean_repo(tmp_path: Path) -> None:
    """Test _get_file_status() on clean repository."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)

    collector = GitStatusCollector()
    staged, modified, untracked = collector._get_file_status(repo)

    assert staged == []
    assert modified == []
    assert untracked == []


def test_git_collector_file_status_staged_files(tmp_path: Path) -> None:
    """Test _get_file_status() parses staged files correctly."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)

    (repo / "new_file.txt").write_text("content", encoding="utf-8")
    subprocess.run(["git", "add", "new_file.txt"], cwd=repo, check=True)

    (repo / "README.md").write_text("modified", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)

    collector = GitStatusCollector()
    staged, modified, untracked = collector._get_file_status(repo)

    assert "new_file.txt" in staged
    assert "README.md" in staged
    assert modified == []


def test_git_collector_file_status_modified_files(tmp_path: Path) -> None:
    """Test _get_file_status() parses modified (unstaged) files."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)

    (repo / "README.md").write_text("modified", encoding="utf-8")

    collector = GitStatusCollector()
    staged, modified, untracked = collector._get_file_status(repo)

    assert staged == []
    assert "README.md" in modified
    assert untracked == []


def test_git_collector_file_status_untracked_files(tmp_path: Path) -> None:
    """Test _get_file_status() parses untracked files."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)

    (repo / "untracked.txt").write_text("content", encoding="utf-8")

    collector = GitStatusCollector()
    staged, modified, untracked = collector._get_file_status(repo)

    assert staged == []
    assert modified == []
    assert "untracked.txt" in untracked


def test_git_collector_file_status_mixed_state(tmp_path: Path) -> None:
    """Test _get_file_status() with combination of states."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)

    (repo / "staged.txt").write_text("staged", encoding="utf-8")
    subprocess.run(["git", "add", "staged.txt"], cwd=repo, check=True)

    (repo / "README.md").write_text("modified", encoding="utf-8")

    (repo / "untracked.txt").write_text("untracked", encoding="utf-8")

    collector = GitStatusCollector()
    staged, modified, untracked = collector._get_file_status(repo)

    assert len(staged) == 1
    assert "staged.txt" in staged
    assert len(modified) == 1
    assert "README.md" in modified
    assert len(untracked) == 1
    assert "untracked.txt" in untracked


def test_git_collector_ahead_behind_no_upstream(tmp_path: Path) -> None:
    """Test _get_ahead_behind() returns (0,0) when no upstream set."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)

    collector = GitStatusCollector()
    ahead, behind = collector._get_ahead_behind(repo, "main")

    assert ahead == 0
    assert behind == 0


def test_git_collector_ahead_behind_with_upstream(tmp_path: Path) -> None:
    """Test _get_ahead_behind() returns correct counts."""
    remote = tmp_path / "remote"
    remote.mkdir()
    subprocess.run(["git", "init", "--bare"], cwd=remote, check=True, capture_output=True)

    local = tmp_path / "local"
    subprocess.run(["git", "clone", str(remote), str(local)], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=local, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=local, check=True)

    (local / "file.txt").write_text("content", encoding="utf-8")
    subprocess.run(["git", "add", "file.txt"], cwd=local, check=True)
    subprocess.run(["git", "commit", "-m", "Initial"], cwd=local, check=True)
    # Ensure we're on main branch (git init may create master or main depending on config)
    subprocess.run(["git", "branch", "-M", "main"], cwd=local, check=True)
    subprocess.run(["git", "push", "-u", "origin", "main"], cwd=local, check=True, capture_output=True)

    (local / "local.txt").write_text("local", encoding="utf-8")
    subprocess.run(["git", "add", "local.txt"], cwd=local, check=True)
    subprocess.run(["git", "commit", "-m", "Local commit"], cwd=local, check=True)

    collector = GitStatusCollector()
    ahead, behind = collector._get_ahead_behind(local, "main")

    assert ahead == 1
    assert behind == 0


def test_git_collector_recent_commits(tmp_path: Path) -> None:
    """Test _get_recent_commits() parses git log output."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)

    for i in range(1, 4):
        (repo / f"file{i}.txt").write_text(f"content {i}", encoding="utf-8")
        subprocess.run(["git", "add", f"file{i}.txt"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-m", f"Commit {i}"], cwd=repo, check=True)

    collector = GitStatusCollector()
    commits = collector._get_recent_commits(repo, limit=5)

    assert len(commits) >= 3
    assert commits[0].message == "Commit 3"
    assert len(commits[0].sha) == 7
    assert commits[0].author == "Test User"
    assert commits[0].date != ""


def test_git_collector_collect_integration(tmp_path: Path) -> None:
    """Test full collect() method aggregates all data."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)

    (repo / "staged.txt").write_text("staged", encoding="utf-8")
    subprocess.run(["git", "add", "staged.txt"], cwd=repo, check=True)
    (repo / "README.md").write_text("modified", encoding="utf-8")
    (repo / "untracked.txt").write_text("untracked", encoding="utf-8")

    git_ops = FakeGitOps(current_branches={repo: "main"})
    ctx = create_test_context(git_ops=git_ops)
    collector = GitStatusCollector()
    result = collector.collect(ctx, repo, repo)

    assert result is not None
    assert result.branch == "main"
    assert result.clean is False
    assert result.ahead == 0
    assert result.behind == 0
    assert len(result.staged_files) == 1
    assert len(result.modified_files) == 1
    assert len(result.untracked_files) == 1
    assert len(result.recent_commits) > 0


def test_github_pr_collector_name() -> None:
    """Test GitHubPRCollector name property."""
    collector = GitHubPRCollector()
    assert collector.name == "pr"


def test_github_pr_collector_is_available_pr_info_disabled(tmp_path: Path) -> None:
    """Test is_available() returns False when show_pr_info disabled."""
    config_ops = FakeGlobalConfigOps(exists=True, show_pr_info=False)
    ctx = create_test_context(global_config_ops=config_ops)

    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()

    collector = GitHubPRCollector()
    assert collector.is_available(ctx, worktree_path) is False


def test_github_pr_collector_is_available_worktree_not_exists(tmp_path: Path) -> None:
    """Test is_available() returns False when worktree doesn't exist."""
    config_ops = FakeGlobalConfigOps(exists=True, show_pr_info=True)
    ctx = create_test_context(global_config_ops=config_ops)

    nonexistent_path = tmp_path / "does_not_exist"

    collector = GitHubPRCollector()
    assert collector.is_available(ctx, nonexistent_path) is False


def test_github_pr_collector_is_available_success(tmp_path: Path) -> None:
    """Test is_available() returns True when enabled and worktree exists."""
    config_ops = FakeGlobalConfigOps(exists=True, show_pr_info=True)
    ctx = create_test_context(global_config_ops=config_ops)

    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()

    collector = GitHubPRCollector()
    assert collector.is_available(ctx, worktree_path) is True


def test_github_pr_collector_collect_no_branch(tmp_path: Path) -> None:
    """Test collect() returns None when get_current_branch returns None."""
    git_ops = FakeGitOps(current_branches={})
    ctx = create_test_context(git_ops=git_ops)

    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    collector = GitHubPRCollector()
    result = collector.collect(ctx, worktree_path, repo_root)

    assert result is None


def test_github_pr_collector_collect_no_pr_found(tmp_path: Path) -> None:
    """Test collect() returns None when no PR found."""
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    git_ops = FakeGitOps(
        current_branches={worktree_path: "feature"}, git_common_dirs={repo_root: repo_root / ".git"}
    )
    graphite_ops = FakeGraphiteOps()
    github_ops = FakeGitHubOps(prs={})
    ctx = create_test_context(git_ops=git_ops, graphite_ops=graphite_ops, github_ops=github_ops)

    collector = GitHubPRCollector()
    result = collector.collect(ctx, worktree_path, repo_root)

    assert result is None


def test_github_pr_collector_collect_uses_graphite_data(tmp_path: Path) -> None:
    """Test collect() uses Graphite data when available (fast path)."""
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    git_ops = FakeGitOps(
        current_branches={worktree_path: "feature"}, git_common_dirs={repo_root: repo_root / ".git"}
    )

    pr_data = PullRequestInfo(
        number=123,
        state="OPEN",
        url="https://github.com/owner/repo/pull/123",
        is_draft=False,
        checks_passing=True,
        owner="owner",
        repo="repo",
    )
    graphite_ops = FakeGraphiteOps(pr_info={"feature": pr_data})
    github_ops = FakeGitHubOps(prs={})
    ctx = create_test_context(git_ops=git_ops, graphite_ops=graphite_ops, github_ops=github_ops)

    collector = GitHubPRCollector()
    result = collector.collect(ctx, worktree_path, repo_root)

    assert result is not None
    assert result.number == 123
    assert result.url == "https://github.com/owner/repo/pull/123"


def test_github_pr_collector_collect_falls_back_to_github(tmp_path: Path) -> None:
    """Test collect() falls back to GitHub when Graphite unavailable."""
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    git_ops = FakeGitOps(
        current_branches={worktree_path: "feature"}, git_common_dirs={repo_root: repo_root / ".git"}
    )
    graphite_ops = FakeGraphiteOps()
    github_ops = FakeGitHubOps(
        prs={
            "feature": PullRequestInfo(
                number=456,
                state="OPEN",
                url="https://github.com/owner/repo/pull/456",
                is_draft=False,
                checks_passing=True,
                owner="owner",
                repo="repo",
            )
        }
    )
    ctx = create_test_context(git_ops=git_ops, graphite_ops=graphite_ops, github_ops=github_ops)

    collector = GitHubPRCollector()
    result = collector.collect(ctx, worktree_path, repo_root)

    assert result is not None
    assert result.number == 456
    assert result.url == "https://github.com/owner/repo/pull/456"


def test_github_pr_collector_ready_to_merge_true(tmp_path: Path) -> None:
    """Test ready_to_merge=True when OPEN, not draft, checks passing."""
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    git_ops = FakeGitOps(current_branches={worktree_path: "feature"})
    github_ops = FakeGitHubOps(
        prs={
            "feature": PullRequestInfo(
                number=123,
                state="OPEN",
                url="https://github.com/owner/repo/pull/123",
                is_draft=False,
                checks_passing=True,
                owner="owner",
                repo="repo",
            )
        }
    )
    ctx = create_test_context(git_ops=git_ops, github_ops=github_ops)

    collector = GitHubPRCollector()
    result = collector.collect(ctx, worktree_path, repo_root)

    assert result is not None
    assert result.ready_to_merge is True
    assert result.state == "OPEN"
    assert result.is_draft is False
    assert result.checks_passing is True


def test_github_pr_collector_ready_to_merge_false_draft(tmp_path: Path) -> None:
    """Test ready_to_merge=False when PR is draft."""
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    git_ops = FakeGitOps(current_branches={worktree_path: "feature"})
    github_ops = FakeGitHubOps(
        prs={
            "feature": PullRequestInfo(
                number=123,
                state="OPEN",
                url="https://github.com/owner/repo/pull/123",
                is_draft=True,
                checks_passing=True,
                owner="owner",
                repo="repo",
            )
        }
    )
    ctx = create_test_context(git_ops=git_ops, github_ops=github_ops)

    collector = GitHubPRCollector()
    result = collector.collect(ctx, worktree_path, repo_root)

    assert result is not None
    assert result.ready_to_merge is False
    assert result.is_draft is True


def test_github_pr_collector_ready_to_merge_false_checks_failing(tmp_path: Path) -> None:
    """Test ready_to_merge=False when checks failing."""
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    git_ops = FakeGitOps(current_branches={worktree_path: "feature"})
    github_ops = FakeGitHubOps(
        prs={
            "feature": PullRequestInfo(
                number=123,
                state="OPEN",
                url="https://github.com/owner/repo/pull/123",
                is_draft=False,
                checks_passing=False,
                owner="owner",
                repo="repo",
            )
        }
    )
    ctx = create_test_context(git_ops=git_ops, github_ops=github_ops)

    collector = GitHubPRCollector()
    result = collector.collect(ctx, worktree_path, repo_root)

    assert result is not None
    assert result.ready_to_merge is False
    assert result.checks_passing is False


def test_github_pr_collector_ready_to_merge_true_checks_unknown(tmp_path: Path) -> None:
    """Test ready_to_merge=True when checks_passing=None (no check data available)."""
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    git_ops = FakeGitOps(current_branches={worktree_path: "feature"})
    github_ops = FakeGitHubOps(
        prs={
            "feature": PullRequestInfo(
                number=123,
                state="OPEN",
                url="https://github.com/owner/repo/pull/123",
                is_draft=False,
                checks_passing=None,
                owner="owner",
                repo="repo",
            )
        }
    )
    ctx = create_test_context(git_ops=git_ops, github_ops=github_ops)

    collector = GitHubPRCollector()
    result = collector.collect(ctx, worktree_path, repo_root)

    assert result is not None
    assert result.ready_to_merge is True
    assert result.checks_passing is None
