# Publishing Guide

## Overview

This project uses a uv workspace with two packages that are published to PyPI:

1. **devclikit** - Framework for building development CLIs with PEP 723 script support
2. **workstack** - Main worktree management tool (depends on devclikit)

Both packages share the same version number and are published together.

## Quick Start

```bash
# Build both packages
make build

# Publish to PyPI (requires credentials)
make publish
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

The `make publish` target automatically:

1. **Cleans** old build artifacts from `dist/`
2. **Builds devclikit** from `packages/devclikit/`
3. **Builds workstack** from the root
4. **Publishes devclikit** first (since workstack depends on it)
5. **Publishes workstack** second

```bash
make publish
```

Output:

```
Publishing devclikit...
Uploading devclikit-0.1.10-py3-none-any.whl (12.4KiB)
Uploading devclikit-0.1.10.tar.gz (9.3KiB)
Publishing workstack...
Uploading workstack-0.1.10-py3-none-any.whl (79KiB)
Uploading workstack-0.1.10.tar.gz (183KiB)
✓ Both packages published successfully
```

### Manual Publishing

If you need more control, you can publish manually:

```bash
# Build both packages
make build

# Publish devclikit first
uvx uv-publish ./dist/devclikit-*.whl ./dist/devclikit-*.tar.gz

# Publish workstack second (after devclikit is available on PyPI)
uvx uv-publish ./dist/workstack-*.whl ./dist/workstack-*.tar.gz
```

## Version Management

Both packages share the same version number defined in their respective `pyproject.toml` files:

- **devclikit**: `packages/devclikit/pyproject.toml`
- **workstack**: `pyproject.toml`

### Updating Version

Before publishing a new release:

1. **Update both version numbers** to match:

   ```toml
   # In packages/devclikit/pyproject.toml
   [project]
   version = "0.1.11"

   # In pyproject.toml
   [project]
   version = "0.1.11"
   ```

2. **Commit the version bump**:

   ```bash
   git add pyproject.toml packages/devclikit/pyproject.toml
   git commit -m "Bump version to 0.1.11"
   ```

3. **Create a git tag**:

   ```bash
   git tag v0.1.11
   git push origin v0.1.11
   ```

4. **Publish to PyPI**:
   ```bash
   make publish
   ```

## Package Order

**IMPORTANT**: Always publish `devclikit` before `workstack` because workstack depends on devclikit.

The `make publish` target handles this automatically by publishing devclikit first.

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
uv pip install ./dist/workstack-*.whl

# Test functionality
workstack --help
workstack-dev --help

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
├── workstack-0.1.10-py3-none-any.whl
└── workstack-0.1.10.tar.gz
```

- **`.whl`** - Wheel distribution (binary package)
- **`.tar.gz`** - Source distribution

Both are uploaded to PyPI for each package.

## Makefile Targets

| Target         | Description                                 |
| -------------- | ------------------------------------------- |
| `make clean`   | Remove all build artifacts from `dist/`     |
| `make build`   | Build both devclikit and workstack packages |
| `make publish` | Build and publish both packages to PyPI     |

## Workspace Structure

```
workstack/                           # Root workspace
├── pyproject.toml                   # Workspace config + workstack package
├── packages/
│   └── devclikit/
│       ├── pyproject.toml           # devclikit package metadata
│       └── src/devclikit/           # devclikit source
└── src/workstack/                   # workstack source
```

The workspace is configured in the root `pyproject.toml`:

```toml
[tool.uv.workspace]
members = ["packages/*"]

[tool.uv.sources]
devclikit = { workspace = true }
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
- [ ] Version updated in both `pyproject.toml` files
- [ ] Changelog/release notes updated (if applicable)
- [ ] Changes committed and pushed
- [ ] Git tag created: `git tag v0.1.x`
- [ ] Tag pushed: `git push origin v0.1.x`
- [ ] PyPI credentials configured
- [ ] Build succeeds: `make build`
- [ ] Published to PyPI: `make publish`
- [ ] Verify on PyPI:
  - https://pypi.org/project/devclikit/
  - https://pypi.org/project/workstack/
- [ ] Test installation: `uv tool install workstack`

## References

- **uv Documentation**: https://docs.astral.sh/uv/
- **PyPI Publishing Guide**: https://packaging.python.org/guides/distributing-packages-using-setuptools/
- **Workspace Setup**: See `devclikit-extraction-plan.md` for the original workspace migration plan
