from pathlib import Path

from dot_agent_kit import __version__
from dot_agent_kit.config import (
    DotAgentConfig,
    get_config_path,
    parse_markdown_frontmatter,
)


def test_default_config_uses_package_version() -> None:
    config = DotAgentConfig.default()
    assert config.version == __version__
    assert any(f.startswith("tools/") for f in config.managed_files)


def test_save_and_reload_round_trip(tmp_path: Path) -> None:
    agent_dir = tmp_path / ".agent"
    agent_dir.mkdir()

    config = DotAgentConfig.default()
    config_path = get_config_path(agent_dir)

    config.save(config_path)
    loaded = DotAgentConfig.load(config_path)

    assert loaded == config


def test_load_handles_missing_file(tmp_path: Path) -> None:
    config_path = tmp_path / ".agent" / ".dot-agent-kit.yml"
    loaded = DotAgentConfig.load(config_path)

    assert loaded.managed_files
    assert loaded.exclude == ()


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
