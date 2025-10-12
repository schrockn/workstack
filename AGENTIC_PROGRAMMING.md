# Agentic Programming Best Practices

Best practices for structuring code to be amenable to AI-assisted engineering.

---

## Coarse-grained Parallel Modules

### Core Principle

Organize code into coarse-grained, parallel modules where each module handles a complete feature independently. This enables efficient agentic engineering through better context management, faster implementation, and safe disposability.

### Key Pattern: One Feature Per File

**Structure Example:** CLI Commands

```
commands/
├── list.py      # Complete 'list' command - self-contained
├── create.py    # Complete 'create' command - independent
├── delete.py    # Complete 'delete' command - isolated
└── update.py    # Complete 'update' command - standalone
```

### Three Critical Benefits

#### 1. Context Window Management

- Each module fits entirely within an agent's context window
- No need to load multiple files to understand one feature
- Reduces cross-file navigation and confusion

#### 2. Implementation Speed

- Agents can generate complete features in a single response
- No coordination needed between multiple files
- Parallel development - multiple features can be built simultaneously

#### 3. Disposability

- Failed implementations can be deleted with `rm feature.py`
- No cleanup or refactoring required
- No risk of breaking other features when removing code
- Experimentation becomes low-cost

### Self-Describing Features for Navigation

**Critical:** Include metadata that makes features self-describing and discoverable.

**Good Examples:**

```python
# CLI command with help text
@click.command("list")
@click.option("--format", help="Output format (json/table)")
def list_cmd():
    """List all available resources with filtering."""
    pass

# API endpoint with docstring
@app.route("/api/users")
def get_users():
    """GET /api/users - Retrieve paginated user list."""
    pass

# Plugin with manifest
class DataProcessor:
    """Process CSV files for reporting.

    Capabilities:
    - Input: CSV files up to 100MB
    - Output: JSON summary statistics
    - Performance: ~1000 rows/second
    """
```

This metadata enables:

- Quick discovery without reading implementation
- Automated documentation generation
- Faster agent navigation to relevant code
- Clear understanding of module capabilities

### Example Applications (Non-Exhaustive)

This pattern applies broadly to any system with parallel, independent features:

- **CLI Commands**: One command per file with complete implementation
- **API Endpoints**: One endpoint/resource per file
- **Event Handlers**: One handler per file with its logic
- **Report Generators**: One report type per file
- **Data Processors**: One processing pipeline per file
- **Migration Scripts**: One migration per file

The key characteristic: features that can be added, modified, or removed independently without affecting sibling features.

### Implementation Guidelines

- Keep modules under 500 lines for optimal context usage
- Include all imports and dependencies in each file
- Prefer duplication over shared utilities (within reason)
- Use dependency injection for truly shared resources
- Always include descriptive docstrings/help text

### Anti-Pattern to Avoid

```python
# DON'T: Multiple features interleaved in one file
cli_commands.py:
    def list_command(): ...
    def create_command(): ...
    def _shared_helper(): ...  # Used by multiple commands
    def delete_command(): ...
```

**Why this is problematic:**

When an agent breaks `create_command()`, removal becomes complex and risky. You cannot simply delete the broken code without:

- Checking if other commands depend on it
- Ensuring shared helpers aren't orphaned
- Verifying no cross-references exist
- Potentially refactoring the entire file

This violates the disposability principle and slows down agentic development.

---

## Agent Documentation: The `.agent` Directory

### Core Principle

The `.agent` directory serves as a **token cache** - a persistent store of understanding that agents have already computed. This prevents redundant analysis, reduces context window pollution, and accelerates future agent work.

### The Token Cache Concept

**Problem:** Agents repeatedly consume thousands of tokens to understand the same patterns, conventions, and architectural decisions across sessions.

**Solution:** When an agent invests significant tokens to achieve deep understanding, persist that understanding in `.agent` for future reuse.

**Think of it as:** Pre-computed knowledge that transforms expensive discovery into cheap retrieval.

### Structure Example

```
.agent/
├── docs/
│   ├── PATTERNS.md              # Code patterns with examples
│   ├── EXCEPTION_HANDLING.md    # Detailed exception philosophy
│   ├── QUICK_REFERENCE.md       # Fast lookup tables
│   └── GT_MENTAL_MODEL.md       # External tool mental models
├── prompts/
│   └── code_review_checklist.md # Reusable agent prompts
└── README.md                    # Directory purpose and index
```

