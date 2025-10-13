# Sandbox Rebases: Safe, Predictable Rebasing for Stacked Development

## Executive Summary

Sandbox Rebases transform git rebasing from a high-stakes operation into a safe, predictable workflow by performing all rebase operations in isolated temporary worktrees before touching your actual branches. This gives you complete visibility into what will happen, the ability to experiment with conflict resolution, and a guaranteed escape hatch if things go wrong.

**Core Value**: Try before you apply. See conflicts before you commit. Never lose work.

---

## The Problem

Traditional git rebasing is scary because:

1. **It's destructive** - Once you start a rebase, your branch is in flux
2. **Conflicts are surprising** - You don't know what conflicts exist until you're in the middle of them
3. **Recovery is complex** - Aborting leaves you anxious about whether you're truly back to safety
4. **No preview** - You can't see the end result before committing to the operation
5. **Testing is risky** - You can't run tests on the rebased code without completing the rebase

## The Solution: Sandbox Rebases

Sandbox rebases perform all operations in a completely isolated temporary worktree, allowing you to:

- **Preview** exactly what will happen before affecting your real branch
- **Experiment** with different conflict resolution strategies
- **Test** the rebased code before applying it
- **Abort** cleanly with zero risk to your working branch
- **Apply** the successful rebase only when you're 100% confident

---

## User Workflow

### 1. Check If Rebase Is Needed

```bash
$ workstack status feature-frontend
Branch: feature-frontend
Parent: feature-backend (5 commits ahead, 3 commits behind)
Status: Needs rebase
Potential conflicts: Unknown (run 'workstack rebase --preview' to check)
```

### 2. Preview the Rebase (Dry Run)

```bash
$ workstack rebase --preview feature-frontend
Creating sandbox at ~/worktrees/.sandbox-feature-frontend...
Attempting rebase onto feature-backend...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REBASE PREVIEW RESULTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Successfully applied: 4 of 5 commits
⚠ Conflicts detected:   1 file

Detailed Results:
  ✓ Commit 1: "Add user authentication" - Applied cleanly
  ✓ Commit 2: "Update API endpoints" - Applied cleanly
  ✓ Commit 3: "Add validation logic" - Applied cleanly
  ⚠ Commit 4: "Refactor user service" - CONFLICT in src/services/user.ts
  ✓ Commit 5: "Add tests" - Applied (will need conflict resolution first)

Conflicts:
  src/services/user.ts (lines 45-67)
    - Your branch: Added new validation method
    - Parent branch: Refactored the same area

Next Steps:
  • workstack rebase --resolve feature-frontend  (fix conflicts interactively)
  • workstack rebase --apply feature-frontend    (apply if preview looks good)
  • workstack rebase --abort feature-frontend    (discard sandbox)

Sandbox preserved at: ~/worktrees/.sandbox-feature-frontend
```

### 3. Resolve Conflicts in Sandbox (Optional)

```bash
$ workstack rebase --resolve feature-frontend
Opening conflict resolution in sandbox...

File: src/services/user.ts
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<<<<<<< HEAD (feature-backend)
  async validateUser(id: string): Promise<User> {
    // New error handling from backend
    if (!id) {
      throw new ValidationError('User ID required');
    }
    return await this.fetchUser(id);
  }
=======
  async validateUser(id: string): Promise<User> {
    // Your logging addition
    logger.info(`Validating user ${id}`);
    return await this.fetchUser(id);
  }
>>>>>>> feature-frontend
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Resolution options:
  1. Keep parent version (feature-backend)
  2. Keep your version (feature-frontend)
  3. Open in editor (keep both changes manually)
  4. View side-by-side diff

Choose [1-4]: 3

Opening in your editor...
[User manually merges, keeping both error handling and logging]

✓ Conflict resolved in sandbox
✓ All commits now apply cleanly

Would you like to:
  1. Run tests in sandbox
  2. Review full diff
  3. Apply rebase to real branch
  4. Continue editing sandbox
  5. Abort

Choose [1-5]: 1
```

