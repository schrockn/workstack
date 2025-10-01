from __future__ import annotations

from workstack.naming import (
    default_branch_for_worktree,
    sanitize_branch_component,
    sanitize_worktree_name,
)


def test_sanitize_branch_component_basic() -> None:
    assert sanitize_branch_component("Foo") == "foo"
    assert sanitize_branch_component(" Foo Bar ") == "foo-bar"
    assert sanitize_branch_component("A/B C") == "a/b-c"
    assert sanitize_branch_component("@@weird!!name??") == "weird-name"


def test_default_branch_for_worktree() -> None:
    assert default_branch_for_worktree("feature X") == "work/feature-x"
    assert default_branch_for_worktree("/ / ") == "work/work"


def test_sanitize_worktree_name() -> None:
    """Test worktree name sanitization with lowercase and underscore replacement."""
    assert sanitize_worktree_name("Foo") == "foo"
    assert sanitize_worktree_name("Add_Auth_Feature") == "add-auth-feature"
    assert sanitize_worktree_name("My_Cool_Plan") == "my-cool-plan"
    assert sanitize_worktree_name("FOO_BAR_BAZ") == "foo-bar-baz"
    assert (
        sanitize_worktree_name("feature__with___multiple___underscores")
        == "feature-with-multiple-underscores"
    )
    assert sanitize_worktree_name("name-with-hyphens") == "name-with-hyphens"
    assert sanitize_worktree_name("Mixed_Case-Hyphen_Underscore") == "mixed-case-hyphen-underscore"
    assert sanitize_worktree_name("@@weird!!name??") == "weird-name"
    assert sanitize_worktree_name("   spaces   ") == "spaces"
    assert sanitize_worktree_name("---") == "work"  # Empty result defaults to "work"
