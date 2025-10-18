---
name: command-creator
description: This skill should be used when creating a Claude Code slash command. Use when users ask to "create a command", "make a slash command", "add a command", or want to document a workflow as a reusable command. Essential for creating optimized, agent-executable slash commands with proper structure and best practices.
---

# Command Creator

This skill guides the creation of Claude Code slash commands - reusable workflows that can be invoked with `/command-name` in Claude Code conversations.

## About Slash Commands

Slash commands are markdown files stored in `.claude/commands/` (project-level) or `~/.claude/commands/` (global/user-level) that get expanded into prompts when invoked. They're ideal for:

- Repetitive workflows (code review, PR submission, CI fixing)
- Multi-step processes that need consistency
- Agent delegation patterns
- Project-specific automation

## When to Use This Skill

Invoke this skill when users:

- Ask to "create a command" or "make a slash command"
- Want to automate a repetitive workflow
- Need to document a consistent process for reuse
- Say "I keep doing X, can we make a command for it?"
- Want to create project-specific or global commands

## Command Structure

Every slash command is a markdown file with:

```markdown
---
description: Brief description shown in /help (required)
argument-hint: <placeholder> (optional, if command takes arguments)
---

# Command Title

[Detailed instructions for the agent to execute autonomously]
```

## Command Creation Workflow

### Step 1: Determine Location

**Auto-detect the appropriate location:**

1. **Check git repository status:**

   ```bash
   git rev-parse --is-inside-work-tree 2>/dev/null
   ```

2. **Default location:**
   - If in git repo → Project-level: `.claude/commands/`
   - If not in git repo → Global: `~/.claude/commands/`

3. **Allow user override:**
   - If user explicitly mentions "global" or "user-level" → Use `~/.claude/commands/`
   - If user explicitly mentions "project" or "project-level" → Use `.claude/commands/`

**Report the chosen location to the user before proceeding.**

### Step 2: Show Command Patterns

Help the user understand different command types by showing brief examples from existing commands:

**Workflow Automation Pattern** (example: submit-stack):

- Analyzes changes
- Creates git commit
- Submits PRs with Graphite
- Reports results

**Iterative Fixing Pattern** (example: ensure_ci):

- Runs check (like `make all-ci`)
- Identifies failures
- Applies fixes iteratively
- Continues until success or stuck

**Agent Delegation Pattern** (example: create_implementation_plan):

- Invokes specialized agent (Task tool)
- Passes context to agent
- Agent works autonomously
- Returns results to user

**Simple Execution Pattern** (example: codex-review):

- Runs specific command or script
- Handles arguments
- Returns output

Ask the user: "Which pattern is closest to what you want to create?" This helps frame the conversation.

### Step 3: Gather Command Information

Ask the user for key information needed to create an effective command:

#### A. Command Name and Purpose

**Ask:**

- "What should the command be called?" (for filename)
- "What does this command do?" (for description field)

**Guidelines:**

- Command names should be kebab-case (e.g., `submit-stack`, `ensure-ci`)
- Description should be concise, action-oriented (appears in `/help` output)
- Good: "Run make all-ci and iteratively fix issues until all checks pass"
- Avoid: "A command that helps with CI stuff"

#### B. Arguments

**Ask:**

- "Does this command take any arguments?"
- "Are arguments required or optional?"
- "What should arguments represent?" (e.g., branch name, file path, description)

**If command takes arguments:**

- Add `argument-hint: <placeholder>` to frontmatter
- Use descriptive placeholder (e.g., `<description>`, `[base-branch]`)
- Use `<angle-brackets>` for required arguments
- Use `[square-brackets]` for optional arguments

#### C. Workflow Steps

**Ask:**

- "What are the specific steps this command should follow?"
- "What order should they happen in?"
- "What tools or commands should be used?"

**Gather details about:**

- Initial analysis or checks to perform
- Main actions to take
- How to handle results
- Success criteria
- Error handling approach

#### D. Tool Restrictions and Guidance

