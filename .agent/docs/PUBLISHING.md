# Publishing Guide

## Overview

This project uses a uv workspace with two packages that are published to PyPI:

1. **dot-agent-kit** - CLI tool for managing .agent/ automated documentation folders
2. **workstack** - Main worktree management tool

All packages share the same version number and are published together.

## Quick Start

```bash
# Use the workstack-dev automated script (recommended)
uv run workstack-dev publish-to-pypi
uv run workstack-dev publish-to-pypi --dry-run  # Preview changes
```

## Publishing Process

### Prerequisites

1. **PyPI Account** - You need a PyPI account with publishing rights
2. **API Token** - Create an API token at https://pypi.org/manage/account/token/
3. **Configure ~/.pypirc** - Set up your credentials file (see below)

### Authentication Setup

The `uvx uv-publish` command reads credentials from `~/.pypirc`. Create this file with your PyPI credentials:

```ini
[pypi]
username = __token__
password = pypi-your-token-here
```

Or with username/password:

```ini
[pypi]
username = your-username
password = your-password
```

Make sure the file has proper permissions:

```bash
chmod 600 ~/.pypirc
```

### Publishing Steps

#### Automated Publishing (Recommended)

The `workstack-dev publish-to-pypi` script automates the entire workflow:

```bash
uv run workstack-dev publish-to-pypi
```

This script:

1. **Validates** git status and version consistency
2. **Pulls** latest changes from remote
3. **Bumps** patch version in all packages
4. **Syncs** dependencies with `uv sync`
5. **Builds** all packages to `dist/`
6. **Publishes** packages:
   - dot-agent-kit
   - workstack
7. **Commits** version changes
8. **Pushes** to remote

Use `--dry-run` to preview changes without making them:

```bash
uv run workstack-dev publish-to-pypi --dry-run
```

#### Manual Publishing

You can publish packages manually using `uvx uv-publish`:

```bash
# Build all packages first
uv build --package dot-agent-kit -o dist
uv build --package workstack -o dist

# Publish dot-agent-kit
uvx uv-publish ./dist/dot_agent_kit-*.whl ./dist/dot_agent_kit-*.tar.gz

# Publish workstack
uvx uv-publish ./dist/workstack-*.whl ./dist/workstack-*.tar.gz
```

## Version Management

All packages share the same version number defined in their respective `pyproject.toml` files:

- **dot-agent-kit**: `packages/dot-agent-kit/pyproject.toml`
- **workstack**: `pyproject.toml`

### Updating Version

The `workstack-dev publish-to-pypi` script automatically handles version updates. It will:

- Validate all packages have the same version
- Bump the patch version (e.g., 0.1.10 → 0.1.11)
- Update all `pyproject.toml` files
- Sync the lockfile
- Commit and push changes

For manual version updates:

1. **Update all version numbers** to match:

   ```toml
   # In packages/dot-agent-kit/pyproject.toml
   [project]
   version = "0.1.11"

   # In pyproject.toml
   [project]
   version = "0.1.11"
   ```

2. **Sync lockfile**:

   ```bash
   uv sync
   ```

3. **Commit the version bump**:

   ```bash
   git add pyproject.toml packages/*/pyproject.toml uv.lock
   git commit -m "Bump version to 0.1.11"
   ```

4. **Create a git tag**:

   ```bash
   git tag v0.1.11
   git push origin v0.1.11
   ```

5. **Publish to PyPI**:
   ```bash
   uv run workstack-dev publish-to-pypi
   ```

## Testing Before Publishing

### Local Testing

Test the built packages locally before publishing:

```bash
# Build packages
uv build --package dot-agent-kit -o dist
uv build --package workstack -o dist

# Install locally in a test environment
uv venv test-env
source test-env/bin/activate
uv pip install ./dist/dot_agent_kit-*.whl
uv pip install ./dist/workstack-*.whl

# Test functionality
workstack --help
dot-agent --help

# Cleanup
deactivate
rm -rf test-env
```

