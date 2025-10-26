import re

import yaml


def parse_frontmatter(content: str) -> tuple[dict[str, object] | None, str]:
    """
    Parse YAML frontmatter from markdown content.

    Returns tuple of (frontmatter_dict, body_content).
    If no frontmatter exists, returns (None, original_content).
    """
    # Check for frontmatter delimiters at start of file
    if not content.startswith("---\n"):
        return None, content

    # Find closing delimiter
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)
    if not match:
        return None, content

    yaml_content = match.group(1)
    body = match.group(2)

    try:
        frontmatter = yaml.safe_load(yaml_content)
        if not isinstance(frontmatter, dict):
            return None, content
        return frontmatter, body
    except yaml.YAMLError:
        # Invalid YAML, treat as no frontmatter
        return None, content


def build_mdstack_frontmatter(version: str = "0.1.0") -> dict[str, object]:
    """
    Build the mdstack frontmatter section.

    Returns dict with mdstack metadata and agent instructions.
    """
    return {
        "mdstack": {
            "version": version,
            "generated_docs": {
                "tests": ".mdstack/TESTS.md",
                "lookup": ".mdstack/LOOKUP.md",
                "architecture": ".mdstack/OBSERVED_ARCHITECTURE.md",
            },
            "instructions": (
                "AI Agent: This scope has generated documentation in .mdstack/\n"
                "\n"
                "When to consult generated docs:\n"
                "- tests: For test coverage, testing patterns, what functionality is validated\n"
                "- lookup: For semantic search, finding code by concept/capability\n"
                "- architecture: For module organization, patterns, data flow, extension points\n"
                "\n"
                "Consult these files when working in this scope for best results."
            ),
        }
    }


def merge_frontmatter(
    existing: dict[str, object] | None, mdstack: dict[str, object]
) -> dict[str, object]:
    """
    Merge mdstack frontmatter with existing frontmatter.

    Preserves all existing keys, updates only the mdstack section.
    """
    if existing is None:
        return mdstack

    # Make a copy to avoid mutating input
    merged = existing.copy()

    # Update mdstack section
    merged.update(mdstack)

    return merged


def serialize_frontmatter(frontmatter: dict[str, object] | None, body: str) -> str:
    """
    Serialize frontmatter and body into markdown content.

    If frontmatter is None, returns just the body.
    """
    if frontmatter is None:
        return body

    # Serialize YAML with nice formatting
    yaml_content = yaml.dump(
        frontmatter, default_flow_style=False, sort_keys=False, allow_unicode=True
    )

    # Construct full content with frontmatter delimiters
    return f"---\n{yaml_content}---\n{body}"


def update_claude_md_frontmatter(content: str, version: str = "0.1.0") -> str:
    """
    Update CLAUDE.md content with mdstack frontmatter.

    Adds or updates the mdstack section while preserving user content.
    """
    # Parse existing content
    existing_frontmatter, body = parse_frontmatter(content)

    # Build mdstack section
    mdstack_section = build_mdstack_frontmatter(version)

    # Merge with existing frontmatter
    merged = merge_frontmatter(existing_frontmatter, mdstack_section)

    # Serialize back to string
    return serialize_frontmatter(merged, body)
