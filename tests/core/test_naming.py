from workstack.cli.commands.create import (
    default_branch_for_worktree,
    sanitize_branch_component,
    sanitize_worktree_name,
    strip_plan_from_filename,
)


def test_sanitize_branch_component_basic() -> None:
    assert sanitize_branch_component("Foo") == "foo"
    assert sanitize_branch_component(" Foo Bar ") == "foo-bar"
    assert sanitize_branch_component("A/B C") == "a/b-c"
    assert sanitize_branch_component("@@weird!!name??") == "weird-name"


def test_default_branch_for_worktree() -> None:
    assert default_branch_for_worktree("feature X") == "feature-x"
    assert default_branch_for_worktree("/ / ") == "work"


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


def test_strip_plan_from_filename() -> None:
    """Test intelligent removal of 'plan' from filenames."""
    # Real-world examples
    assert strip_plan_from_filename("devclikit-extraction-plan") == "devclikit-extraction"

    # Basic cases - suffix
    assert strip_plan_from_filename("my-feature-plan") == "my-feature"

    # Basic cases - prefix
    assert strip_plan_from_filename("plan-for-auth") == "for-auth"

    # Position variations
    assert strip_plan_from_filename("plan-something") == "something"
    assert strip_plan_from_filename("something-plan") == "something"
    assert strip_plan_from_filename("something-plan-else") == "something-else"

    # Multiple occurrences
    assert strip_plan_from_filename("plan-my-plan-feature") == "my-feature"
    assert strip_plan_from_filename("my-plan-feature-plan") == "my-feature"

    # Edge case: only "plan" - should be preserved
    assert strip_plan_from_filename("plan") == "plan"

    # Separator variations
    assert strip_plan_from_filename("my_feature_plan") == "my_feature"
    assert strip_plan_from_filename("my feature plan") == "my feature"
    assert strip_plan_from_filename("my-feature_plan") == "my-feature"

    # Case variations
    assert strip_plan_from_filename("MY-FEATURE-PLAN") == "MY-FEATURE"
    assert strip_plan_from_filename("My-Feature-Plan") == "My-Feature"
    assert strip_plan_from_filename("my-feature-PLAN") == "my-feature"

    # Non-plan words should be preserved
    assert strip_plan_from_filename("airplane-feature") == "airplane-feature"
    assert strip_plan_from_filename("explain-system") == "explain-system"
    assert strip_plan_from_filename("planted-tree") == "planted-tree"

    # Plan variants should NOT be removed (only exact word "plan")
    assert strip_plan_from_filename("planning-session") == "planning-session"
    assert strip_plan_from_filename("plans-document") == "plans-document"

    # Leading/trailing separators after plan removal should be cleaned
    assert strip_plan_from_filename("-plan-feature") == "feature"
    assert strip_plan_from_filename("feature-plan-") == "feature"

    # Implementation plan variations - basic cases
    assert strip_plan_from_filename("my-feature-implementation-plan") == "my-feature"
    assert strip_plan_from_filename("implementation-plan-for-auth") == "for-auth"
    assert strip_plan_from_filename("implementation_plan_feature") == "feature"
    assert strip_plan_from_filename("feature implementation plan") == "feature"

    # Implementation plan with mixed separators
    assert strip_plan_from_filename("my-feature_implementation-plan") == "my-feature"
    assert strip_plan_from_filename("implementation_plan-for-auth") == "for-auth"

    # Implementation plan - case variations
    assert strip_plan_from_filename("IMPLEMENTATION-PLAN-FEATURE") == "FEATURE"
    assert strip_plan_from_filename("Implementation-Plan-Feature") == "Feature"
    assert strip_plan_from_filename("my-IMPLEMENTATION-plan") == "my"

    # Implementation plan in middle
    assert strip_plan_from_filename("my-implementation-plan-feature") == "my-feature"

    # Mixed leading "plan" with implementation plan phrase
    assert strip_plan_from_filename("plan-implementation-plan") == "implementation"
    assert strip_plan_from_filename("plan implementation plan") == "implementation"

    # Edge case: just "implementation-plan" becomes "implementation"
    # (Similar to how we would strip "plan" if there was other text)
    assert strip_plan_from_filename("implementation-plan") == "implementation"
    assert strip_plan_from_filename("implementation_plan") == "implementation"
    assert strip_plan_from_filename("IMPLEMENTATION-PLAN") == "IMPLEMENTATION"

    # Should not match "implementation" or "plan" separately when part of other words
    assert strip_plan_from_filename("reimplementation-feature") == "reimplementation-feature"
    assert strip_plan_from_filename("implantation-system") == "implantation-system"