### Test PyPI

For testing the full publishing flow without affecting production PyPI:

1. **Create TestPyPI account**: https://test.pypi.org/
2. **Create API token**: https://test.pypi.org/manage/account/token/
3. **Configure ~/.pypirc for TestPyPI**:

   ```ini
   [testpypi]
   repository = https://test.pypi.org/legacy/
   username = __token__
   password = pypi-test-token-here
   ```

4. **Publish to TestPyPI**:

   ```bash
   # Build packages
   uv build --package dot-agent-kit -o dist
   uv build --package workstack -o dist

   # Publish to TestPyPI (note: uv-publish doesn't support --repository flag yet)
   # You'll need to use twine for TestPyPI:
   uvx twine upload --repository testpypi ./dist/dot_agent_kit-*.whl ./dist/dot_agent_kit-*.tar.gz
   uvx twine upload --repository testpypi ./dist/workstack-*.whl ./dist/workstack-*.tar.gz
   ```

5. **Install from TestPyPI**:
   ```bash
   uv tool install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ workstack
   ```

## Build Artifacts

All build artifacts are placed in the `dist/` directory:

```
dist/
├── dot_agent_kit-0.1.10-py3-none-any.whl
├── dot_agent_kit-0.1.10.tar.gz
├── workstack-0.1.10-py3-none-any.whl
└── workstack-0.1.10.tar.gz
```

- **`.whl`** - Wheel distribution (binary package)
- **`.tar.gz`** - Source distribution

Both are uploaded to PyPI for each package.

## Workspace Structure

```
workstack/                           # Root workspace
├── pyproject.toml                   # Workspace config + workstack package
├── packages/
│   ├── dot-agent-kit/
│   │   ├── pyproject.toml           # dot-agent-kit package metadata
│   │   └── src/dot_agent_kit/       # dot-agent-kit source
│   └── workstack-dev/
│       ├── pyproject.toml           # workstack-dev (dev tools, not published)
│       └── src/workstack_dev/       # workstack-dev source
└── src/workstack/                   # workstack source
```

The workspace is configured in the root `pyproject.toml`:

```toml
[tool.uv.workspace]
members = ["packages/*"]

[tool.uv.sources]
dot-agent-kit = { workspace = true }
workstack-dev = { workspace = true }
```

## Troubleshooting

### "Missing credentials" error

**Problem**: `uvx uv-publish` fails with "Missing credentials"

**Solution**: Configure `~/.pypirc` with your credentials:

```ini
[pypi]
username = __token__
password = pypi-your-token-here
```

Then ensure proper permissions:

```bash
chmod 600 ~/.pypirc
```

### "File already exists" error

**Problem**: `uv publish` fails because the version already exists on PyPI

**Solution**: Bump the version number in both `pyproject.toml` files and try again. PyPI does not allow overwriting existing versions.

### Build artifacts from previous version

**Problem**: Old build artifacts in `dist/` from a previous version

**Solution**: Remove old artifacts with `rm -rf dist/` before building.

## CI/CD Publishing

For automated publishing via GitHub Actions or other CI:

```yaml
# Example GitHub Actions workflow
name: Publish to PyPI

on:
  push:
    tags:
      - "v*"

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Install uv
        run: pip install uv

      - name: Configure PyPI credentials
        run: |
          cat > ~/.pypirc << EOF
          [pypi]
          username = __token__
          password = ${{ secrets.PYPI_API_TOKEN }}
          EOF
          chmod 600 ~/.pypirc

      - name: Build and publish
        run: uv run workstack-dev publish-to-pypi
```

Store your PyPI token as `PYPI_API_TOKEN` in GitHub repository secrets.

**Note**: `uvx uv-publish` reads credentials from `~/.pypirc`, not environment variables.

## Release Checklist

Before publishing a new version:

