"""File operation utilities."""

from pathlib import Path


def extract_plan_title(plan_path: Path) -> str | None:
    """Extract the first heading from a markdown plan file.

    Uses python-frontmatter library to properly parse YAML frontmatter,
    then extracts the first line starting with # from the content.

    Args:
        plan_path: Path to the .PLAN.md file

    Returns:
        The heading text (without the # prefix), or None if not found or file doesn't exist
    """
    if not plan_path.exists():
        return None

    import frontmatter

    # Parse file with frontmatter library (handles YAML frontmatter properly)
    post = frontmatter.load(str(plan_path))

    # Get the content (without frontmatter)
    content = post.content
    lines = content.splitlines()

    # Find first heading
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            # Remove all # symbols and strip whitespace
            title = stripped.lstrip("#").strip()
            if title:
                return title

    return None
