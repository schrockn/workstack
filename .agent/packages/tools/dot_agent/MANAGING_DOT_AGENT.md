---
description: Rules and guidelines for managing .agent/ directories
---

# Managing the .agent Directory

This document defines rules for managing `.agent/` directories and explains which files can be edited versus which are managed by dot-agent-kit.

## Directory Structure

```
.agent/
├── packages/                   # MANAGED - DO NOT EDIT
│   ├── agentic_programming_guide/
│   │   └── AGENTIC_PROGRAMMING.md
│   └── tools/
│       ├── dot_agent/
│       ├── gh/
│       ├── gt/
│       └── workstack/
├── README.md                   # Project-specific (safe to edit)
├── ARCHITECTURE.md             # Project-specific (safe to edit)
└── *.md                        # Any custom files (safe to edit)
```

## 🔴 Critical Rules

### Rule 1: Never Edit Package Files

**Files in `.agent/packages/` are managed by dot-agent-kit and MUST NOT be edited directly.**

❌ **DO NOT**:

- Edit any file under `.agent/packages/`
- Modify tool documentation in `packages/tools/`
- Update guides in `packages/agentic_programming_guide/`
- Delete package files manually
- Copy package files from other projects

✅ **INSTEAD**:

- Use `dot-agent sync` to update packages
- Create custom documentation at `.agent/` root level
- Report issues or suggest changes to dot-agent-kit repository

### Rule 2: Verify Package Integrity

**Run `dot-agent check` to verify package files match bundled versions.**

The check command reports:

- **Modified files**: Package files that have been edited (❌ violation)
- **Missing files**: Package files that should exist but don't
- **Up-to-date files**: Package files matching bundled versions (✅ correct)

If `dot-agent check` reports modified files, run `dot-agent sync` to restore them.

### Rule 3: Root-Level Files Are Yours

**Files at `.agent/` root level are project-specific and safe to edit.**

These files will NEVER be touched by `dot-agent sync`:

- `ARCHITECTURE.md` - Your architecture documentation
- `CUSTOM_RULES.md` - Your project-specific rules
- `GLOSSARY.md` - Your domain terminology
- Any other `.md` files you create

## Why Package Files Are Immutable

### 1. Consistency Across Updates

When dot-agent-kit releases updates with improved documentation:

- All projects get the improvements automatically via `dot-agent sync`
- Local modifications would be lost or create conflicts
- Immutability ensures predictable update behavior

### 2. Shared Knowledge Base

Package files provide consistent, vetted documentation:

- AI agents rely on accurate, up-to-date information
- Local modifications create inconsistency between projects
- Shared packages benefit from community improvements

### 3. Clean Separation of Concerns

- **Packages**: General, reusable documentation managed by dot-agent-kit
- **Root files**: Project-specific context managed by you

This separation keeps roles clear and prevents confusion.

## Common Scenarios

### Scenario 1: Package Documentation Is Wrong

**Problem**: You found an error in `packages/tools/gt/gt.md`.

**❌ Wrong approach**: Edit the file directly.

**✅ Correct approach**:

1. Report the issue to dot-agent-kit repository
2. Create temporary workaround at `.agent/GT_WORKAROUND.md`
3. Wait for fix in next dot-agent-kit release
4. Run `dot-agent sync` to get the fix
5. Delete your workaround file

### Scenario 2: Need Project-Specific Tool Notes

**Problem**: Your project uses `gt` in a special way not covered by `packages/tools/gt/gt.md`.

**❌ Wrong approach**: Edit `packages/tools/gt/gt.md`.

**✅ Correct approach**:

1. Create `.agent/PROJECT_GT_USAGE.md`
2. Document your project-specific patterns
3. Reference the package docs: "See `packages/tools/gt/gt.md` for general usage"

### Scenario 3: Package File Is Outdated

**Problem**: You upgraded dot-agent-kit and packages aren't updated.

**❌ Wrong approach**: Copy files from another project.

**✅ Correct approach**:

```bash
dot-agent sync  # Updates all packages to current version
```

### Scenario 4: Accidentally Edited Package File

**Problem**: You modified `packages/tools/gh/gh.md` by mistake.

**Solution**:

```bash
# Check what's been modified
dot-agent check

# Restore to bundled version
dot-agent sync

# Verify restoration
dot-agent check
```

## Enforcement

### Manual Verification

Run `dot-agent check` before committing:

```bash
dot-agent check
# Exit code 0: All packages intact
# Exit code 1: Packages modified (fix before committing)
```

### CI/CD Integration

Add to your CI pipeline:

```yaml
# .github/workflows/validate.yml
- name: Verify .agent integrity
  run: |
    uv tool install dot-agent-kit
    dot-agent check
```

This prevents modified package files from being merged.

### Git Hooks

Add a pre-commit hook (optional):

```bash
#!/bin/sh
# .git/hooks/pre-commit
if ! dot-agent check; then
  echo "Error: .agent/packages/ files have been modified"
  echo "Run 'dot-agent sync' to restore them"
  exit 1
fi
```

## What Happens If You Edit Package Files

### During Sync

`dot-agent sync` will:

1. Detect the modification (shows in diff)
2. Overwrite with bundled version
3. Your changes are lost

### During Check

`dot-agent check` will:

1. Report file as "Modified"
2. Exit with code 1 (failure)
3. CI/CD pipelines will fail

### Long-Term Consequences

- Your changes disappear on next sync
- Other developers get confused by inconsistent state
- AI agents receive inconsistent information
- Merge conflicts with upstream updates

## Best Practices

### DO

✅ Run `dot-agent check` regularly
✅ Include check in CI/CD pipelines
✅ Create custom documentation at root level
✅ Use `exclude` for unneeded packages
✅ Report issues to dot-agent-kit repository
✅ Run `dot-agent sync` after upgrading dot-agent-kit

### DON'T

❌ Edit files under `packages/`
❌ Delete package files manually
❌ Commit modified package files
❌ Copy package files between projects
❌ Ignore `dot-agent check` failures

## Summary

The `.agent/` directory separates managed packages from project-specific documentation:

**Managed (packages/)**:

- Provided by dot-agent-kit
- Updated via `dot-agent sync`
- Verified via `dot-agent check`
- Never edit directly

**Project-Specific (root level)**:

- Created by you
- Managed by you
- Never touched by sync
- Edit freely

This separation ensures consistent, reliable documentation while preserving your project's unique context.

## Additional Resources

- CLI reference: See `dot_agent.md` in this directory
- Agentic programming patterns: See `packages/agentic_programming_guide/AGENTIC_PROGRAMMING.md`
- Tool-specific docs: See `packages/tools/{tool-name}/`
