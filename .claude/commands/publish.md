You are a package publishing assistant. Your task is to bump the version number, sync dependencies, publish the package, and commit the changes.

## Your Task

Execute the full publishing workflow for this Python package:

1. Check the current version number in `pyproject.toml`
2. Bump the version to the next patch version (e.g., 0.1.6 → 0.1.7)
3. Run `uv sync` to update the lock file
4. Run `make publish` to build and publish to PyPI
5. Commit the changes with message "Published X.Y.Z"
6. Push the commit to the remote repository

## Process

### 1. Read Current Version

Read `pyproject.toml` and extract the current version number from the `version` field.

### 2. Bump Version

Calculate the next patch version by incrementing the last number:
- Current: `0.1.6` → New: `0.1.7`
- Current: `0.2.9` → New: `0.2.10`
- Current: `1.0.0` → New: `1.0.1`

Update the version in `pyproject.toml` using the Edit tool.

### 3. Sync Dependencies

Run `uv sync` to update `uv.lock` with the new version.

### 4. Publish Package

Run `make publish` which will:
- Clean old builds: `rm -rf dist/*.whl dist/*.tar.gz`
- Build new distribution: `uv build`
- Publish to PyPI: `uvx uv-publish`

Verify the publish completes successfully.

### 5. Commit Changes

Create a git commit with the modified files:
- `pyproject.toml` (version bump)
- `uv.lock` (updated version reference)

Use commit message format:
```
Published X.Y.Z

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

Where `X.Y.Z` is the new version number.

### 6. Push to Remote

Push the commit to the remote repository with `git push`.

## Error Handling

If any step fails:
- **uv sync fails**: Check for dependency conflicts in `pyproject.toml`
- **make publish fails**: Verify PyPI credentials are configured
- **git push fails**: Check if branch is protected or needs pull first

## Output

After successful completion, report:
- Old version → New version
- PyPI publish status
- Git commit SHA
- Remote push status

Example output:
```
✓ Version bumped: 0.1.6 → 0.1.7
✓ Dependencies synced
✓ Published to PyPI: workstack-0.1.7
✓ Committed: bae260f "Published 0.1.7"
✓ Pushed to origin/main
```

Begin the publishing workflow now.
