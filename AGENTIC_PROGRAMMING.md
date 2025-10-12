# Agentic Programming Best Practices

Best practices for structuring code to be amenable to AI-assisted engineering.

---

## Introduction

This document presents best practices for **agentic programming** - the art of structuring code and development processes to maximize effectiveness when working with AI assistants.

### What is Agentic Programming?

Agentic programming is an emerging discipline focused on making codebases and workflows optimally compatible with AI-assisted development. It recognizes that AI agents have unique strengths and constraints that fundamentally differ from human developers.

Agents work within limited context windows that require efficient information architecture. Their stateless interactions need persistent artifacts for continuity. Their pattern recognition capabilities benefit from consistent structures, and their parallel processing potential emerges when tasks are properly decomposed. Understanding these characteristics shapes how we structure code for agent collaboration.

### Document Philosophy

These practices are opinionated and prescriptive. They represent patterns that have proven effective across multiple projects and teams. Not every pattern will apply to every codebase, but understanding the principles will help you make informed decisions about your own AI-assisted development workflow.

Vibe alert: these guidelines have been developed from observed experience, rather than formal evaluations. We have not rigorously tested this techniques nor understand which ones are more effective than others relatively, and to the degree that they actually compound. These are formulated from intuition, first-principles reasoning, and from observed behavior during actual development.

---

## Table of Contents

