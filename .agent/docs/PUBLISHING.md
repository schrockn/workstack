# Publishing Guide

## Overview

This project uses a uv workspace with three packages that are published to PyPI:

1. **devclikit** - Framework for building development CLIs with PEP 723 script support
2. **dot-agent-kit** - CLI tool for managing .agent/ automated documentation folders
3. **workstack** - Main worktree management tool (depends on devclikit)

All packages share the same version number and are published together.

## Quick Start

```bash
# Build all packages
make build

# Publish to PyPI (requires credentials)
make publish

# Or use the workstack-dev automated script (recommended)
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
6. **Publishes** in dependency order:
   - devclikit (no dependencies)
   - dot-agent-kit (no dependencies)
   - workstack (depends on devclikit)
7. **Commits** version changes
8. **Pushes** to remote

Use `--dry-run` to preview changes without making them:

```bash
uv run workstack-dev publish-to-pypi --dry-run
```

#### Manual Publishing

The `make publish` target automatically:

1. **Cleans** old build artifacts from `dist/`
2. **Builds devclikit** from `packages/devclikit/`
3. **Builds dot-agent-kit** from `packages/dot-agent-kit/`
4. **Builds workstack** from the root
5. **Publishes devclikit** first (since workstack depends on it)
6. **Publishes dot-agent-kit** second
7. **Publishes workstack** third

```bash
make publish
```

Output:

```
Publishing devclikit...
Uploading devclikit-0.1.10-py3-none-any.whl (12.4KiB)
Uploading devclikit-0.1.10.tar.gz (9.3KiB)
Publishing dot-agent-kit...
Uploading dot-agent-kit-0.1.10-py3-none-any.whl (15KiB)
Uploading dot-agent-kit-0.1.10.tar.gz (11KiB)
Publishing workstack...
Uploading workstack-0.1.10-py3-none-any.whl (79KiB)
Uploading workstack-0.1.10.tar.gz (183KiB)
✓ All packages published successfully
```

#### Advanced Manual Publishing

If you need more control, you can publish manually:

```bash
# Build all packages
make build

# Publish devclikit first
uvx uv-publish ./dist/devclikit-*.whl ./dist/devclikit-*.tar.gz

# Publish dot-agent-kit second
uvx uv-publish ./dist/dot-agent-kit-*.whl ./dist/dot-agent-kit-*.tar.gz

# Publish workstack third (after devclikit is available on PyPI)
uvx uv-publish ./dist/workstack-*.whl ./dist/workstack-*.tar.gz
```

## Version Management

All packages share the same version number defined in their respective `pyproject.toml` files:

- **devclikit**: `packages/devclikit/pyproject.toml`
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
   # In packages/devclikit/pyproject.toml
   [project]
   version = "0.1.11"

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
   make publish
   ```

## Package Order

**IMPORTANT**: Always publish packages in dependency order:

1. **devclikit** - Has no dependencies, publish first
2. **dot-agent-kit** - Has no dependencies on our packages, can publish anytime after devclikit
3. **workstack** - Depends on devclikit, must publish last

The `workstack-dev publish-to-pypi` script and `make publish` target handle this automatically.

If you publish manually, ensure devclikit is available on PyPI before publishing workstack, otherwise users installing workstack will fail to find the devclikit dependency.

## Testing Before Publishing

### Local Testing

Test the built packages locally before publishing:

```bash
# Build packages
make build

# Install locally in a test environment
uv venv test-env
source test-env/bin/activate
uv pip install ./dist/devclikit-*.whl
uv pip install ./dist/dot-agent-kit-*.whl
uv pip install ./dist/workstack-*.whl

# Test functionality
workstack --help
workstack-dev --help
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
   make build

   # Publish to TestPyPI (note: uv-publish doesn't support --repository flag yet)
   # You'll need to use twine for TestPyPI:
   uvx twine upload --repository testpypi ./dist/devclikit-*.whl ./dist/devclikit-*.tar.gz
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
├── devclikit-0.1.10-py3-none-any.whl
├── devclikit-0.1.10.tar.gz
├── dot-agent-kit-0.1.10-py3-none-any.whl
├── dot-agent-kit-0.1.10.tar.gz
├── workstack-0.1.10-py3-none-any.whl
└── workstack-0.1.10.tar.gz
```

