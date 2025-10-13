"""Tests for file_utils.py."""

from pathlib import Path

from workstack.core.file_utils import extract_plan_title


def test_extract_plan_title_with_frontmatter(tmp_path: Path) -> None:
    """Test extracting title from plan with YAML frontmatter."""
    plan = tmp_path / "plan.md"
    plan.write_text(
        """---
title: Metadata
---

# Actual Title

Content here.
""",
        encoding="utf-8",
    )

    result = extract_plan_title(plan)
    assert result == "Actual Title"


def test_extract_plan_title_without_frontmatter(tmp_path: Path) -> None:
    """Test extracting title when heading is first line."""
    plan = tmp_path / "plan.md"
    plan.write_text("# First Heading\n\nContent.", encoding="utf-8")

    result = extract_plan_title(plan)
    assert result == "First Heading"


def test_extract_plan_title_multiple_hashes(tmp_path: Path) -> None:
    """Test extracting title from ### heading."""
    plan = tmp_path / "plan.md"
    plan.write_text("### Deep Heading\n\nContent.", encoding="utf-8")

    result = extract_plan_title(plan)
    assert result == "Deep Heading"


def test_extract_plan_title_no_heading(tmp_path: Path) -> None:
    """Test that None is returned when no heading exists."""
    plan = tmp_path / "plan.md"
    plan.write_text("Just some text without headings.", encoding="utf-8")

    result = extract_plan_title(plan)
    assert result is None


def test_extract_plan_title_missing_file(tmp_path: Path) -> None:
    """Test that None is returned for non-existent file."""
    plan = tmp_path / "nonexistent.md"

    result = extract_plan_title(plan)
    assert result is None


def test_extract_plan_title_empty_file(tmp_path: Path) -> None:
    """Test that None is returned for empty file."""
    plan = tmp_path / "plan.md"
    plan.write_text("", encoding="utf-8")

    result = extract_plan_title(plan)
    assert result is None


def test_extract_plan_title_empty_heading(tmp_path: Path) -> None:
    """Test that None is returned for heading with no text."""
    plan = tmp_path / "plan.md"
    plan.write_text("#\n\nContent.", encoding="utf-8")

    result = extract_plan_title(plan)
    assert result is None


def test_extract_plan_title_heading_with_whitespace(tmp_path: Path) -> None:
    """Test that heading with extra whitespace is properly trimmed."""
    plan = tmp_path / "plan.md"
    plan.write_text("#   Title With Spaces   \n\nContent.", encoding="utf-8")

    result = extract_plan_title(plan)
    assert result == "Title With Spaces"


def test_extract_plan_title_only_frontmatter(tmp_path: Path) -> None:
    """Test that None is returned when file only contains frontmatter."""
    plan = tmp_path / "plan.md"
    plan.write_text(
        """---
title: Metadata
---
""",
        encoding="utf-8",
    )

    result = extract_plan_title(plan)
    assert result is None


def test_extract_plan_title_second_heading_ignored(tmp_path: Path) -> None:
    """Test that only the first heading is extracted."""
    plan = tmp_path / "plan.md"
    plan.write_text(
        """# First Heading

Some content.

## Second Heading

More content.
""",
        encoding="utf-8",
    )

    result = extract_plan_title(plan)
    assert result == "First Heading"