**Ask:**

- "Should this command use any specific agents or tools?"
- "Are there any tools or operations it should avoid?"
- "Should it read any specific files for context?"

**Common patterns:**

- Use makefile-runner agent for `make` commands
- Use Task tool for specialized agents (implementation-planner, plan-executors)
- Avoid unnecessary exploration (explicitly state what NOT to do)
- Check for specific files first (e.g., `.PLAN.md`)

### Step 4: Generate Optimized Command

Create the command file with agent-optimized instructions:

#### Frontmatter Structure

```yaml
---
description: [One-line description of what the command does]
argument-hint: [<required-arg>] or [[optional-arg]] (omit if no arguments)
---
```

#### Content Structure

Follow this template structure:

````markdown
# [Command Title]

[1-2 sentence overview of what this command does]

## What This Command Does

[Bulleted list of main steps, user-facing description]

## Usage

```bash
# [Example with arguments]
/command-name "argument example"

# [Example without arguments if optional]
/command-name
```
````

## Implementation Steps

[Detailed, numbered steps for the agent to execute autonomously]

### 1. [First Major Step]

[Clear instructions with specifics]

```bash
# Example commands if applicable
command --flag value
```

[Explain what to do with results]

### 2. [Second Major Step]

[Continue with clear, actionable instructions]

## Important Notes

- **[Key constraint or requirement]**
- **[What to check first]**
- **[What NOT to do]**
- **[Error handling approach]**

## Error Handling

[Specify how to handle failures]

## Example Output

```
[Show expected terminal output]
```

````

#### Best Practices for Agent Execution

Include these elements for precise agent execution:

1. **Explicit file checks:**
   ```markdown
   **FIRST**: Check if `.PLAN.md` exists in the repository root
````

2. **Tool usage guidance:**

   ```markdown
   Use the makefile-runner agent (Task tool) instead of Bash for make commands
   ```

3. **Anti-patterns:**

   ```markdown
   - **NEVER run additional exploration commands** beyond what's specified
   - **DO NOT batch completions** - mark todos complete immediately
   ```

4. **Conditional logic:**

   ```markdown
   If condition A:

   - Do X
     Otherwise:
   - Do Y
   ```

5. **Success criteria:**

   ```markdown
   Stop when:

   - All checks pass (exit code 0)
   - User approves the result
   ```

6. **Error handling:**

   ```markdown
   If any step fails:

   - Report the specific command that failed
   - Show the error message
   - Ask user how to proceed
   ```

### Step 5: Create the Command File

1. **Determine full file path:**
   - Project: `.claude/commands/[command-name].md`
   - Global: `~/.claude/commands/[command-name].md`

2. **Ensure directory exists:**

   ```bash
   mkdir -p [directory-path]
   ```

3. **Write the command file:**
   - Use Write tool to create the file
   - Use the generated content from Step 4

4. **Confirm with user:**
   - Report the file location
   - Summarize what the command does
   - Explain how to use it: `/command-name [arguments]`

### Step 6: Test and Iterate (Optional)

If the user wants to test:

1. **Suggest testing the command:**

   ```
   You can test this command by running:
   /command-name [arguments]
   ```

2. **Be ready to iterate:**
   - If command doesn't work as expected, ask what needs adjustment
   - Refine the instructions based on feedback
   - Update the file with improvements

## Command Writing Guidelines

### Writing Style

- Use **imperative/infinitive form** (verb-first instructions)
- Be explicit and specific (not "check for errors" but "run make lint to check for errors")
- Include expected outcomes ("This should output...")
- Provide examples with realistic values (not foo/bar)

### Agent Optimization

Commands are executed by AI agents, so optimize for:

1. **Clarity:** No ambiguous instructions
2. **Completeness:** Include all necessary context
3. **Autonomy:** Agent should execute without asking questions
4. **Determinism:** Same input should produce consistent results
5. **Error handling:** Explicit guidance for failure cases

### Common Patterns to Include

**Progress tracking:**

```markdown
Use TodoWrite to track progress:

