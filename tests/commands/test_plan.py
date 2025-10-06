import os
import subprocess
from pathlib import Path


def test_create_with_plan_file(tmp_path: Path) -> None:
    """Test creating a worktree from a plan file."""
    # Set up isolated global config
    global_config_dir = tmp_path / ".workstack"
    global_config_dir.mkdir()
    workstacks_root = tmp_path / "workstacks"
    (global_config_dir / "config.toml").write_text(
        f'workstacks_root = "{workstacks_root}"\nuse_graphite = false\n'
    )

    # Set up a fake git repo
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)

    # Create an initial commit
    (repo / "README.md").write_text("test")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo, check=True)

    # Create a plan file
    plan_file = repo / "Add_Auth_Feature.md"
    plan_content = "# Auth Feature Plan\n\n- Add login\n- Add signup\n"
    plan_file.write_text(plan_content)

    # Run workstack create with --plan, using isolated config
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    result = subprocess.run(
        ["uv", "run", "workstack", "create", "--plan", "Add_Auth_Feature.md", "--no-post"],
        cwd=repo,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0, f"Command failed: {result.stderr}"

    # Verify worktree was created with sanitized name
    worktree_path = workstacks_root / "repo" / "add-auth-feature"
    assert worktree_path.exists()
    assert worktree_path.is_dir()

    # Verify plan file was moved to .PLAN.md in worktree
    plan_dest = worktree_path / ".PLAN.md"
    assert plan_dest.exists()
    assert plan_dest.read_text() == plan_content

    # Verify original plan file was moved (not copied)
    assert not plan_file.exists()

    # Verify .env was created
    assert (worktree_path / ".env").exists()


def test_create_with_plan_name_sanitization(tmp_path: Path) -> None:
    """Test that plan filename gets properly sanitized for worktree name."""
    # Set up isolated global config
    global_config_dir = tmp_path / ".workstack"
    global_config_dir.mkdir()
    workstacks_root = tmp_path / "workstacks"
    (global_config_dir / "config.toml").write_text(
        f'workstacks_root = "{workstacks_root}"\nuse_graphite = false\n'
    )

    # Set up a fake git repo
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)

    # Create an initial commit
    (repo / "README.md").write_text("test")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo, check=True)

    # Create a plan file with underscores and mixed case
    plan_file = repo / "MY_COOL_Plan_File.md"
    plan_file.write_text("# Cool Plan\n")

    # Run workstack create with --plan, using isolated config
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    result = subprocess.run(
        ["uv", "run", "workstack", "create", "--plan", "MY_COOL_Plan_File.md", "--no-post"],
        cwd=repo,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0, f"Command failed: {result.stderr}"

    # Verify worktree name is lowercase with hyphens
    worktree_path = workstacks_root / "repo" / "my-cool-plan-file"
    assert worktree_path.exists()

    # Verify plan was moved
    assert (worktree_path / ".PLAN.md").exists()
    assert not plan_file.exists()


def test_create_with_both_name_and_plan_fails(tmp_path: Path) -> None:
    """Test that providing both NAME and --plan is an error."""
    # Set up a fake git repo
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)

    # Create an initial commit
    (repo / "README.md").write_text("test")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo, check=True)

    # Create a plan file
    plan_file = repo / "plan.md"
    plan_file.write_text("# Plan\n")

    # Run workstack create with both NAME and --plan
    result = subprocess.run(
        ["uv", "run", "workstack", "create", "myname", "--plan", "plan.md"],
        cwd=repo,
        capture_output=True,
        text=True,
    )

    # Should fail
    assert result.returncode != 0
    assert (
        "Cannot specify both NAME and --plan" in result.stdout
        or "Cannot specify both NAME and --plan" in result.stderr
    )