- [ ] All tests pass: `uv run pytest`
- [ ] Linting passes: `uv run ruff check`
- [ ] Type checking passes: `uv run pyright`
- [ ] Version updated in both `pyproject.toml` files (or use automated script)
- [ ] Changelog/release notes updated (if applicable)
- [ ] Changes committed and pushed
- [ ] PyPI credentials configured in `~/.pypirc`
- [ ] Published to PyPI: `uv run workstack-dev publish-to-pypi`
- [ ] Verify on PyPI:
  - https://pypi.org/project/dot-agent-kit/
  - https://pypi.org/project/workstack/
- [ ] Test installation:
  - `uv tool install workstack`
  - `uv tool install dot-agent-kit`

## Adding a New Package to the Workspace

To add a new package to the publishing workflow:

### 1. Create the Package Structure

```bash
mkdir -p packages/my-package/src/my_package
```

### 2. Create pyproject.toml

Create `packages/my-package/pyproject.toml`:

```toml
[project]
name = "my-package"
version = "0.1.0"  # Must match other packages
description = "Package description"
readme = "README.md"
authors = [
    { name = "Dagster Labs", email = "hello@dagsterlabs.com" }
]
license = { text = "MIT" }
requires-python = ">=3.13"
dependencies = [
    # Add dependencies here
]

[project.urls]
Homepage = "https://github.com/dagster-io/workstack"
Repository = "https://github.com/dagster-io/workstack"
Issues = "https://github.com/dagster-io/workstack/issues"

[project.scripts]
my-package = "my_package.cli:main"  # If CLI entry point

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/my_package"]
```

### 3. Update Workspace Configuration

The workspace automatically includes all packages in `packages/*/` via:

```toml
[tool.uv.workspace]
members = ["packages/*"]
```

If the main workstack package depends on your new package, add it to the root `pyproject.toml`:

```toml
[tool.uv.sources]
my-package = { workspace = true }
```

### 4. Update Publishing Script

Edit `packages/workstack-dev/src/workstack_dev/commands/publish_to_pypi/command.py` in the `get_workspace_packages` function:

```python
def get_workspace_packages(repo_root: Path) -> list[PackageInfo]:
    """Get all publishable packages in workspace."""
    packages = [
        PackageInfo(
            name="dot-agent-kit",
            path=repo_root / "packages" / "dot-agent-kit",
            pyproject_path=repo_root / "packages" / "dot-agent-kit" / "pyproject.toml",
        ),
        # Add your package here
        PackageInfo(
            name="my-package",
            path=repo_root / "packages" / "my-package",
            pyproject_path=repo_root / "packages" / "my-package" / "pyproject.toml",
        ),
        PackageInfo(
            name="workstack",
            path=repo_root,
            pyproject_path=repo_root / "pyproject.toml",
        ),
    ]
```

### 5. Update Git Status Check

Edit the same file to exclude your package's pyproject.toml from git status checks:

```python
    excluded_files = {
        "pyproject.toml",
        "uv.lock",
        "packages/dot-agent-kit/pyproject.toml",
        "packages/my-package/pyproject.toml",  # Add this
    }
```

### 6. Update Documentation

Update this file (`.agent/docs/PUBLISHING.md`) to include your package in:

- Overview section (list of packages)
- Publishing order
- Build artifacts example
- Release checklist (PyPI URLs, test installation)

### 6. Sync and Test

```bash
# Sync the lockfile
uv sync

# Test building
uv build --package my-package -o dist

# Verify artifacts
ls -la dist/
```

### 7. Version Consistency

Ensure your new package has the same version as other packages before first publish:

```toml
version = "0.1.11"  # Match current version
```

The automated publishing script will keep all versions in sync going forward.

## References

- **uv Documentation**: https://docs.astral.sh/uv/
- **PyPI Publishing Guide**: https://packaging.python.org/guides/distributing-packages-using-setuptools/
