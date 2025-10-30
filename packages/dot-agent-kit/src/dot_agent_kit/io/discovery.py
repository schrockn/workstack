"""Filesystem discovery utilities for installed artifacts."""

from pathlib import Path


def discover_installed_artifacts(project_dir: Path) -> dict[str, set[str]]:
    """Discover artifacts present in .claude/ directory.

    Scans the .claude/ directory structure to identify which kits have
    artifacts installed, without checking config files.

    Args:
        project_dir: Project root directory

    Returns:
        Dictionary mapping kit_id to set of artifact types found.
        Example: {"devrun": {"agent", "skill"}, "gt": {"command", "skill"}}
    """
    claude_dir = project_dir / ".claude"
    if not claude_dir.exists():
        return {}

    discovered: dict[str, set[str]] = {}

    # Scan each artifact type directory
    for artifact_type in ["agents", "commands", "skills"]:
        type_dir = claude_dir / artifact_type
        if not type_dir.exists():
            continue

        # Scan subdirectories to identify kits
        for item in type_dir.iterdir():
            if not item.is_dir():
                continue

            # For agents and commands, the parent directory name is the kit
            # For skills, we need to check if there's a SKILL.md file
            if artifact_type == "skills":
                # Skills have format: .claude/skills/skill-name/SKILL.md
                skill_file = item / "SKILL.md"
                if skill_file.exists():
                    # Extract kit from skill name prefix
                    # Examples: "devrun-make" -> "devrun", "gt-graphite" -> "gt"
                    kit_id = _extract_kit_from_skill_name(item.name)
                    if kit_id:
                        if kit_id not in discovered:
                            discovered[kit_id] = set()
                        discovered[kit_id].add("skill")
            elif artifact_type == "commands":
                # Commands have format: .claude/commands/kit-name/command.md
                kit_id = item.name
                if any(item.glob("*.md")):
                    if kit_id not in discovered:
                        discovered[kit_id] = set()
                    discovered[kit_id].add("command")
            elif artifact_type == "agents":
                # Agents have format: .claude/agents/kit-name/agent.md
                kit_id = item.name
                if any(item.glob("*.md")):
                    if kit_id not in discovered:
                        discovered[kit_id] = set()
                    discovered[kit_id].add("agent")

    return discovered


def _extract_kit_from_skill_name(skill_name: str) -> str | None:
    """Extract kit ID from skill name.

    Skills are named with kit prefix, like:
    - "devrun-make" -> "devrun"
    - "devrun-pytest" -> "devrun"
    - "gt-graphite" -> "gt"

    For skills without a clear kit prefix (standalone skills), returns the
    full skill name as the kit ID.

    Args:
        skill_name: Full skill directory name

    Returns:
        Kit ID - either extracted prefix or full skill name
    """
    # Known kit prefixes (bundled kits)
    known_prefixes = ["devrun", "gt"]

    # Check if skill starts with known prefix
    for prefix in known_prefixes:
        if skill_name.startswith(f"{prefix}-"):
            return prefix

    # For skills without known prefix, treat as standalone "kit"
    # This handles skills like "gh", "workstack", "skill-creator", etc.
    return skill_name