- Task 1: Description
- Task 2: Description
```

**File operations:**

````markdown
Read the file first to understand current state:

```bash
cat path/to/file
```
````

````

**Git operations:**
```markdown
Check current git status:
```bash
git status
git diff HEAD
````

````

**Conditional execution:**
```markdown
FIRST check if X exists:
- If yes: do A
- If no: do B
````

**Tool delegation:**

```markdown
Use the Task tool with subagent_type="agent-name" for this step
```

## Examples from Existing Commands

### Simple Workflow Command (submit-stack)

**Pattern:** Analyze → Act → Report

```markdown
1. Check for .PLAN.md first
2. If exists: use plan context
3. Otherwise: analyze git changes
4. Create commit with summary
5. Submit PRs with Graphite
6. Report results
```

**Key features:**

- Explicit file check order
- Conditional logic based on file existence
- Clear success output format

### Iterative Fixing Command (ensure_ci)

**Pattern:** Run → Parse → Fix → Repeat

```markdown
1. Run make all-ci
2. Parse failures by type
3. Apply targeted fixes
4. Run again to verify
5. Repeat until success (max 10 iterations)
```

**Key features:**

- Iteration control (max attempts, stuck detection)
- Progress tracking with TodoWrite
- Clear stopping conditions

### Agent Delegation Command (create_implementation_plan)

**Pattern:** Context → Delegate → Iterate

```markdown
1. Present planning context to user
2. Invoke implementation-planner agent
3. Agent creates plan iteratively
4. Plan is reviewed and refined
5. Save to disk after approval
```

**Key features:**

- Clear agent invocation instructions
- Phase-based workflow
- Explicit save-to-disk trigger

## Quality Checklist

Before finalizing a command:

- [ ] Command name is descriptive and kebab-case
- [ ] Description is concise and action-oriented
- [ ] Arguments are documented if applicable
- [ ] Steps are numbered and clearly ordered
- [ ] Tool usage is explicitly specified
- [ ] Anti-patterns are called out
- [ ] Error handling is defined
- [ ] Success criteria are clear
- [ ] Examples show realistic usage
- [ ] Instructions are agent-optimized (imperative, specific)
- [ ] Location (project vs global) is appropriate
- [ ] File has been created at correct location
- [ ] User knows how to invoke the command

## Common Pitfalls

**Avoid:**

1. **Vague instructions** - "Fix any errors" vs "Run make fix to auto-fix lint errors"
2. **Missing error handling** - Always specify what to do on failure
3. **Ambiguous conditionals** - Be explicit about if/else branches
4. **Batch operations** - Specify when to mark todos complete immediately
5. **Tool confusion** - Be explicit: "Use Task tool" not "use an agent"
6. **Missing context** - Include necessary file checks and initial analysis
7. **Poor descriptions** - Frontmatter description is what users see in /help

## Advanced Patterns

### Multi-Agent Orchestration

```markdown
1. Use Task tool with subagent_type="explore" to find files
2. Use Task tool with subagent_type="implementation-planner" to create plan
3. Use Task tool with subagent_type="haiku-plan-executor" to execute
```

### Context File Checks

```markdown
Check these files in order for context:

1. .PLAN.md - implementation plan
2. .github/CONTRIBUTING.md - contribution guidelines
3. CLAUDE.md - coding standards

Use the first file found to inform the workflow.
```

### Conditional Tool Selection

```markdown
If changes span 3+ files:

- Use implementation-planner agent
  Otherwise:
- Execute changes directly
```

## Summary

When creating a command:

1. **Detect location** (project vs global)
2. **Show patterns** to frame the conversation
3. **Gather information** (name, purpose, arguments, steps, tool guidance)
4. **Generate optimized command** with agent-executable instructions
5. **Create file** at appropriate location
6. **Confirm and iterate** as needed

Focus on creating commands that agents can execute autonomously, with clear steps, explicit tool usage, and proper error handling.
