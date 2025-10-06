from pathlib import Path


def test_each_claude_md_has_agents_md_symlink() -> None:
    """Verify that every CLAUDE.md has a peer AGENTS.md that is a symbolic link to it."""
    repo_root = Path(__file__).parent.parent

    # Find all CLAUDE.md files
    claude_files = list(repo_root.rglob("CLAUDE.md"))

    # Ensure we found at least one (so test doesn't pass vacuously)
    assert len(claude_files) > 0, "Expected to find at least one CLAUDE.md file"

    for claude_file in claude_files:
        # Check for peer AGENTS.md
        agents_file = claude_file.parent / "AGENTS.md"

        assert agents_file.exists(), (
            f"Missing AGENTS.md peer for {claude_file.relative_to(repo_root)}"
        )

        assert agents_file.is_symlink(), (
            f"{agents_file.relative_to(repo_root)} exists but is not a symbolic link"
        )

        # Verify it points to CLAUDE.md
        link_target = agents_file.readlink()
        assert link_target == Path("CLAUDE.md"), (
            f"{agents_file.relative_to(repo_root)} points to '{link_target}', expected 'CLAUDE.md'"
        )
