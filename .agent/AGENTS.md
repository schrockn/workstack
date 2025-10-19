# Agents

This project uses specialized agents for cost optimization and specific workflows.

## Available Agents

### graphite-haiku

**Purpose**: Execute Graphite (gt) commands using the Haiku model for cost optimization instead of the main Sonnet agent.

**Location**: `.claude/agents/graphite-haiku.md`

**When to use**:

- Executing any gt command that needs output parsing
- Extracting structured data from gt results (PR URLs, branch names, commit info)
- Cost-sensitive operations where Haiku's capabilities are sufficient

**Usage**:

```python
Task(
    subagent_type="graphite-haiku",
    description="Get stack log",
    prompt="Execute the command: gt log short"
)
```

**What it does**:

1. Executes the provided gt command
2. Parses output to extract structured data:
   - PR URLs from `gt submit`
   - Branch names from `gt log`, `gt ls`
   - Commit info from `gt log`
   - File lists from `gt status`
3. Returns markdown-formatted results with both parsed and raw output

**What it doesn't do**:

- Command validation (main agent decides what to run)
- Error interpretation (returns errors, main agent handles them)
- Decision making about next steps

**Model**: Haiku (claude-3-5-haiku-latest)

---

### git-diff-summarizer

**Purpose**: Analyze git diffs and provide structured summaries.

**Location**: `.claude/agents/git-diff-summarizer.md`

**When to use**:

- Understanding changes between commits or branches
- Summarizing work before creating commits or PRs
- Analyzing Graphite stack changes

**Model**: Haiku

---

### makefile-runner

**Purpose**: Execute make targets and report results.

**Location**: `.claude/agents/makefile-runner.md`

**When to use**:

- Running `make` commands (use this instead of Bash for make)
- Building, testing, or linting via Makefile

**Model**: Haiku

---

### implementation-planner

**Purpose**: Create iterative, reviewable implementation plans.

**Location**: `.claude/agents/implementation-planner.md`

**When to use**:

- Planning features spanning 3+ files
- Evaluating multiple implementation approaches
- Surfacing architectural decisions

**Model**: Opus (for complex planning)

## Agent Development

### Creating a New Agent

1. Create a markdown file in `.claude/agents/`:

   ```
   .claude/agents/my-agent.md
   ```

2. Add YAML frontmatter:

   ```yaml
   ---
   name: my-agent
   description: |
     When to use this agent...

     <example>
     Context: [scenario]
     user: "user request"
     assistant: "I'll use the my-agent to..."
     </example>

   model: haiku # or opus
   color: cyan # optional
   ---
   ```

3. Write the agent's system prompt with:
   - Core responsibilities
   - Execution framework
   - Quality standards
   - Example interactions

4. Restart Claude Code to load the new agent

### Agent Design Principles

**Do**:

- Focus on a specific, well-defined task
- Use Haiku for simple execution/parsing tasks
- Use Opus for complex planning/decision-making
- Provide clear examples in the description
- Return structured, parseable output

**Don't**:

- Add validation logic (main agent decides)
- Make decisions about what to do next
- Duplicate work the main agent should do
- Create agents for trivial tasks

### Cost Optimization

The primary value of Haiku agents is **cost reduction**:

- Haiku is ~10-20x cheaper than Sonnet
- Use Haiku for: command execution, output parsing, simple analysis
- Use Opus for: complex planning, architectural decisions
- Use Sonnet for: main interaction, decision-making, error recovery

## Registration

Agents are automatically discovered from `.claude/agents/` directory. No configuration or build step required - just restart Claude Code after creating or modifying an agent file.
