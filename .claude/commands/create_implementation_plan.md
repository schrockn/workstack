---
description: Create an implementation plan using the implementation-planner agent
---

## ⚠️ PLANNING-ONLY MODE ACTIVE

I'll help you create an implementation plan using the specialized planning agent. This workflow is designed for **planning only** - no code will be written until the plan is finalized and saved to disk.

### How This Works

1. **You provide context** about what needs to be built
2. **The agent creates a plan** (displayed in terminal for review)
3. **We iterate together** until the plan is perfect
4. **Plan is saved to disk** as a markdown file
5. **Then (and only then)** implementation can begin

### Provide Your Planning Context

You can share:

- A feature you want to implement
- An error message or bug to fix
- Performance issues to optimize
- A refactoring goal
- Any relevant context or requirements

**What would you like to plan?**

---

**IMPORTANT AGENT INSTRUCTIONS:**

When invoking the implementation-planner agent:

1. **DO NOT write any code during planning phase**
2. **DO NOT use Edit, Write, or any modification tools**
3. **ONLY output the plan to terminal for iterative review**
4. **ONLY persist to disk after explicit user approval**
5. The agent should remain in "Phase 1: Human-Readable Planning" mode until the user explicitly approves with signals like "looks good", "approved", or "ready to implement"

The goal is to create a comprehensive implementation plan that will be saved as a `.md` file at the repository root, which can then guide future implementation work.