### What Belongs in `.agent`

**Good candidates:**

- **Architectural decisions** - Why the codebase is structured a certain way
- **Pattern libraries** - Examples of correct implementations
- **Mental models** - How to reason about complex subsystems
- **Tool-specific guides** - How to work with external tools (e.g., Graphite)
- **Detailed explanations** - Deep dives that would otherwise require reading many files
- **Agent-specific prompts** - Reusable instruction templates

**Poor candidates:**

- User-facing documentation (belongs in root `docs/`)
- Getting started guides (belongs in `README.md`)
- API references (generate from code or use standard locations)
- Marketing content
- Anything requiring frequent human consumption

### Key Characteristics

#### 1. Agent-First Writing Style

Documentation optimized for AI consumption rather than human reading:

```markdown
<!-- GOOD: Imperative, structured, scannable -->

## Exception Handling Rules

🔴 MUST: Never use try/except for control flow
🟡 SHOULD: Check conditions with if statements
🟢 MAY: Catch at error boundaries only

<!-- LESS GOOD: Conversational, meandering -->

You know, exceptions are kind of tricky. We've found over time that it's
generally better to avoid using them for control flow because...
```

#### 2. Rich Examples Over Prose

Show, don't just tell:

````markdown
<!-- GOOD -->

## Path Operations

✅ CORRECT:

```python
if path.exists():
    resolved = path.resolve()
```
````

❌ WRONG:

```python
resolved = path.resolve()  # May fail if path doesn't exist
```

<!-- LESS GOOD -->

When working with paths, make sure to check existence first before resolving.

````

#### 3. Rapid Navigation

Include tables, checklists, and quick references:

```markdown
| If you're writing...    | Check this...                          |
|-------------------------|----------------------------------------|
| `try/except`            | → Exception Handling section           |
| Subprocess calls        | → Always use `check=True`              |
````

### Integration with Main Codebase Documentation

**CLAUDE.md (Root):** Quick reference, critical rules, links to `.agent` for details

```markdown
# CLAUDE.md

## Exception Handling

**NEVER use try/except for control flow.**

Full guide: [.agent/docs/EXCEPTION_HANDLING.md](.agent/docs/EXCEPTION_HANDLING.md)
```

**`.agent/docs/EXCEPTION_HANDLING.md`:** Comprehensive explanation, examples, edge cases

This two-tier approach gives agents a fast path (CLAUDE.md) and a deep path (.agent) without loading unnecessary context.

### Maintenance Guidelines

- **Update when understanding deepens** - Agent discovers new patterns worth caching
- **Refactor when documentation is consulted repeatedly** - Signal that knowledge is valuable
- **Delete when outdated** - Stale documentation is worse than missing documentation
- **Keep synchronized with CLAUDE.md** - Root file should link to `.agent` for details

### Known Risk: Documentation Drift

**Critical challenge:** `.agent` documentation can become outdated as the codebase evolves, leading agents to follow obsolete patterns or incorrect assumptions. Stale agent documentation is actively harmful - it wastes tokens and introduces bugs.

**Current state:** This is an **unsolved problem** in agentic engineering. We lack robust tooling to detect when `.agent` files diverge from actual code patterns. Current mitigation relies on manual review and agent prompting to verify documentation accuracy.

**Future solution space:** This problem requires proper tooling and workflows - automated drift detection, tests that validate documentation claims against code, and integration into CI/CD pipelines. Until then, treat `.agent` maintenance as a manual, high-priority task.

### Benefits Recap

1. **Context Window Efficiency** - Load understanding directly instead of deriving it
2. **Consistency** - All agents reference the same canonical patterns
3. **Speed** - Skip rediscovery phase and start implementation faster
4. **Accuracy** - Reduce misunderstandings from incomplete analysis
5. **Compound Value** - Each agent session can contribute to shared knowledge base

### Anti-Pattern: Human-Centric Documentation in `.agent`

```markdown
<!-- DON'T: Tutorial-style, beginner-focused -->

# Getting Started with Our Codebase

Welcome! We're excited to have you here. Let's walk through how to set up
your development environment step by step...
```

**Why this is problematic:**

- Humans rarely look in `.agent` directory
- Agents don't need tutorials, they need structured references
- Wastes context window on conversational fluff
- Belongs in `README.md` or `docs/` instead

**Correct placement:** Root `README.md` or `docs/CONTRIBUTING.md` for humans, `.agent/docs/` for machine-optimized references.