1. [Coarse-grained Parallel Modules](#coarse-grained-parallel-modules) - Organize code into independent, self-contained modules for efficient context management and safe disposability.

2. [Agent Documentation: The `.agent` Directory](#agent-documentation-the-agent-directory) - Create a token cache of persistent knowledge that agents can reference instead of rediscovering.

3. [External Tool Mental Models](#external-tool-mental-models) - Document how external tools and APIs work to prevent expensive rediscovery and incorrect assumptions.

4. [Planning: Iterative Design Before Implementation](#planning-iterative-design-before-implementation) - Invest in iterative planning with persistent artifacts before implementation to reduce context thrashing and increase the complexity of tasks that can be performed autonomously.

5. [Parallel Development with Worktrees and Workstack](#parallel-development-with-worktrees-and-workstack) - Enable parallel agentic sessions using Git worktrees and plan-based development workflows.

6. [Authoring Guidelines](#authoring-guidelines) - Guidelines for maintaining this document with professional tone and clear structure.

---

## Coarse-grained Parallel Modules

### Core Principle

Organize code into coarse-grained, parallel modules where each module handles a complete feature independently. When agents can see an entire feature in one file, they work faster and make fewer mistakes. When features fail, you can delete them cleanly without unwinding dependencies. This pattern transforms how agents interact with your codebase—from navigating mazes of interconnected files to working with discrete, understandable units.

### Key Pattern: One Feature Per File

**Structure Example:** CLI Commands

```
commands/
├── list.py      # Complete 'list' command - self-contained
├── create.py    # Complete 'create' command - independent
├── delete.py    # Complete 'delete' command - isolated
└── update.py    # Complete 'update' command - standalone
```

### Why This Pattern Works

The immediate benefit is context window efficiency. When each module contains a complete feature, agents can understand everything they need without loading multiple files or maintaining mental maps of cross-file dependencies. This isn't just convenient—it fundamentally changes what agents can accomplish.

For reference, Claude Code operates with a 25,000 token context window, which translates to approximately 6,000-8,000 lines of Python code depending on code density and complexity. Coarse-grained modules allow agents to load complete features within this limit.

Implementation becomes dramatically faster because agents can generate complete, working features in a single response. There's no coordination overhead, no careful sequencing of changes across files. You can even develop multiple features in parallel without conflicts, since each module stands alone.

Perhaps most importantly, failed experiments become cheap. Delete the file and the experiment is gone—no cleanup, no refactoring, no archaeological digs through the codebase to find orphaned code. This disposability encourages experimentation and rapid iteration.

**Note**: This pattern enables safe iteration, not careless coding. Each module should still follow your project's coding standards. Disposability refers to clean architectural boundaries, not to code quality.

### Self-Describing Features for Navigation

Include metadata and comments that make features self-describing and discoverable. This enables quick discovery without reading implementation details, automated documentation generation, and faster agent navigation to relevant code.

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

### Example Applications

This pattern applies broadly to any system with parallel, independent features. CLI commands benefit from one command per file with complete implementation. API endpoints can each live in their own file with all related logic. Event handlers, report generators, data processors, and migration scripts all follow the same principle: features that can be added, modified, or removed independently without affecting sibling features.

The key characteristic is independence. If you can conceptually add or remove a feature without touching other features at the same level, it's a candidate for this pattern.

---

## Agent Documentation: The `.agent` Directory

### Core Principle

The `.agent` directory serves as a **token cache**—a persistent store of understanding that agents have already computed. Instead of repeatedly consuming thousands of tokens to understand the same patterns, conventions, and architectural decisions, agents can load pre-materialized knowledge. When an agent invests significant tokens to achieve deep understanding, persist that understanding for future reuse. This transforms expensive discovery into cheap retrieval.

### The Token Cache Concept

Think of the cache in terms of levels, similar to CPU caching. A CLAUDE.md file might serve as an L0 cache for the most critical, frequently-needed information. A QUICK_REFERENCE.md acts as an L1 cache for common lookups. Detailed guides like EXCEPTION_HANDLING.md form an L2 cache for deeper dives. Like any cache, these documents require invalidation and updates when the underlying reality changes.

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

The `.agent` directory should contain knowledge that agents would otherwise need to derive repeatedly. Architectural decisions belong here—not just what patterns you use, but why you chose them over alternatives. Include pattern libraries showing correct implementations, especially for complex operations that span multiple files or systems.

Mental models earn their place when they help agents reason about non-obvious subsystems. If an agent needs to understand that your event system uses eventual consistency, or that your API versioning follows specific rules, document these models explicitly. Tool-specific guides prove valuable when external tools require particular workflows—how to structure commits for Graphite, or which deployment commands to run in what order.

Keep user-facing documentation in standard locations. The `.agent` directory isn't for getting started guides or API references—it's for the deep operational knowledge that makes agents effective. Marketing content, user tutorials, and general README files belong in their traditional locations, not hidden in an agent-specific directory.

### Key Characteristics

#### Agent-First Writing Style

Documentation optimized for AI consumption differs from human-oriented writing. Structure information for rapid scanning and extraction. Use imperative statements and clear hierarchies rather than conversational prose.

```markdown
## Exception Handling Rules

Never use try/except for control flow.
Check conditions with if statements before operations that might fail.
Catch exceptions only at error boundaries where you can meaningfully handle them.
```

This direct style helps agents quickly extract rules and apply them consistently.

#### Rich Examples Over Prose

Show patterns through contrasting examples rather than lengthy explanations. Agents excel at pattern matching, so give them patterns to match.

````markdown
## Path Operations

Correct approach:

```python
if path.exists():
    resolved = path.resolve()
```
````

Problematic approach:

```python
resolved = path.resolve()  # May fail if path doesn't exist
```

````

The contrast makes the pattern immediately clear without requiring paragraph-long explanations.

#### Rapid Navigation

Include tables and quick references for common decision points:

```markdown
| If you're writing...    | Check this...                          |
|-------------------------|----------------------------------------|
| Exception handling      | → Exception Handling section           |
| Subprocess calls        | → Always use check=True                |
| Path operations         | → Validate existence before resolving  |
````

These navigation aids help agents quickly locate relevant guidance without loading entire documents.

### Integration with Main Codebase Documentation

CLAUDE.md in the root provides quick reference and critical rules, linking to `.agent` for comprehensive details. This two-tier approach gives agents both a fast path for common operations and a deep path for complex scenarios without loading unnecessary context.

For example, CLAUDE.md might contain: "Never use try/except for control flow. Full guide: [.agent/docs/EXCEPTION_HANDLING.md]" while the linked document provides comprehensive examples, edge cases, and rationale.

### Maintenance Guidelines

Update documentation when understanding deepens—when agents discover new patterns worth preserving or when existing patterns prove insufficient. Refactor when the same documentation gets consulted repeatedly, signaling its value. Delete outdated documentation ruthlessly, as stale guidance causes more harm than missing guidance. Keep the root CLAUDE.md synchronized with `.agent` details to maintain consistency.

### Known Risk: Documentation Drift

Documentation drift represents a critical challenge in agentic engineering. The `.agent` documentation can become outdated as the codebase evolves, leading agents to follow obsolete patterns or incorrect assumptions. Stale agent documentation actively harms development by wasting tokens and introducing bugs.

This remains an unsolved problem. We lack robust tooling to detect when `.agent` files diverge from actual code patterns. Current mitigation relies on manual review and agent prompting to verify documentation accuracy. The solution space requires proper tooling—automated drift detection, tests that validate documentation claims against code, and integration into CI/CD pipelines. Until then, treat `.agent` maintenance as a manual, high-priority task.

### The Compound Effect

The `.agent` directory creates compound value over time. Each agent session that would have spent thousands of tokens deriving understanding instead loads it directly. This isn't just faster—it's more consistent and accurate, since all agents reference the same canonical patterns rather than developing their own interpretations. As agents contribute new discoveries back to this shared knowledge base, the entire system becomes more capable.

### Anti-Pattern: Human-Centric Documentation in `.agent`

Avoid placing tutorial-style, beginner-focused content in `.agent`:

```markdown
# Getting Started with Our Codebase

Welcome! We're excited to have you here. Let's walk through how to set up
your development environment step by step...
```

This content belongs in root README.md or docs/CONTRIBUTING.md for humans. The `.agent` directory should contain machine-optimized references. Humans rarely look there, agents don't need tutorials, and mixing audiences dilutes both experiences.

---

# External Tool Mental Models

## Core Principle

Many projects depend on external tools that agents need to understand deeply—specialized build systems, deployment pipelines, API clients, or domain-specific utilities. These tools often emerged after an agent's training cutoff or exist in niche domains where documentation is scattered. Creating comprehensive mental model documents for these tools transforms expensive discovery into efficient loading of pre-computed understanding. These documents are natural candidates for the `.agent` directory, where they serve as reusable knowledge artifacts.

## Why This Matters

When agents encounter unfamiliar tools, they resort to web searches, parsing HTML documentation into usable knowledge. This process repeats for every agent session, creating inefficiency and inconsistency. Worse, agents may make incorrect assumptions based on superficial similarity to other tools they know.

Documenting tool mental models once creates reusable knowledge that every agent can leverage immediately. This investment pays dividends through faster development, fewer errors, and consistent understanding across all agent interactions.

## What to Document

Focus documentation efforts on tools specific to your domain or industry, recently released tools that postdate agent training, complex tools with non-obvious conceptual models, internal or proprietary systems unique to your organization, and tools with poor, scattered, or outdated public documentation.

Skip documentation for standard Unix commands and utilities, well-established programming language features, widely-adopted frameworks like React, Django, or Rails, and common development tools like Git, Docker, or npm. These tools already exist in agent training data with sufficient depth.

## Creating Effective Documentation

The goal isn't to replicate official documentation but to distill it into efficient, agent-optimized knowledge. Transform verbose documentation into concise patterns that agents can quickly load and apply. A well-crafted mental model document might compress thousands of tokens of HTML documentation into hundreds of tokens of essential patterns and concepts. This distillation process—extracting core concepts from sprawling documentation—creates the token cache that makes `.agent` valuable.

## Structure and Content

Effective tool documentation follows a consistent pattern that helps agents quickly understand and apply the tool.

### Conceptual Foundation

Begin with the tool's fundamental mental model. Rather than diving into commands, explain the core concepts that make the tool's behavior predictable. For a branching tool, explain how branches relate. For a build system, describe the dependency graph. For an API, clarify the authentication flow and data models.

### Common Patterns

Document the workflows developers use daily. Show complete examples with context, not just isolated commands. Include the happy path prominently, then cover important variations and edge cases. Real examples with actual file paths and realistic data prove more valuable than abstract descriptions.

### Error Recovery

Catalog common failure modes and their solutions. When tools fail in predictable ways, documented solutions prevent agents from getting stuck. Include specific error messages, their causes, and step-by-step recovery procedures.

### Authoritative Resources

Provide direct links to official documentation, preventing agents from finding outdated or incorrect information through general web searches. Link to specific sections of documentation rather than just homepages.

## Creating Documentation

Documentation can emerge from several sources. For open-source tools, clone the repository and extract documentation directly, transforming verbose HTML documentation into concise markdown focused on practical usage. As your team discovers patterns through usage, capture them immediately—when an agent spends significant time understanding a tool's behavior, that understanding becomes valuable documentation for future sessions. When agents search tool documentation online, save useful findings and transform search results into structured documents, removing redundancy and organizing for quick reference.

## Integration Strategies

Make tool documentation discoverable and loadable when needed. Structure documents to support incremental loading—a quick reference for common operations, detailed patterns for complex workflows, and troubleshooting guides for error handling. In your main agent documentation, reference tool documents clearly so agents know when to load additional context.

## Practical Example

Consider documenting Graphite, a specialized stacking tool for Git. Rather than assuming agents understand its unique approach to branch management, create a distilled mental model document:

```markdown
# Graphite Mental Model

## Core Concept

Graphite manages "stacks"—linear chains of dependent branches...

# ... conceptual overview continues ...

## Common Operations

Creating a stack:

- `gt create feature-1` creates first branch in stack
- `gt create feature-2` stacks on top of feature-1

# ... additional operations ...

## Error Recovery

When "parent branch not found" appears, run `gt sync`...

# ... more error scenarios and solutions ...
```

This document provides enough context for agents to work effectively without searching for documentation or making incorrect assumptions based on Git's branching model. The focus remains on evergreen concepts unlikely to change between minor versions, ensuring documentation longevity.

## Maintenance Considerations

Tool documentation requires ongoing attention. Focus on documenting stable, conceptual foundations rather than version-specific details. Update when tools introduce major conceptual changes, not minor feature additions. Refine based on patterns that prove useful in practice. Verify that external documentation links remain valid.

The goal isn't comprehensive coverage but practical sufficiency. Document the core knowledge that enables productive work, leaving detailed reference material to official documentation.

## Planning: Iterative Design Before Implementation

### Core Principle

Invest in planning before implementation for non-trivial or complex tasks. Well-crafted plans save time and reduce context thrashing during execution. Think of plans as execution blueprints—detailed specifications that enable efficient, autonomous agent work.

### Key Pattern: Plans as Persistent Artifacts

For tasks requiring substantial implementation time, persist plans as `.md` files. This approach preserves context across multiple agent sessions, enables switching between planning models and execution models, tracks progress through complex multi-step implementations, and creates clear boundaries between design thinking and implementation.

### Planning Best Practices

#### Iterate on the Plan

Plans often require refinement. Investing in precise planning saves significant implementation time. Fixing errors in plans costs far less than fixing errors in implementations. Treat the planning phase as an opportunity to explore edge cases, identify dependencies, and clarify ambiguities before committing to code.

#### Persist Non-Trivial Plans

Create persistent plans for substantial tasks. Persistent plans preserve context without requiring re-explanation to agents. They provide session flexibility, allowing you to switch between agents or models mid-task. Progress becomes visible through clear checklists of completed work. The original intent remains accessible for debugging when implementation diverges from design.

#### Keep Plans Out of Version Control

In our experience, plans should remain outside repositories. They confuse human reviewers who encounter implementation details in pull requests. Plans also become outdated quickly, creating maintenance burden without corresponding value.

#### Two-Phase Planning for Complex Features

Features touching multiple components or requiring architectural decisions benefit from a two-phase approach.

**Phase 1: Specification Document** focuses on what and why. Create an overview without implementation details. Define functional requirements, constraints, and security considerations. Design APIs with clear interfaces and data flows. Document architecture decisions with rationale, alternatives considered, and accepted tradeoffs.

**Phase 2: Implementation Plan** focuses on how. Create a pre-implementation checklist covering dependencies, environment setup, and documentation review. Develop step-by-step implementation sequences with specific files and patterns. Identify context requirements including files to load, patterns to follow, and external documentation. Define testing strategy spanning unit, integration, and performance benchmarks.

This separation enables using different tools optimized for each phase, reduces cognitive load during implementation, and creates clear decision documentation before coding begins.

---

## Parallel Development with Worktrees and Workstack

### Core Principle

Git worktrees enable truly parallel agentic development by creating independent working directories from a single repository. When combined with comprehensive planning and proper orchestration tools, agents can work autonomously on separate features without coordination overhead. This pattern transforms sequential development into parallel execution.

### Understanding Git Worktrees

Git worktrees solve a fundamental problem in parallel development: the need for multiple working copies without repository duplication. A worktree is a linked working directory that shares the same Git repository but maintains its own working files, index, and HEAD. This means you can have multiple branches checked out simultaneously in different directories, all connected to the same `.git` repository.

Each worktree provides a complete, independent working directory. Agents operating in different worktrees can work simultaneously without conflicts, check out different branches independently, and maintain separate build states and dependencies. Since agents are stateless between sessions, each worktree becomes a persistent workspace for a specific task. An agent can return to its worktree and resume work without needing to understand the state of other parallel efforts.

### Workstack: Orchestrating Parallel Development

While Git provides worktree functionality natively through commands like `git worktree add`, managing multiple worktrees for parallel development introduces complexity. Workstack provides an orchestration layer that simplifies worktree lifecycle management, standardizes naming and organization conventions, and integrates planning documents with worktrees automatically.

The tool addresses specific pain points in parallel development: tracking which worktree corresponds to which feature, maintaining consistent branch naming across worktrees, and ensuring plan documents are available in the working directory. By providing consistent commands and conventions, Workstack ensures that agents can reliably create, navigate, and manage parallel development environments.

### Key Pattern: Plan-Based Development

Parallel agent work requires comprehensive planning. Without detailed plans, agents cannot operate autonomously for extended periods. Plan-based development creates a contract between the human architect and the executing agents. When you use `workstack create --plan`, the tool automatically copies your plan document into the worktree as `.PLAN.md`. This file is gitignored but remains accessible to agents and tools, providing immediate context for the task at hand.

### Workstack Best Practices

#### Keep the Root Repository Clean

The root repository should never have direct commits. It serves as the coordination point and planning center. This approach prevents conflicts between planning and execution, maintains a clean workspace for creating new plans, and ensures the root always reflects the main branch state.

```bash
# Create plans in root, execute in worktrees
cd ~/repository/main
echo "Implementation plan..." > plans/new-feature.md
workstack create --plan plans/new-feature.md new-feature

# Avoid making changes directly in root
# Don't checkout branches or edit files in the root directory
```

#### Use Plan Files as Task Manifests

Plan files serve as executable specifications for agents containing clear success criteria, specific implementation steps, required context and dependencies, and testing requirements. Think of them as detailed instructions that an agent can follow autonomously. The more comprehensive the plan, the longer an agent can work without human intervention.

#### Leverage Plan-Based Worktree Creation

Workstack's `--plan` flag automates the workflow of creating a worktree with embedded context:

```bash
workstack create --plan plans/auth-feature.md auth-feature
```

This command creates a new worktree for the feature, copies the plan to `.PLAN.md` in the worktree, checks out a new branch, and provides agents with immediate context. The `.PLAN.md` file is gitignored but accessible to tools, allowing agents to understand their mission without additional context.

### Enabling Autonomous Agent Operation

For parallel development to work effectively, agents must operate autonomously for extended periods. This requires comprehensive planning before execution, clear boundaries between features, and well-defined success criteria. The time invested in creating detailed plans reduces coordination overhead and increases development velocity.

### Practical Example: Parallel Feature Development

Consider developing three independent features simultaneously:

```bash
# In the root repository, create three plans
echo "User authentication implementation plan..." > plans/user-auth.md
echo "API v2 migration plan..." > plans/api-v2.md
echo "Performance optimization plan..." > plans/perf-opt.md

# Create worktrees with embedded plans
workstack create --plan plans/user-auth.md user-auth
workstack create --plan plans/api-v2.md api-v2
workstack create --plan plans/perf-opt.md perf-opt

# Three agents can now work in parallel
# Agent 1: cd user-auth && implement based on .PLAN.md
# Agent 2: cd api-v2 && implement based on .PLAN.md
# Agent 3: cd perf-opt && implement based on .PLAN.md
```

Each agent operates independently, following its plan without needing to coordinate with others. When features are complete, they can be reviewed and merged independently.

### Managing Worktree Lifecycle

Worktrees should be treated as temporary workspaces. Once a feature is merged, remove its worktree to keep the development environment clean:

```bash
# After merging the authentication feature
workstack remove user-auth

# List active worktrees to review parallel work
workstack list
```

This lifecycle management prevents accumulation of stale worktrees and maintains clarity about active development efforts.

### Anti-Pattern: Underspecified Parallel Work

Attempting parallel development without comprehensive planning leads to confusion, conflicts, and wasted effort. Without detailed plans, agents cannot work autonomously. They require constant clarification, defeating the purpose of parallel development. Worse, they might make conflicting assumptions, creating integration challenges later.

### Integration with Planning Workflow

The worktree pattern integrates seamlessly with the planning practices described earlier. Plans created during the design phase become the execution blueprints for worktrees. This creates a natural flow from conception to completion: planning phase to create detailed plans in the root repository, worktree creation using plan documents to initialize workspaces, parallel execution with multiple agents working autonomously, integration of completed features independently, and cleanup by removing worktrees after successful integration.

This workflow scales to support as many parallel efforts as you have agents available, limited only by the quality of your planning and the independence of your features.

## Authoring Guidelines

This section provides guidance for maintaining and extending this document. Following these guidelines ensures consistency and readability.

### Tone and Voice

#### Professional and Informative

Write clearly and directly without unnecessary dramatization. Trust that clear, straightforward language conveys importance better than emphatic words. Present information objectively and assume technical competence—intelligent readers don't need ideas shouted at them.

Show patterns through examples rather than prescriptive commands. Instead of declaring what readers must never do, demonstrate better alternatives and explain their benefits. Let the quality of the solution speak for itself.

### Structure and Format

#### Section Organization

Each major section should follow a consistent pattern. Begin with a core principle that summarizes the main idea in one paragraph. Present the key pattern or primary implementation approach. Provide detailed explanation of how and why it works. Include concrete examples that demonstrate the pattern in practice. Address anti-patterns by showing what to avoid and explaining why.

#### Heading Hierarchy

Reserve `#` for the document title only. Use `##` for major sections that appear in the table of contents. Apply `###` for subsections within major sections. Deploy `####` for specific topics within subsections when needed.

#### Code Examples

Provide practical, contextualized examples that readers can understand and adapt:

```python
# Complete example with context
def search_content(query: str, filters: dict) -> list:
    """Search content with optional filters."""
    results = index.search(query)
    if filters:
        results = apply_filters(results, filters)
    return results
```

Avoid fragments that lack context or require additional explanation to understand their purpose and integration points.

#### Language-Agnostic When Possible

Use generic examples that apply across languages when illustrating structural patterns. When language-specific examples become necessary, clearly indicate the language and explain any language-specific considerations.

#### Balance Between Abstract and Concrete

Start with the concept to establish understanding. Provide concrete examples that demonstrate real implementations. Return to abstraction to summarize how readers can apply the pattern broadly. This progression from concept to example to principle helps readers both understand and generalize the pattern.
