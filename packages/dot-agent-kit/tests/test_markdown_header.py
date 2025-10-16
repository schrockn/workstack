from dot_agent_kit.markdown_header import parse_markdown_frontmatter


def test_parse_frontmatter_with_valid_yaml() -> None:
    content = """---
description: "Test description"
url: "https://example.com"
---

# Content

This is the body."""
    metadata, remaining = parse_markdown_frontmatter(content)

    assert metadata.description == "Test description"
    assert metadata.url == "https://example.com"
    assert remaining.startswith("# Content")


def test_parse_frontmatter_without_front_matter() -> None:
    content = """# No Front Matter

Just regular content."""
    metadata, remaining = parse_markdown_frontmatter(content)

    assert metadata.description is None
    assert metadata.url is None
    assert remaining == content


def test_parse_frontmatter_with_incomplete_fields() -> None:
    content = """---
description: "Only description"
---

# Content"""
    metadata, remaining = parse_markdown_frontmatter(content)

    assert metadata.description == "Only description"
    assert metadata.url is None


def test_parse_frontmatter_with_malformed_yaml() -> None:
    import pytest
    import yaml

    content = """---
description: "Missing closing quote
url: invalid
---

# Content"""

    # Should raise an exception for malformed YAML
    with pytest.raises(yaml.YAMLError):
        parse_markdown_frontmatter(content)


def test_parse_frontmatter_with_non_string_values() -> None:
    content = """---
description: 123
url: ["list", "of", "urls"]
---

# Content"""
    metadata, remaining = parse_markdown_frontmatter(content)

    # Should ignore non-string values
    assert metadata.description is None
    assert metadata.url is None
