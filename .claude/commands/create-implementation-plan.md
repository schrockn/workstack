---
description: Create an implementation plan using the implementation-planner agent
---

## ⚠️ TECHNICAL PLANNING MODE ACTIVE

I'll help you create a detailed technical implementation plan. This workflow focuses on:

- **Specific file paths** and directory structure
- **Class/function names** and module organization
- **Design patterns** and technical approaches
- **Concrete implementation details**

### Command Usage

**Option 1: Plan from specification file**

```
/create-implementation-plan <spec-file>
```

Creates a technical plan based on an existing `-spec.md` file.

**Option 2: Plan from conversational description**

```
/create-implementation-plan
```

Creates a technical plan directly from your description.

### How This Works

**Phase 1: Technical Planning (Iterative)**

1. **You provide context** (spec file or description)
2. **Agent creates technical plan** (displayed in terminal)
3. **We iterate together** until the plan is complete
4. **Plan is saved to disk** as a `-plan.md` file

**Phase 2: Implementation**

- After saving, create a worktree with: `workstack create --plan <plan-file>`
- Switch to the new worktree to begin implementation

### What to Provide

**If you have a spec file:**

- Provide the path to your `-spec.md` file
- Agent will read it and create a technical plan based on the conceptual design

**If working from scratch:**

- A feature you want to implement
- Technical requirements or constraints
- Performance goals or optimization targets
- Refactoring objectives
- Any relevant context

**What would you like to plan?**

---

**AGENT INSTRUCTIONS:**

When invoking the implementation-planner agent:

**Step 1: Detect Mode**

- Check if user provided a spec file argument (ends with `-spec.md`)
- If spec file provided: Read it first, extract key information, create plan based on spec
- If no spec file: Create plan from conversational description

**Step 2: Planning Phase**

1. **DO NOT write any code during planning phase**
2. **DO NOT use Edit, Write, or any modification tools**
3. **ONLY output the plan to terminal for iterative review**
4. **ONLY persist to disk after explicit user approval**
5. Remain in "Phase 1: Human-Readable Planning" mode until explicit approval

**Step 3: File Creation (After Approval)**

- Suggest filename with `-plan.md` suffix
- Ask for confirmation before writing
- Save to repository root
- Suggest creating a worktree with: `workstack create --plan <filename>`

**Example invocation:**

```
Task tool with:
- subagent_type: "implementation-planner"
- description: "Create technical implementation plan"
- prompt: "[If spec file: 'Read and create plan from <spec-file>'] [If conversational: '<user description>']"
```

The goal is to create a detailed technical implementation plan saved as a `-plan.md` file at the repository root.
