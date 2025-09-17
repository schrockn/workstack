from __future__ import annotations

from workstack.naming import default_branch_for_worktree, sanitize_branch_component


def test_sanitize_branch_component_basic() -> None:
    assert sanitize_branch_component("Foo") == "foo"
    assert sanitize_branch_component(" Foo Bar ") == "foo-bar"
    assert sanitize_branch_component("A/B C") == "a/b-c"
    assert sanitize_branch_component("@@weird!!name??") == "weird-name"


def test_default_branch_for_worktree() -> None:
    assert default_branch_for_worktree("feature X") == "work/feature-x"
    assert default_branch_for_worktree("/ / ") == "work/work"
