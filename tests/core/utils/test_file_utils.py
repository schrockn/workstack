"""Tests for file_utils.extract_plan_title."""

import pytest

from workstack.core.file_utils import extract_plan_title

PLAN_CASES = [
    pytest.param(
        "frontmatter_followed_by_heading",
        "plan.md",
        """---
title: Metadata
---

# Actual Title

Content here.
""",
        "Actual Title",
        id="frontmatter_followed_by_heading",
    ),
    pytest.param(
        "heading_on_first_line",
        "plan.md",
        "# First Heading\n\nContent.",
        "First Heading",
        id="heading_on_first_line",
    ),
    pytest.param(
        "deep_heading",
        "plan.md",
        "### Deep Heading\n\nContent.",
        "Deep Heading",
        id="deep_heading",
    ),
    pytest.param(
        "only_frontmatter",
        "plan.md",
        """---
title: Metadata
---
""",
        None,
        id="only_frontmatter",
    ),
    pytest.param(
        "no_heading",
        "plan.md",
        "Just some text without headings.",
        None,
        id="no_heading",
    ),
    pytest.param(
        "empty_file",
        "plan.md",
        "",
        None,
        id="empty_file",
    ),
    pytest.param(
        "empty_heading",
        "plan.md",
        "#\n\nContent.",
        None,
        id="empty_heading",
    ),
    pytest.param(
        "heading_with_whitespace",
        "plan.md",
        "#   Title With Spaces   \n\nContent.",
        "Title With Spaces",
        id="heading_with_whitespace",
    ),
    pytest.param(
        "second_heading_ignored",
        "plan.md",
        """# First Heading

Some content.

## Second Heading

More content.
""",
        "First Heading",
        id="second_heading_ignored",
    ),
    pytest.param(
        "missing_file",
        "nonexistent.md",
        None,
        None,
        id="missing_file",
    ),
]


@pytest.mark.parametrize(
    ("description", "filename", "contents", "expected"),
    PLAN_CASES,
)
def test_extract_plan_title_cases(tmp_path, description, filename, contents, expected):
    """Exercise extract_plan_title across the supported input variations."""
    plan = tmp_path / filename

    if contents is not None:
        plan.write_text(contents, encoding="utf-8")

    assert extract_plan_title(plan) == expected