### 4. Test in Sandbox (Optional)

```bash
$ workstack rebase --test feature-frontend
Running tests in sandbox worktree...

npm test
  ✓ Authentication tests (15 passed)
  ✓ User service tests (23 passed)
  ✓ API endpoint tests (18 passed)
  ✓ Validation tests (12 passed)

All tests pass! (68 tests, 3.2s)

The rebased code is working correctly.
Apply rebase to real branch? [Y/n]: Y
```

### 5. Apply the Successful Rebase

```bash
$ workstack rebase --apply feature-frontend
Applying rebase from sandbox to real branch...

Pre-flight checks:
  ✓ Sandbox is clean (no uncommitted changes)
  ✓ Target branch has no uncommitted changes
  ✓ No new commits on parent since preview

Applying rebase:
  ✓ Fast-forwarding feature-backend commits
  ✓ Applying your resolved commits
  ✓ Updating branch pointer
  ✓ Cleaning up sandbox

SUCCESS: feature-frontend rebased onto feature-backend
  - 5 commits successfully applied
  - 1 conflict was resolved
  - All tests passing

Your worktree at ~/worktrees/feature-frontend has been updated.
```

---

## Advanced Features

### Compare Before and After

```bash
$ workstack rebase --compare feature-frontend
Opening comparison view...

Left:  ~/worktrees/feature-frontend (current state)
Right: ~/worktrees/.sandbox-feature-frontend (after rebase)

Files changed: 8 modified, 2 added, 0 deleted
Lines changed: +145, -89

[Opens in your diff tool of choice]
```

### Incremental Conflict Resolution

```bash
$ workstack rebase --preview feature-frontend --interactive
Commit 1/5: "Add user authentication"
  ✓ Applies cleanly
  Continue? [Y/n]: Y

Commit 2/5: "Update API endpoints"
  ✓ Applies cleanly
  Continue? [Y/n]: Y

Commit 3/5: "Add validation logic"
  ⚠ Conflict in src/services/user.ts
  Options:
    1. Resolve now
    2. Skip this commit
    3. Abort rebase
  Choose [1-3]: 1

[Resolves conflict for just this commit before continuing]
```

### Batch Operations

```bash
$ workstack rebase --preview-all
Checking entire stack for rebase needs...

Stack: my-feature-stack
  main
    ├─ backend-auth      [✓ Up to date]
    ├─ backend-api       [⚠ 2 commits behind - no conflicts]
    │   └─ frontend      [⚠ 5 commits behind - 1 conflict]
    │       └─ tests     [⚠ 7 commits behind - 2 conflicts]
    └─ docs             [✓ Up to date]

Create sandboxes for all branches needing rebase? [Y/n]: Y

Created 3 sandboxes:
  - .sandbox-backend-api (no conflicts, ready to apply)
  - .sandbox-frontend (1 conflict, needs resolution)
  - .sandbox-tests (2 conflicts, needs resolution)
```

---

## Safety Guarantees

### What Sandbox Rebase WILL Do:

- ✅ Create an isolated copy of your branch
- ✅ Perform all operations in the sandbox first
- ✅ Preserve your original branch until you explicitly apply changes
- ✅ Allow you to experiment with different resolution strategies
- ✅ Let you run tests before committing to changes
- ✅ Clean up temporary files automatically

### What Sandbox Rebase WON'T Do:

- ❌ Touch your actual branch until you explicitly apply
- ❌ Leave your repository in an inconsistent state
- ❌ Lose any of your commits or changes
- ❌ Create merge commits unless you explicitly choose to
- ❌ Prevent you from aborting at any time

---

## Configuration

```bash
# Set default behavior
$ workstack config set rebase.alwaysUseSandbox true
$ workstack config set rebase.autoRunTests true
$ workstack config set rebase.defaultConflictTool "vimdiff"

# Configure sandbox location
$ workstack config set rebase.sandboxPath "~/.workstack/sandboxes"

# Set preview depth
$ workstack config set rebase.previewCommits 10
```

