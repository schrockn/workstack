# dot-agent-kit

Kit management system for Claude Code.

## Installation

```bash
pip install dot-agent-kit
```

## Usage

```bash
dot-agent --help
```

## Creating Kits

### Kit Structure

A kit is a collection of Claude Code artifacts (agents, skills, commands) distributed as a package. Each kit requires:

1. **kit.yaml** - Manifest file with kit metadata and artifact paths
2. **Artifacts** - The actual agent, skill, and command files

### Namespace Pattern (Required)

**All bundled kits** must follow the namespace pattern:

```
{artifact_type}s/{kit_name}/...
```

This organizational pattern:

- Prevents naming conflicts when multiple kits are installed
- Makes it clear which kit an artifact belongs to
- Enables clean uninstallation of kit artifacts
- Keeps the `.claude/` directory organized

**Example structure:**

```
my-kit/
├── kit.yaml
├── agents/
│   └── my-kit/
│       └── my-agent.md
└── skills/
    └── my-kit/
        ├── tool-a/
        │   └── SKILL.md
        └── tool-b/
            └── SKILL.md
```

**Example kit.yaml:**

```yaml
name: my-kit
version: 1.0.0
description: My awesome Claude Code kit
artifacts:
  agent:
    - agents/my-kit/my-agent.md
  skill:
    - skills/my-kit/tool-a/SKILL.md
    - skills/my-kit/tool-b/SKILL.md
```

### Invocation Names vs File Paths

**Important**: Claude Code discovers artifacts by their filename/directory name, not the full path:

- **Agents**: Discovered by filename (e.g., `agents/my-kit/helper.md` → invoked as "helper")
- **Skills**: Discovered by directory name (e.g., `skills/my-kit/pytest/SKILL.md` → invoked as "pytest")
- **Commands**: Discovered by filename (e.g., `commands/my-kit/build.md` → invoked as "/build")

The namespace directory (`my-kit/`) is **organizational only** - it doesn't become part of the invocation name.

### Namespace Requirement for Kit Types

**Bundled kits** (distributed with packages): Namespacing is **required** and enforced. Non-namespaced kits will fail to install.

**Project-local artifacts** (in `.claude/` not from kits): Namespacing is **optional**. These are project-specific and not distributed.

### Validation

Bundled kits are automatically validated for namespace compliance during installation. If artifacts don't follow the required pattern, installation will fail with a clear error:

```
ValueError: Bundled kit 'my-kit' does not follow required namespace pattern:
  - Artifact 'agents/helper.md' is not namespaced (too shallow).
    Expected pattern: agents/my-kit/...

All bundled kit artifacts must use the pattern: {type}s/my-kit/...
```

### Migration Guide

If you have an existing kit without namespacing:

1. **Create namespace directories:**

   ```bash
   mkdir -p agents/{kit-name}
   mkdir -p skills/{kit-name}
   mkdir -p commands/{kit-name}
   ```

2. **Move artifacts into namespaced directories:**

   ```bash
   mv agents/*.md agents/{kit-name}/
   mv skills/* skills/{kit-name}/
   ```

3. **Update kit.yaml artifact paths:**

   ```yaml
   artifacts:
     agent:
       - agents/{kit-name}/my-agent.md # Was: agents/my-agent.md
     skill:
       - skills/{kit-name}/my-skill/SKILL.md # Was: skills/my-skill/SKILL.md
   ```

4. **Test installation** to verify paths are correct
