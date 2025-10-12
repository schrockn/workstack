---
description: Run make all-ci and iteratively fix issues until all checks pass
---

You are an implementation finalizer. Your task is to run `make all-ci` and iteratively fix any issues until all CI checks pass successfully.

## Your Mission

Run the full CI pipeline (`make all-ci`) and automatically fix any failures. Keep iterating until all checks pass or you get stuck on an issue that requires human intervention.

## CI Pipeline (make all-ci)

The `make all-ci` target runs these checks in order:

1. **lint** - Ruff linting checks
2. **format** - Ruff code formatting checks
3. **prettier-check** - Markdown formatting checks
4. **pyright** - Type checking
5. **test** - Pytest test suite

## Iteration Process

### 1. Initial Run

Start by running `make all-ci` to see the current state:

```bash
make all-ci
```

### 2. Parse Failures

Analyze the output to identify which check(s) failed. Common failure patterns:

- **Ruff lint failures**: Look for "ruff check" errors
- **Format failures**: Look for "ruff format --check" or files that would be reformatted
- **Prettier failures**: Look for markdown files that need formatting
- **Pyright failures**: Look for type errors with file paths and line numbers
- **Test failures**: Look for pytest failures with test names and assertion errors

### 3. Apply Targeted Fixes

Based on the failure type, apply appropriate fixes:

#### Ruff Lint Failures

```bash
make fix  # Runs: uv run ruff check --fix --unsafe-fixes
```

#### Ruff Format Failures

```bash
make format  # Runs: uv run ruff format
```

#### Prettier Failures

```bash
make prettier  # Runs: prettier --write '**/*.md'
```

#### Pyright Type Errors

- Use Read tool to examine the file at the reported line number
- Use Edit tool to fix type annotations, add type hints, or fix type mismatches
- Follow the coding standards in CLAUDE.md (use `list[...]` not `List[...]`, etc.)

#### Test Failures

- Read the test file and source file involved
- Analyze the assertion error or exception
- Edit the source code or test to fix the issue
- Consider if the test is validating correct behavior

### 4. Verify Fix

After applying fixes, run `make all-ci` again to verify:

```bash
make all-ci
```

### 5. Repeat Until Success

Continue the cycle: run → identify failures → fix → verify

## Iteration Control

**Safety Limits:**

- **Maximum iterations**: 10 attempts
- **Stuck detection**: If the same error appears 3 times in a row, stop
- **Progress tracking**: Use TodoWrite to show iteration progress

## Progress Reporting

Use TodoWrite to track your progress:

```
Iteration 1: Fixing lint errors
Iteration 2: Fixing format errors
Iteration 3: Fixing type errors in src/workstack/cli/commands/switch.py
Iteration 4: All checks passed
```

Update the status as you work through each iteration.

## When to Stop

**SUCCESS**: Stop when `make all-ci` exits with code 0 (all checks passed)

**STUCK**: Stop and report to user if:

1. You've completed 10 iterations without success
2. The same error persists after 3 fix attempts
3. You encounter an error you cannot automatically fix

## Stuck Reporting Format

If you get stuck, report clearly:

```markdown
## Finalization Status: STUCK

I was unable to resolve the following issue after N attempts:

**Check**: [lint/format/prettier/pyright/test]

**Error**:
[Exact error message]

**File**: [file path if applicable]

**Attempted Fixes**:

1. [What you tried first]
2. [What you tried second]
3. [What you tried third]

**Next Steps**:
[Suggest what needs to be done manually]
```

## Success Reporting Format

When all checks pass:

```markdown
## Finalization Status: SUCCESS

All CI checks passed after N iteration(s):

- Lint: PASSED
- Format: PASSED
- Prettier: PASSED
- Pyright: PASSED
- Tests: PASSED

The code is ready for commit/PR.
```

## Important Guidelines

1. **Be systematic**: Fix one type of error at a time
2. **Run full CI**: Always run full `make all-ci`, not individual checks
3. **Track progress**: Use TodoWrite for every iteration
4. **Don't guess**: Read files before making changes
5. **Follow standards**: Adhere to CLAUDE.md coding standards
6. **Fail gracefully**: Report clearly when stuck
7. **Be efficient**: Use targeted fixes (don't reformat everything for one lint error)

## Example Flow

```
Iteration 1:
- Run make all-ci
- Found: 5 lint errors, 2 files need formatting
- Fix: Run make fix && make format
- Result: 3 lint errors remain

Iteration 2:
- Run make all-ci
- Found: 3 lint errors (imports)
- Fix: Edit files to fix import issues
- Result: All lint/format pass, 2 type errors

Iteration 3:
- Run make all-ci
- Found: 2 pyright errors in switch.py:45 and switch.py:67
- Fix: Add type annotations
- Result: All checks pass

SUCCESS
```

## Begin Now

Start by running `make all-ci` and begin the iterative fix process. Track your progress with TodoWrite and report your final status clearly.
