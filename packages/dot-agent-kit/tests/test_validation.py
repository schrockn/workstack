"""Tests for artifact validation functionality."""

from dot_agent_kit.io.frontmatter import load_artifact, parse_frontmatter
from dot_agent_kit.models.artifact import ArtifactFrontmatter


def test_parse_valid_frontmatter():
    """Test parsing valid frontmatter."""
    content = """<!-- dot-agent-kit:
kit_id: test-dot-agent-kit
version: 1.0.0
type: command
tags: [test, example]
-->

# Test Command

Command content here.
"""

    frontmatter, body = parse_frontmatter(content)

    assert frontmatter is not None
    assert frontmatter.kit_id == "test-dot-agent-kit"
    assert frontmatter.version == "1.0.0"
    assert frontmatter.artifact_type == "command"
    assert frontmatter.tags == ["test", "example"]
    assert "# Test Command" in body
    assert "<!-- dot-agent-kit:" not in body


def test_parse_invalid_frontmatter():
    """Test parsing invalid frontmatter."""
    content = """<!-- dot-agent-kit:
invalid yaml: [
-->

Content
"""

    frontmatter, body = parse_frontmatter(content)

    assert frontmatter is None
    assert "<!-- dot-agent-kit:" in body  # Original content preserved


def test_validate_frontmatter():
    """Test frontmatter validation."""
    # Valid frontmatter
    valid = ArtifactFrontmatter(kit_id="test-dot-agent-kit", version="1.0.0")
    assert valid.validate() == []

    # Missing kit_id
    invalid = ArtifactFrontmatter(version="1.0.0")
    errors = invalid.validate()
    assert len(errors) == 1
    assert "kit_id" in errors[0]

    # Invalid kit_id format
    invalid_format = ArtifactFrontmatter(
        kit_id="InvalidKit",  # Should be lowercase with hyphens
        version="1.0.0",
    )
    errors = invalid_format.validate()
    assert len(errors) == 1
    assert "Invalid kit_id format" in errors[0]


def test_load_artifact_with_validation(tmp_path):
    """Test loading and validating an artifact file."""
    # Create valid artifact
    valid_content = """<!-- dot-agent-kit:
kit_id: test-dot-agent-kit
version: 1.0.0
-->

# Valid Command
"""

    valid_path = tmp_path / "valid.md"
    valid_path.write_text(valid_content)

    artifact = load_artifact(valid_path)
    assert artifact.is_valid
    assert artifact.frontmatter is not None
    assert artifact.frontmatter.kit_id == "test-dot-agent-kit"

    # Create invalid artifact
    invalid_content = """<!-- dot-agent-kit:
version: 1.0.0
-->

# Invalid Command (missing kit_id)
"""

    invalid_path = tmp_path / "invalid.md"
    invalid_path.write_text(invalid_content)

    artifact = load_artifact(invalid_path)
    assert not artifact.is_valid
    assert len(artifact.validation_errors) > 0