- **`.whl`** - Wheel distribution (binary package)
- **`.tar.gz`** - Source distribution

Both are uploaded to PyPI for each package.

## Makefile Targets

| Target         | Description                                   |
| -------------- | --------------------------------------------- |
| `make clean`   | Remove all build artifacts from `dist/`       |
| `make build`   | Build devclikit, dot-agent-kit, and workstack |
| `make publish` | Build and publish all three packages to PyPI  |

## Workspace Structure

```
workstack/                           # Root workspace
├── pyproject.toml                   # Workspace config + workstack package
├── packages/
│   ├── devclikit/
│   │   ├── pyproject.toml           # devclikit package metadata
│   │   └── src/devclikit/           # devclikit source
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
devclikit = { workspace = true }
dot-agent-kit = { workspace = true }
workstack-dev = { workspace = true }
```

This allows workstack to depend on the local devclikit during development, but the published workstack package will depend on devclikit from PyPI.

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

### "Could not find dependency" error during install

**Problem**: Users can't install workstack because devclikit is not found

**Solution**: Ensure devclikit was published first and is available on PyPI before publishing workstack.

### Build artifacts from previous version

**Problem**: Old build artifacts in `dist/` from a previous version

**Solution**: Run `make clean` before building or use `make build` which includes the clean step.

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
        run: make publish
```

Store your PyPI token as `PYPI_API_TOKEN` in GitHub repository secrets.

**Note**: `uvx uv-publish` reads credentials from `~/.pypirc`, not environment variables.

## Release Checklist

Before publishing a new version:

- [ ] All tests pass: `make test`
- [ ] Linting passes: `make lint`
- [ ] Type checking passes: `make pyright`
- [ ] Version updated in all three `pyproject.toml` files (or use automated script)
- [ ] Changelog/release notes updated (if applicable)
- [ ] Changes committed and pushed
- [ ] Git tag created: `git tag v0.1.x` (optional for automated script)
- [ ] Tag pushed: `git push origin v0.1.x` (optional for automated script)
- [ ] PyPI credentials configured in `~/.pypirc`
- [ ] Build succeeds: `make build`
- [ ] Published to PyPI: `uv run workstack-dev publish-to-pypi` or `make publish`
- [ ] Verify on PyPI:
  - https://pypi.org/project/devclikit/
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

Edit `packages/workstack-dev/src/workstack_dev/commands/publish_to_pypi/script.py:114`:

```python
def get_workspace_packages(repo_root: Path) -> list[PackageInfo]:
    """Get all publishable packages in workspace.

    Returns:
        List of packages in dependency order (dependencies first)
    """
    packages = [
        PackageInfo(
            name="devclikit",
            path=repo_root / "packages" / "devclikit",
            pyproject_path=repo_root / "packages" / "devclikit" / "pyproject.toml",
        ),
        PackageInfo(
            name="dot-agent-kit",
            path=repo_root / "packages" / "dot-agent-kit",
            pyproject_path=repo_root / "packages" / "dot-agent-kit" / "pyproject.toml",
        ),
        # Add your package here (in dependency order)
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

Edit the same file around line 544 to exclude your package's pyproject.toml from git status checks:

```python
    excluded_files = {
        "pyproject.toml",
        "uv.lock",
        "packages/devclikit/pyproject.toml",
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

### 7. Sync and Test

```bash
# Sync the lockfile
uv sync

# Test building
make build

# Verify artifacts
ls -la dist/
```

### 8. Version Consistency

Ensure your new package has the same version as other packages before first publish:

```toml
version = "0.1.11"  # Match current version
```

The automated publishing script will keep all versions in sync going forward.

## References

- **uv Documentation**: https://docs.astral.sh/uv/
- **PyPI Publishing Guide**: https://packaging.python.org/guides/distributing-packages-using-setuptools/
- **Workspace Setup**: See `devclikit-extraction-plan.md` for the original workspace migration plan
