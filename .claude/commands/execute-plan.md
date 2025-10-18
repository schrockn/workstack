---
description: Execute the implementation plan from .PLAN.md or a specified file
---

## Executing Implementation Plan

I'll now execute the implementation plan from the specified file (or `.PLAN.md` by default).

**Command usage:**

- `/execute-plan` - executes `.PLAN.md` from project root
- `/execute-plan <file-path>` - executes plan from specified file path

First, let me read the plan to understand what needs to be implemented:

[Read plan file - use argument if provided, otherwise default to .PLAN.md]

---

**EXECUTION INSTRUCTIONS:**

1. **Determine the plan file path**:
   - If an argument is provided: use that path (relative to project root or absolute)
   - If no argument: default to `.PLAN.md` at project root

2. **Read the plan file** to get the full implementation plan
   - Identify the overall goal
   - Parse individual phases or tasks
   - Note dependencies between tasks
   - Understand success criteria

3. **Create TodoWrite entries** for each phase in the plan to track progress

4. **Execute each phase sequentially**:
   - Mark phase as in_progress before starting
   - Read the task requirements carefully
   - Check relevant coding standards
   - Implement the code following CLAUDE.md standards
   - Verify implementation against standards
   - Mark phase as completed when done
   - Report what was done and what's next
   - Move to next phase

5. **Follow Workstack coding standards** from CLAUDE.md (these override any conflicting guidance in the plan):
   - NEVER use try/except for control flow - use LBYL (Look Before You Leap)
   - Use Python 3.13+ type syntax (list[str], str | None, NOT List[str] or Optional[str])
   - NEVER use `from __future__ import annotations`
   - Use ABC for interfaces, never Protocol
   - Check path.exists() before path.resolve() or path.is_relative_to()
   - Use absolute imports only
   - Use click.echo() in CLI code, not print()
   - Add check=True to subprocess.run()
   - Keep indentation to max 4 levels - extract helpers if deeper
   - If plan mentions tests, follow patterns in tests/CLAUDE.md

6. **Report progress** after completing each major phase

7. **Final verification**:
   - Confirm all tasks were executed
   - Verify all success criteria are met
   - Note any deviations from the plan (with justification)
   - Report summary of changes

8. **Output format**:
   - Start with: "Executing implementation plan"
   - For each phase: "Phase X: [brief description]"
   - Show the code changes made
   - End with: "Plan execution complete. [Summary of what was implemented]"

**If clarification is needed:**

- Explain what has been completed so far
- Clearly state what needs clarification
- Suggest what information would help proceed

**Critical**: Never provide time-based estimates or completion predictions