def test_create_rejects_reserved_name_root(tmp_path: Path) -> None:
    """Test that 'root' is rejected as a reserved worktree name."""
    # Set up isolated global config
    global_config_dir = tmp_path / ".workstack"
    global_config_dir.mkdir()
    workstacks_root = tmp_path / "workstacks"
    (global_config_dir / "config.toml").write_text(
        f'workstacks_root = "{workstacks_root}"\nuse_graphite = false\n'
    )

    # Set up a fake git repo
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)

    # Create an initial commit
    (repo / "README.md").write_text("test")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo, check=True)

    # Try to create a worktree named "root"
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    result = subprocess.run(
        ["uv", "run", "workstack", "create", "root", "--no-post"],
        cwd=repo,
        capture_output=True,
        text=True,
        env=env,
    )

    # Should fail with reserved name error
    assert result.returncode != 0
    assert "root" in result.stderr.lower() and "reserved" in result.stderr.lower(), (
        f"Expected error about 'root' being reserved, got: {result.stderr}"
    )

    # Verify worktree was not created
    worktree_path = workstacks_root / "repo" / "root"
    assert not worktree_path.exists()


def test_create_rejects_reserved_name_root_case_insensitive(tmp_path: Path) -> None:
    """Test that 'ROOT', 'Root', etc. are also rejected (case-insensitive)."""
    # Set up isolated global config
    global_config_dir = tmp_path / ".workstack"
    global_config_dir.mkdir()
    workstacks_root = tmp_path / "workstacks"
    (global_config_dir / "config.toml").write_text(
        f'workstacks_root = "{workstacks_root}"\nuse_graphite = false\n'
    )

    # Set up a fake git repo
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)

    # Create an initial commit
    (repo / "README.md").write_text("test")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo, check=True)

    # Test various cases of "root"
    for name_variant in ["ROOT", "Root", "RoOt"]:
        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        result = subprocess.run(
            ["uv", "run", "workstack", "create", name_variant, "--no-post"],
            cwd=repo,
            capture_output=True,
            text=True,
            env=env,
        )

        # Should fail with reserved name error
        assert result.returncode != 0, f"Expected failure for name '{name_variant}'"
        assert "reserved" in result.stderr.lower(), (
            f"Expected error about 'root' being reserved for '{name_variant}', got: {result.stderr}"
        )


def test_create_rejects_main_as_worktree_name(tmp_path: Path) -> None:
    """Test that 'main' is rejected as a worktree name."""
    # Set up isolated global config
    global_config_dir = tmp_path / ".workstack"
    global_config_dir.mkdir()
    workstacks_root = tmp_path / "workstacks"
    (global_config_dir / "config.toml").write_text(
        f'workstacks_root = "{workstacks_root}"\nuse_graphite = false\n'
    )

    # Set up a fake git repo
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)

    # Create an initial commit
    (repo / "README.md").write_text("test")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo, check=True)

    # Try to create a worktree named "main"
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    result = subprocess.run(
        ["uv", "run", "workstack", "create", "main", "--no-post"],
        cwd=repo,
        capture_output=True,
        text=True,
        env=env,
    )

    # Should fail with error suggesting to use root
    assert result.returncode != 0
    assert "main" in result.stderr.lower()
    assert "workstack switch root" in result.stderr

    # Verify worktree was not created
    worktree_path = workstacks_root / "repo" / "main"
    assert not worktree_path.exists()


def test_create_rejects_master_as_worktree_name(tmp_path: Path) -> None:
    """Test that 'master' is rejected as a worktree name."""
    # Set up isolated global config
    global_config_dir = tmp_path / ".workstack"
    global_config_dir.mkdir()
    workstacks_root = tmp_path / "workstacks"
    (global_config_dir / "config.toml").write_text(
        f'workstacks_root = "{workstacks_root}"\nuse_graphite = false\n'
    )

    # Set up a fake git repo
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)

    # Create an initial commit
    (repo / "README.md").write_text("test")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo, check=True)

    # Try to create a worktree named "master"
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    result = subprocess.run(
        ["uv", "run", "workstack", "create", "master", "--no-post"],
        cwd=repo,
        capture_output=True,
        text=True,
        env=env,
    )

    # Should fail with error suggesting to use root
    assert result.returncode != 0
    assert "master" in result.stderr.lower()
    assert "workstack switch root" in result.stderr

    # Verify worktree was not created
    worktree_path = workstacks_root / "repo" / "master"
    assert not worktree_path.exists()
