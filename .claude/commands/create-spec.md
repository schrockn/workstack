---
description: Create a conceptual specification using the spec-creator agent (Opus)
---

## ⚠️ CONCEPTUAL PLANNING MODE ACTIVE

I'll help you create a conceptual specification for your idea. This workflow focuses on:

- **Problem definition** and requirements gathering
- **High-level architecture** and design decisions
- **User experience** and success criteria
- **NO implementation details** (file paths, class names, code structure)

### How This Works

**Phase 1: Conceptual Design (Iterative)**

1. **You describe your idea** - What you want to build and why
2. **I create a conceptual spec** (displayed in terminal for review)
3. **We iterate together** until the spec captures your vision
4. **Spec is saved to disk** as a `-spec.md` file after your approval

**Phase 2: Next Steps**

- After saving the spec, you can run `/create-implementation-plan <spec-file>` to create a detailed technical plan
- Or continue to refine the spec based on feedback

### What to Provide

Describe your idea, feature, or problem you want to solve. Include:

- What problem you're trying to solve
- Why this matters
- Any requirements or constraints you have in mind
- Who will use this and how

The more context you provide, the better the initial spec will be.

---

**AGENT INSTRUCTIONS:**

You are now invoking the `spec-creator` agent to help the user create a conceptual specification.

**Your task:**

1. Use the Task tool to invoke the `spec-creator` agent (subagent_type="spec-creator")
2. Pass the user's idea/description as the prompt
3. The agent will guide the user through iterative spec creation
4. The agent will handle:
   - Creating the initial spec (terminal output only)
   - Iterating based on user feedback
   - Suggesting a filename and asking for approval
   - Writing the `-spec.md` file to the project root after approval

**Example invocation:**

```
Task tool with:
- subagent_type: "spec-creator"
- description: "Create conceptual spec"
- prompt: "[User's idea/description from the conversation]"
```

**Important reminders for the spec-creator agent:**

- Focus on WHAT and WHY, not HOW
- No file paths, class names, or implementation details
- Keep it conceptual and high-level
- Output to terminal first, iterate, then write file only after approval
- Always suggest running `/create-implementation-plan <spec-file>` as next step
