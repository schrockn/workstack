from mdstack.frontmatter import (
    build_mdstack_frontmatter,
    merge_frontmatter,
    parse_frontmatter,
    serialize_frontmatter,
    update_claude_md_frontmatter,
)


def test_parse_frontmatter_with_valid_yaml():
    """Test parsing valid YAML frontmatter."""
    content = """---
foo: bar
baz: 42
---
# Body content
Some text here
"""
    frontmatter, body = parse_frontmatter(content)

    assert frontmatter is not None
    assert frontmatter == {"foo": "bar", "baz": 42}
    assert body == "# Body content\nSome text here\n"


def test_parse_frontmatter_without_frontmatter():
    """Test parsing content without frontmatter."""
    content = "# Just a heading\n\nSome content"
    frontmatter, body = parse_frontmatter(content)

    assert frontmatter is None
    assert body == content


def test_parse_frontmatter_with_invalid_yaml():
    """Test parsing invalid YAML frontmatter."""
    content = """---
invalid: yaml: structure:
---
# Body
"""
    frontmatter, body = parse_frontmatter(content)

    # Invalid YAML should be treated as no frontmatter
    assert frontmatter is None
    assert body == content


def test_build_mdstack_frontmatter():
    """Test building mdstack frontmatter section."""
    frontmatter = build_mdstack_frontmatter(version="0.1.0")

    assert "mdstack" in frontmatter
    assert frontmatter["mdstack"]["version"] == "0.1.0"
    assert "generated_docs" in frontmatter["mdstack"]
    assert frontmatter["mdstack"]["generated_docs"]["tests"] == ".mdstack/TESTS.md"
    assert frontmatter["mdstack"]["generated_docs"]["lookup"] == ".mdstack/LOOKUP.md"
    assert (
        frontmatter["mdstack"]["generated_docs"]["architecture"]
        == ".mdstack/OBSERVED_ARCHITECTURE.md"
    )
    assert "instructions" in frontmatter["mdstack"]
    assert "AI Agent" in frontmatter["mdstack"]["instructions"]


def test_merge_frontmatter_with_none():
    """Test merging when existing frontmatter is None."""
    mdstack = build_mdstack_frontmatter()
    merged = merge_frontmatter(None, mdstack)

    assert merged == mdstack


def test_merge_frontmatter_preserves_existing():
    """Test that merging preserves existing frontmatter keys."""
    existing = {"author": "Alice", "date": "2024-01-01", "tags": ["python", "testing"]}
    mdstack = build_mdstack_frontmatter()

    merged = merge_frontmatter(existing, mdstack)

    # Should have both existing and mdstack keys
    assert merged["author"] == "Alice"
    assert merged["date"] == "2024-01-01"
    assert merged["tags"] == ["python", "testing"]
    assert "mdstack" in merged


def test_merge_frontmatter_updates_mdstack():
    """Test that merging updates existing mdstack section."""
    existing = {"mdstack": {"version": "0.0.1", "old_key": "value"}, "other": "data"}
    mdstack = build_mdstack_frontmatter(version="0.1.0")

    merged = merge_frontmatter(existing, mdstack)

    # Should update mdstack section completely
    assert merged["mdstack"]["version"] == "0.1.0"
    assert "old_key" not in merged["mdstack"]
    # Should preserve other keys
    assert merged["other"] == "data"


def test_serialize_frontmatter_with_none():
    """Test serializing with no frontmatter."""
    body = "# Just content\n\nNo frontmatter here"
    result = serialize_frontmatter(None, body)

    assert result == body


def test_serialize_frontmatter_with_data():
    """Test serializing with frontmatter."""
    frontmatter = {"foo": "bar", "number": 42}
    body = "# Content\n\nBody text"

    result = serialize_frontmatter(frontmatter, body)

    assert result.startswith("---\n")
    assert "foo: bar" in result
    assert "number: 42" in result
    assert result.endswith("---\n# Content\n\nBody text")


def test_update_claude_md_frontmatter_new_file():
    """Test updating frontmatter for new CLAUDE.md file."""
    content = "\n# AI Agent Instructions\n\n"
    updated = update_claude_md_frontmatter(content)

    # Should have frontmatter
    assert updated.startswith("---\n")
    assert "mdstack:" in updated
    assert "version:" in updated
    assert ".mdstack/TESTS.md" in updated
    # Should preserve body
    assert "# AI Agent Instructions" in updated


def test_update_claude_md_frontmatter_existing_content():
    """Test updating frontmatter preserves user content."""
    content = """# My Custom Instructions

This is important user content that should be preserved.

## More sections
- Item 1
- Item 2
"""
    updated = update_claude_md_frontmatter(content)

    # Should have frontmatter
    assert updated.startswith("---\n")
    assert "mdstack:" in updated

    # Should preserve all user content
    assert "# My Custom Instructions" in updated
    assert "important user content" in updated
    assert "## More sections" in updated
    assert "Item 1" in updated


def test_update_claude_md_frontmatter_preserves_existing_frontmatter():
    """Test that updating preserves other frontmatter keys."""
    content = """---
author: Alice
tags:
  - python
  - testing
custom_key: custom_value
---
# Content
User content here
"""
    updated = update_claude_md_frontmatter(content)

    # Should preserve existing frontmatter
    assert "author: Alice" in updated
    assert "tags:" in updated
    assert "python" in updated
    assert "custom_key: custom_value" in updated

    # Should add mdstack section
    assert "mdstack:" in updated
    assert ".mdstack/TESTS.md" in updated

    # Should preserve content
    assert "# Content" in updated
    assert "User content here" in updated


def test_update_claude_md_frontmatter_updates_existing_mdstack():
    """Test that updating replaces existing mdstack section."""
    content = """---
mdstack:
  version: "0.0.1"
  old_field: old_value
---
# Content
"""
    updated = update_claude_md_frontmatter(content, version="0.1.0")

    # Should update version
    assert "version: 0.1.0" in updated or "version: '0.1.0'" in updated

    # Should have new structure
    assert "generated_docs:" in updated
    assert ".mdstack/TESTS.md" in updated

    # Old field should be gone
    assert "old_field" not in updated
