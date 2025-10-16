---
description: Execute the implementation plan from .PLAN.md using the sonnet-plan-executor agent for complex plans
---

## Executing Complex Implementation Plan

I'll now execute the implementation plan from `.PLAN.md` at the project root using the sonnet-plan-executor agent. This agent is optimized for complex plans that may require interpretation, problem-solving, or handling of edge cases.

First, let me read the plan to understand its complexity and requirements:

```bash
cat .PLAN.md
```

Once I've reviewed the plan, I'll use the sonnet-plan-executor agent to execute it with intelligent adaptation where needed.

---

**AGENT INVOCATION INSTRUCTIONS:**

1. **Read `.PLAN.md` from the project root** to get the full implementation plan
2. **Assess plan complexity** to confirm sonnet-plan-executor is appropriate
3. **Invoke the sonnet-plan-executor agent** with the plan contents as context
4. **Provide the agent with**:
   - The full contents of `.PLAN.md`
   - Clear instruction to execute the plan with intelligent adaptation
   - Reminder to follow Workstack coding standards from CLAUDE.md
   - Permission to make reasonable interpretations where needed

The agent prompt should be:

"Execute the implementation plan from .PLAN.md with intelligent adaptation where needed. Here is the plan content:

[Include the full content of .PLAN.md here]

Follow this plan step-by-step, implementing each phase in order while:

- Making reasonable interpretations for any implicit requirements
- Handling edge cases not explicitly covered in the plan
- Optimizing implementation details while preserving the plan's intent
- Proactively identifying and resolving potential issues

Ensure all code follows the Workstack coding standards defined in CLAUDE.md, particularly:

- NEVER use try/except for control flow
- Use Python 3.13+ type syntax
- Check path.exists() before resolve operations
- Use absolute imports only

Report progress as you complete each phase, noting any significant adaptations or optimizations made."