---

## Why This Changes Everything

### Before Sandbox Rebases

```bash
$ git rebase main
# 😰 "Oh no, conflicts..."
# 😟 "Is this the right resolution?"
# 😨 "Did I break something?"
# 😱 "How do I get back to safety?"
```

### After Sandbox Rebases

```bash
$ workstack rebase --preview my-branch
# 😌 "I can see exactly what will happen"
# 🤔 "Let me try this resolution"
# 🧪 "Tests pass, looks good"
# ✅ "Apply it!"
```

## Implementation Benefits

### For Individual Developers

- **Confidence**: Know exactly what will happen before it happens
- **Safety**: Your work is never at risk
- **Learning**: Experiment with git without fear
- **Speed**: Resolve conflicts once, correctly, without back-and-forth

### For Teams

- **Consistency**: Everyone can safely rebase, not just git experts
- **Quality**: Test rebased code before merging
- **Velocity**: Less time spent on rebase problems
- **Onboarding**: New developers can work with complex stacks safely

### For the Codebase

- **Cleaner History**: More successful rebases mean cleaner git history
- **Fewer Merge Commits**: Confidence in rebasing reduces reliance on merges
- **Better Integration**: Conflicts caught and resolved earlier
- **Maintained Stack Health**: Regular rebasing becomes painless

---

## Success Metrics

| Metric                  | Before    | After (Target) | Measurement                              |
| ----------------------- | --------- | -------------- | ---------------------------------------- |
| Rebase Success Rate     | 60%       | 95%            | % of rebases completed without reverting |
| Average Resolution Time | 25 min    | 10 min         | Time from start to successful completion |
| Rebase Frequency        | Weekly    | Daily          | How often developers rebase              |
| Rebase Anxiety (1-10)   | 7         | 2              | Developer survey                         |
| Lost Work Incidents     | 2-3/month | 0              | Reported data loss from rebases          |

---

## FAQ

**Q: What happens to the sandbox after I'm done?**
A: Sandboxes are automatically cleaned up after successful apply or abort. You can keep them with `--preserve-sandbox` flag.

**Q: Can I have multiple sandboxes?**
A: Yes! Each branch gets its own sandbox. You can have sandboxes for multiple branches simultaneously.

**Q: What if someone pushes to parent branch while I'm resolving?**
A: The apply step checks for new commits and warns you. You can update your sandbox or proceed.

**Q: Can I share sandbox state with teammates?**
A: Sandboxes are local by design, but you can export conflict resolutions as patches to share.

**Q: How much disk space do sandboxes use?**
A: Each sandbox is a git worktree (shares object database), so only working files are duplicated. Typically 10-100MB per sandbox.

**Q: Can I edit code directly in the sandbox?**
A: Yes! The sandbox is a full worktree. You can edit, build, test - anything you'd do in a normal worktree.

---

## Command Reference

```bash
# Preview a rebase without making changes
workstack rebase --preview <branch>

# Resolve conflicts interactively in sandbox
workstack rebase --resolve <branch>

# Run tests in the sandbox
workstack rebase --test <branch>

# Apply successful sandbox rebase to real branch
workstack rebase --apply <branch>

# Abort and clean up sandbox
workstack rebase --abort <branch>

# Compare current branch with sandbox result
workstack rebase --compare <branch>

# Do everything interactively
workstack rebase --interactive <branch>

# Preview all branches in stack
workstack rebase --preview-all

# Keep sandbox for manual inspection
workstack rebase --preview <branch> --preserve-sandbox
```

---

## Summary

Sandbox Rebases eliminate the fear and risk from git rebasing by letting you preview, test, and validate every rebase before it touches your actual branch. This transforms rebasing from a dreaded necessity into a safe, predictable, and even pleasant part of your development workflow.

The key innovation is simple but powerful: **Do everything in a safe space first, then apply only when you're confident.**

With Sandbox Rebases, you'll never lose work to a bad rebase again.
