# Agentic Programming Best Practices

Best practices for structuring code to be amenable to AI-assisted engineering.

---

## Introduction

This document presents best practices for **agentic programming** - the art of structuring code and development processes to maximize effectiveness when working with AI assistants.

### What is Agentic Programming?

Agentic programming is an emerging discipline focused on making codebases and workflows optimally compatible with AI-assisted development. It recognizes that AI agents have unique strengths and constraints:

- **Limited context windows** requiring efficient information architecture
- **Stateless interactions** needing persistent artifacts for continuity
- **Pattern recognition capabilities** that benefit from consistent structures
- **Parallel processing potential** when tasks are properly decomposed

### Document Philosophy

These practices are opinionated and prescriptive. They represent patterns that have proven effective across multiple projects and teams. Not every pattern will apply to every codebase, but understanding the principles will help you make informed decisions about your own AI-assisted development workflow.

---

## Table of Contents

1. [Coarse-grained Parallel Modules](#coarse-grained-parallel-modules) - Organize code into independent, self-contained modules for efficient context management and safe disposability.

2. [Agent Documentation: The `.agent` Directory](#agent-documentation-the-agent-directory) - Create a token cache of persistent knowledge that agents can reference instead of rediscovering.

3. [Planning: Iterative Design Before Implementation](#planning-iterative-design-before-implementation) - Invest in iterative planning with persistent artifacts before implementation to reduce context thrashing and to increased the complexity of tasks that can be performed autonomously.

4. [Authoring Guidelines](#authoring-guidelines) - Guidelines for maintaining this document with professional tone and clear structure.

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

### Benefits

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

Include metadata and/or comments that makes features self-describing and discoverable.

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

This pattern applies broadly to any system with parallel, independent features, such as:

- **CLI Commands**: One command per file with complete implementation
- **API Endpoints**: One endpoint/resource per file
- **Event Handlers**: One handler per file with its logic
- **Report Generators**: One report type per file
- **Data Processors**: One processing pipeline per file
- **Migration Scripts**: One migration per file

The key characteristic: features that can be added, modified, or removed independently without affecting sibling features.

---

## Agent Documentation: The `.agent` Directory

### Core Principle

The `.agent` directory serves as a **token cache** - a persistent store of understanding that agents have already computed. This prevents redundant analysis, reduces context window pollution, and accelerates future agent work.

### The Token Cache Concept

Agents repeatedly consume thousands of tokens to understand the same patterns, conventions, and architectural decisions across sessions. Instead, when an agent invests significant tokens to achieve deep understanding, persist that understanding in `.agent` for future reuse. Pre-materialized knowledge that transforms expensive discovery into cheap retrieval.

The cache term is useful as there are _levels_ to caching. For example you can think of CLAUDE.md as an L0 cache, a QUICK_REFERENCE.md as an L1 cache, EXCEPTION_HANDLING.md as an L2 cache, and so forth. Caches also get invalidated and must be recomputed or refilled, just as these documents do.

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

Example:

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

- Tools that assume that .agent is programmatically recomputed will blow away human-authored changes.
- Humans rarely look in `.agent` directory
- Agents don't need tutorials, they need structured references
- Wastes context window on conversational fluff
- Belongs in `README.md` or `docs/` instead

**Correct placement:** Root `README.md` or `docs/CONTRIBUTING.md` for humans, `.agent/docs/` for machine-optimized references.

---

## Planning: Iterative Design Before Implementation

### Core Principle

Invest in planning before implementation for non-trivial or complex tasks. A well-crafted plan saves time and reduces context thrashing during execution. Think of plans as execution blueprints - detailed specifications that enable efficient, autonomous agent work.

### Key Pattern: Plans as Persistent Artifacts

For non-trivial tasks, persist plans as `.md` files. This enables:

- **Context management** across multiple agent sessions
- **Model flexibility** - switch between planning models (o1, Claude) and execution models
- **Progress tracking** through complex multi-step implementations
- **Clear boundaries** between design thinking and implementation

### Planning Best Practices

#### 1. Iterate on the Plan

Plans often require iteration. Precise planning can save lots of time later. Fix errors in plans is cheaper than fixing errors in implementations.

#### 2. Persist Non-Trivial Plans

For non-trivial tasks requiring more than 30 minutes of implementation, consider creating a persistent plan:

```
project/
├── src/              # Source code
├── docs/             # User documentation
├── plan.md           # Current working plan (git-ignored)
└── .gitignore        # Contains: plan.md, *_plan.md, plans/
```

Benefits of persistent plans:

- **Context preservation** - No need to re-explain the task to agents
- **Session flexibility** - Switch between agents or models mid-task
- **Progress visibility** - Clear checklist of completed work
- **Debugging reference** - Original intent remains accessible

#### 3. Keep Plans Out of Version Control

Plans should not be checked into repositories. In practice this confuses human reviewers and they become out-of-date quickly.

#### 4. Two-Phase Planning for Complex Features

For features touching multiple components or requiring architectural decisions, consider a two-phase approach:

**Phase 1: Specification Document** (Focus: What and Why)

- Overview of the feature without implementation details
- Functional requirements, constraints, and security considerations
- API design with interfaces and data flows
- Architecture decisions with rationale, alternatives considered, and accepted tradeoffs

**Phase 2: Implementation Plan** (Focus: How)

- Pre-implementation checklist (dependencies, environment, documentation review)
- Step-by-step implementation with specific files and patterns
- Context requirements (files to load, patterns to follow, external docs)
- Testing strategy (unit, integration, performance benchmarks)

This separation enables:

- Different tools optimized for each phase
- Reduced cognitive load during implementation
- Clear decision documentation before coding

---

## Authoring Guidelines

This section provides guidance for maintaining and extending this document. Following these guidelines ensures consistency and readability.

### Tone and Voice

#### Professional and Informative

Write clearly and directly without unnecessary dramatization:

- Use clear, straightforward language
- Avoid emphatic words like "CRITICAL", "MUST", "NEVER"
- Present information objectively - let the content speak for itself
- Write for intelligent readers - assume technical competence without being condescating
- Do not inject numeric estimates (e.g. if task is over 30 minutes, do X. Spend Y% of time doing Z.)
- Bias towards brevity. This is a high-level guide.

#### Examples over Prescriptions

Prefer showing over telling:

Instead of: "You MUST NEVER use try/except for control flow!"
Write: "Avoid using try/except for control flow. Check conditions explicitly instead."

Instead of: "CRITICAL INSIGHT: This pattern is essential!"
Write: "This pattern has proven effective across multiple projects."

### Structure and Format

#### Section Organization

Each major section should include:

1. **Core Principle** - One-paragraph summary of the main idea
2. **Key Pattern** - The primary implementation approach
3. **Detailed Explanation** - How and why it works
4. **Examples** - Concrete implementations
5. **Anti-patterns** - What to avoid and why

#### Heading Hierarchy

- `#` Document title only
- `##` Major sections (appear in table of contents)
- `###` Subsections within major sections
- `####` Specific topics within subsections

#### Code Examples

Provide practical, contextualized examples:

```python
# Good: Complete example with context
def search_content(query: str, filters: dict) -> list:
    """Search content with optional filters."""
    results = index.search(query)
    if filters:
        results = apply_filters(results, filters)
    return results

# Less helpful: Fragment without context
results = search(q)  # What is q? What does search return?
```

#### Language-Agnostic When Possible

Use generic examples that apply across languages:

```
project/
├── src/           # Source code
├── tests/         # Test files
├── docs/          # Documentation
└── plan.md        # Working plan (not committed)
```

When language-specific examples are needed, clearly indicate the language.

#### Balance Between Abstract and Concrete

- **Start with the concept** - Explain the principle
- **Provide concrete examples** - Show real implementations
- **Return to abstraction** - Summarize how to apply broadly
