# Synchronized Multi-Package Publishing - Implementation Plan

**Status**: Planning Phase
**Created**: 2025-10-10
**Goal**: Transform single-package publish workflow into synchronized multi-package publisher

## Executive Summary

This plan transforms the current `publish_to_pypi` script to publish both `workstack` and `devclikit` packages in unison, maintaining version synchronization and ensuring atomic publishing with proper error handling.

## Current State

### Project Structure
- **Workspace**: uv workspace with two packages
  - `workstack` (main package, v0.1.10) - CLI for git worktree management
  - `devclikit` (dependency package, v0.1.10) - Framework for dev CLIs with PEP 723 support
- **Dependency**: workstack depends on devclikit as workspace dependency
- **Location**: Root pyproject.toml and packages/devclikit/pyproject.toml

### Current Publishing Process
- **Script**: `src/workstack/dev_cli/commands/publish_to_pypi/script.py`
- **Scope**: Only publishes workstack package
- **Workflow**:
  1. Pull latest changes from git
  2. Bump version in root pyproject.toml (patch increment)
  3. Update lockfile with `uv sync`
  4. Build and publish via `make publish`
  5. Commit version changes and lockfile
  6. Push to remote

### Current Build/Publish Commands
- **Build**: `uv build` (builds only root package)
- **Publish**: `uvx uv-publish` (publishes built artifacts)
- **Makefile**: `make publish` runs `clean`, `uv build`, `uvx uv-publish`

## Requirements

### Functional Requirements
1. **Version Synchronization**: Both packages must have identical version numbers
2. **Atomic Publishing**: Both packages publish successfully or neither publishes
3. **Dependency-Aware**: Publish devclikit before workstack (dependency order)
4. **Git Integration**: Commit both pyproject.toml files after successful publish
5. **Dry Run Support**: Test entire workflow without making changes

### Non-Functional Requirements
1. **Error Handling**: Clear error messages for each failure point
2. **Rollback Capability**: Ability to recover from partial failures
3. **Idempotency**: Safe to re-run after failures
4. **Validation**: Pre-flight checks before irreversible operations

## Implementation Design

### Phase 1: Multi-Package Discovery

#### File: `script.py`

Add package discovery functionality:

```python
@dataclass(frozen=True)
class PackageInfo:
    """Information about a publishable package."""
    name: str
    path: Path
    pyproject_path: Path

def discover_workspace_packages(repo_root: Path) -> list[PackageInfo]:
    """Discover all publishable packages in workspace.

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
            name="workstack",
            path=repo_root,
            pyproject_path=repo_root / "pyproject.toml",
        ),
    ]

    # Validate all packages exist
    for pkg in packages:
        if not pkg.pyproject_path.exists():
            click.echo(f"✗ Package not found: {pkg.name} at {pkg.path}", err=True)
            raise SystemExit(1)

    return packages
```

**Verification**: Script can discover both packages and validate their existence.

### Phase 2: Synchronized Version Management

#### Update Version Functions

Extend existing version functions to handle multiple packages:

```python
def get_current_version(pyproject_path: Path) -> str:
    """Parse current version from pyproject.toml."""
    # Existing implementation stays the same
    pass

def validate_version_consistency(packages: list[PackageInfo]) -> str:
    """Ensure all packages have the same version.

    Returns:
        The current version if consistent

    Raises:
        SystemExit: If versions are inconsistent
    """
    versions = {}
    for pkg in packages:
        version = get_current_version(pkg.pyproject_path)
        versions[pkg.name] = version

    unique_versions = set(versions.values())
    if len(unique_versions) > 1:
        click.echo("✗ Version mismatch across packages:", err=True)
        for name, version in versions.items():
            click.echo(f"  {name}: {version}", err=True)
        raise SystemExit(1)

    return list(unique_versions)[0]

def synchronize_versions(
    packages: list[PackageInfo],
    old_version: str,
    new_version: str,
    dry_run: bool,
) -> None:
    """Update version in all package pyproject.toml files.

    Args:
        packages: List of packages to update
        old_version: Current version to replace
        new_version: New version to write
        dry_run: If True, skip actual file writes
    """
    for pkg in packages:
        update_version(pkg.pyproject_path, old_version, new_version, dry_run)
        if not dry_run:
            click.echo(f"  ✓ Updated {pkg.name}: {old_version} → {new_version}")
```

**Verification**: Both pyproject.toml files updated to same version.

### Phase 3: Multi-Package Build Orchestration

#### Build All Packages

```python
def build_package(package: PackageInfo, out_dir: Path, dry_run: bool) -> None:
    """Build a specific package in the workspace.

    Args:
        package: Package to build
        out_dir: Output directory for artifacts
        dry_run: If True, skip actual build
    """
    if dry_run:
        click.echo(f"[DRY RUN] Would run: uv build --package {package.name} -o {out_dir}")
        return

    run_command(
        ["uv", "build", "--package", package.name, "-o", str(out_dir)],
        cwd=package.path.parent if package.name == "devclikit" else package.path,
        description=f"build {package.name}",
    )

def build_all_packages(
    packages: list[PackageInfo],
    repo_root: Path,
    dry_run: bool,
) -> Path:
    """Build all packages to a staging directory.

    Returns:
        Path to staging directory containing all artifacts
    """
    # Create staging directory
    staging_dir = repo_root / "dist"
    if staging_dir.exists() and not dry_run:
        # Clean existing artifacts
        for artifact in staging_dir.glob("*"):
            artifact.unlink()
    elif not dry_run:
        staging_dir.mkdir(parents=True, exist_ok=True)

    click.echo("\nBuilding packages...")
    for pkg in packages:
        build_package(pkg, staging_dir, dry_run)
        click.echo(f"  ✓ Built {pkg.name}")

    return staging_dir

def validate_build_artifacts(
    packages: list[PackageInfo],
    staging_dir: Path,
    version: str,
    dry_run: bool,
) -> None:
    """Verify all expected artifacts exist.

    Args:
        packages: List of packages that were built
        staging_dir: Directory containing artifacts
        version: Version number to check
        dry_run: If True, skip validation
    """
    if dry_run:
        click.echo("[DRY RUN] Would validate artifacts exist")
        return

    for pkg in packages:
        wheel = staging_dir / f"{pkg.name}-{version}-py3-none-any.whl"
        sdist = staging_dir / f"{pkg.name}-{version}.tar.gz"

        if not wheel.exists():
            click.echo(f"✗ Missing wheel: {wheel}", err=True)
            raise SystemExit(1)
        if not sdist.exists():
            click.echo(f"✗ Missing sdist: {sdist}", err=True)
            raise SystemExit(1)

    click.echo("  ✓ All artifacts validated")
```

**Verification**: Both .whl and .tar.gz files exist in dist/ for each package.

### Phase 4: Dependency-Aware Publishing

#### Publish Sequencer

```python
def publish_package(package: PackageInfo, staging_dir: Path, dry_run: bool) -> None:
    """Publish a single package to PyPI.

    Args:
        package: Package to publish
        staging_dir: Directory containing built artifacts
        dry_run: If True, skip actual publish
    """
    if dry_run:
        click.echo(f"[DRY RUN] Would publish {package.name} to PyPI")
        return

    # uv-publish will publish all artifacts in the directory that match the package
    # We need to filter to only this package's artifacts
    run_command(
        ["uvx", "uv-publish", "--package", package.name],
        cwd=staging_dir,
        description=f"publish {package.name}",
    )

def wait_for_pypi_availability(package: PackageInfo, version: str, dry_run: bool) -> None:
    """Wait for package to be available on PyPI.

    Args:
        package: Package to check
        version: Version to wait for
        dry_run: If True, skip wait
    """
    if dry_run:
        click.echo(f"[DRY RUN] Would wait for {package.name} {version} on PyPI")
        return

    import time
    wait_seconds = 5
    click.echo(f"  ⏳ Waiting {wait_seconds}s for PyPI propagation...")
    time.sleep(wait_seconds)

def publish_all_packages(
    packages: list[PackageInfo],
    staging_dir: Path,
    version: str,
    dry_run: bool,
) -> None:
    """Publish all packages in dependency order.

    Packages are already sorted in dependency order (devclikit first).
    """
    click.echo("\nPublishing to PyPI...")

    for i, pkg in enumerate(packages):
        publish_package(pkg, staging_dir, dry_run)
        click.echo(f"  ✓ Published {pkg.name} {version}")

        # Wait after publishing dependencies (all but last)
        if i < len(packages) - 1:
            wait_for_pypi_availability(pkg, version, dry_run)
```

**Verification**: Both packages visible on PyPI with same version.

### Phase 5: Git Integration Updates

#### Update Commit Function

```python
def commit_changes(
    repo_root: Path,
    packages: list[PackageInfo],
    version: str,
    dry_run: bool,
) -> str:
    """Commit version bump changes for all packages.

    Args:
        repo_root: Repository root directory
        packages: List of packages that were updated
        version: New version number
        dry_run: If True, print commands instead of executing

    Returns:
        Commit SHA (or fake SHA in dry-run mode)
    """
    commit_message = f"""Published workstack and devclikit {version}

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"""

    if dry_run:
        files_to_add = [str(pkg.pyproject_path.relative_to(repo_root)) for pkg in packages]
        files_to_add.append("uv.lock")
        click.echo(f"[DRY RUN] Would run: git add {' '.join(files_to_add)}")
        click.echo(f'[DRY RUN] Would run: git commit -m "Published {version}..."')
        return "abc123f"

    # Add all pyproject.toml files and lockfile
    files_to_add = [str(pkg.pyproject_path.relative_to(repo_root)) for pkg in packages]
    files_to_add.append("uv.lock")

    run_command(
        ["git", "add"] + files_to_add,
        cwd=repo_root,
        description="git add",
    )

    # Commit changes
    run_command(
        ["git", "commit", "-m", commit_message],
        cwd=repo_root,
        description="git commit",
    )

    # Get commit SHA
    sha = run_command(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=repo_root,
        description="get commit SHA",
    )

    return sha
```

**Verification**: Git commit includes both pyproject.toml files and uv.lock.

### Phase 6: Update Main Workflow

#### Updated main() Function

```python
@click.command()
@click.option("--dry-run", is_flag=True, help="Show what would be done without making changes")
def main(dry_run: bool) -> None:
    """Execute the synchronized multi-package publishing workflow."""
    if dry_run:
        click.echo("[DRY RUN MODE - No changes will be made]\n")

    # Step 0: Setup
    repo_root = Path.cwd()
    if not (repo_root / "pyproject.toml").exists():
        click.echo("✗ Not in repository root (pyproject.toml not found)", err=True)
        click.echo("  Run this command from the repository root directory", err=True)
        raise SystemExit(1)

    # Step 1: Discover packages
    click.echo("Discovering workspace packages...")
    packages = discover_workspace_packages(repo_root)
    click.echo(f"  ✓ Found {len(packages)} packages: {', '.join(p.name for p in packages)}")

    # Step 2: Check git status
    status = get_git_status(repo_root)
    if status:
        # Filter out version files that will be updated
        excluded_files = {
            "pyproject.toml",
            "uv.lock",
            "packages/devclikit/pyproject.toml",
        }
        lines = filter_git_status(status, excluded_files)

        if lines:
            click.echo("✗ Working directory has uncommitted changes:", err=True)
            for line in lines:
                click.echo(f"  {line}", err=True)
            raise SystemExit(1)

    click.echo("\nStarting synchronized publish workflow...\n")

    # Step 3: Pull latest changes
    run_git_pull(repo_root, dry_run)

    # Step 4: Validate version consistency
    old_version = validate_version_consistency(packages)
    click.echo(f"  ✓ Current version: {old_version} (consistent)")

    # Step 5: Bump versions
    new_version = bump_patch_version(old_version)
    click.echo(f"\nBumping version: {old_version} → {new_version}")
    synchronize_versions(packages, old_version, new_version, dry_run)

    # Step 6: Update lockfile
    run_uv_sync(repo_root, dry_run)

    # Step 7: Build all packages
    staging_dir = build_all_packages(packages, repo_root, dry_run)
    validate_build_artifacts(packages, staging_dir, new_version, dry_run)

    # Step 8: Publish all packages
    publish_all_packages(packages, staging_dir, new_version, dry_run)

    # Step 9: Commit changes
    sha = commit_changes(repo_root, packages, new_version, dry_run)
    click.echo(f'\n✓ Committed: {sha} "Published {new_version}"')

    # Step 10: Push to remote
    push_to_remote(repo_root, dry_run)
    click.echo("✓ Pushed to origin")

    # Success summary
    click.echo(f"\n✅ Successfully published:")
    for pkg in packages:
        click.echo(f"  • {pkg.name} {new_version}")
```

**Verification**: Entire workflow executes successfully end-to-end.

### Phase 7: Makefile Updates

#### Option A: Keep Single Target

```makefile
publish: clean
	uv build --all-packages
	uvx uv-publish
```

**Note**: This builds and publishes all packages. The script orchestrates the workflow.

#### Option B: Add Separate Targets

```makefile
# Clean build artifacts
clean:
	rm -rf dist/*.whl dist/*.tar.gz

# Build specific packages
build-devclikit:
	uv build --package devclikit

build-workstack:
	uv build --package workstack

# Build all packages
build-all: clean
	uv build --all-packages

# Publish to PyPI (use script for orchestration)
publish:
	uv run workstack-dev publish-to-pypi
```

**Decision Point**: Choose Option B for flexibility, but the script handles the full workflow.

### Phase 8: Testing Updates

#### Update test_publish_to_pypi.py

Add tests for new functionality:

```python
def test_discover_workspace_packages() -> None:
    """Test package discovery finds both packages."""
    # Setup mock workspace
    packages = publish_script.discover_workspace_packages(Path.cwd())

    assert len(packages) == 2
    assert packages[0].name == "devclikit"
    assert packages[1].name == "workstack"

def test_validate_version_consistency_matching() -> None:
    """Test validation passes when versions match."""
    # Setup: Both packages at 0.1.10
    packages = create_test_packages(version="0.1.10")

    version = publish_script.validate_version_consistency(packages)

    assert version == "0.1.10"

def test_validate_version_consistency_mismatch() -> None:
    """Test validation fails when versions don't match."""
    # Setup: devclikit at 0.1.10, workstack at 0.1.11
    packages = create_test_packages_with_versions({
        "devclikit": "0.1.10",
        "workstack": "0.1.11",
    })

    with pytest.raises(SystemExit):
        publish_script.validate_version_consistency(packages)

def test_synchronize_versions() -> None:
    """Test version synchronization updates all packages."""
    # Setup packages
    packages = create_test_packages(version="0.1.10")

    publish_script.synchronize_versions(
        packages,
        old_version="0.1.10",
        new_version="0.1.11",
        dry_run=False,
    )

    # Verify both updated
    for pkg in packages:
        content = pkg.pyproject_path.read_text(encoding="utf-8")
        assert 'version = "0.1.11"' in content
        assert 'version = "0.1.10"' not in content

def test_filter_git_status_excludes_both_pyprojects() -> None:
    """Test git status filtering excludes both pyproject.toml files."""
    status = (
        " M pyproject.toml\n"
        " M packages/devclikit/pyproject.toml\n"
        " M uv.lock\n"
        " M src/other.py"
    )
    excluded = {
        "pyproject.toml",
        "packages/devclikit/pyproject.toml",
        "uv.lock",
    }

    result = publish_script.filter_git_status(status, excluded)

    assert len(result) == 1
    assert " M src/other.py" in result
```

### Phase 9: Error Handling & Recovery

#### Pre-flight Validation

Add validation before any modifications:

```python
def validate_pypi_credentials(dry_run: bool) -> None:
    """Verify PyPI credentials are configured.

    Checks for ~/.pypirc or UV_PUBLISH_TOKEN environment variable.
    """
    if dry_run:
        click.echo("[DRY RUN] Would validate PyPI credentials")
        return

    pypirc = Path.home() / ".pypirc"
    has_token = os.getenv("UV_PUBLISH_TOKEN") is not None

    if not pypirc.exists() and not has_token:
        click.echo("✗ PyPI credentials not configured", err=True)
        click.echo("  Configure ~/.pypirc or set UV_PUBLISH_TOKEN", err=True)
        raise SystemExit(1)
```

#### Failure Recovery Guide

Add to script docstring:

```python
"""Publish workstack and devclikit packages to PyPI.

This script automates the synchronized publishing workflow for both packages.

RECOVERY FROM FAILURES:

1. Pre-build failure (git, version parsing, etc):
   - No changes made, safe to fix issue and retry

2. Build failure:
   - Version bumps made but not committed
   - Run: git checkout -- pyproject.toml packages/devclikit/pyproject.toml uv.lock
   - Fix build issue and retry

3. devclikit publish failure:
   - Version bumps made but not committed
   - Run: git checkout -- pyproject.toml packages/devclikit/pyproject.toml uv.lock
   - Investigate PyPI issue and retry

4. workstack publish failure (devclikit already published):
   - devclikit published to PyPI but workstack failed
   - DO NOT revert version bumps
   - Fix workstack issue and manually publish:
     * cd dist
     * uvx uv-publish workstack-<version>*
   - Then commit and push

5. Git commit/push failure (both packages published):
   - Both packages published successfully
   - Manually commit and push:
     * git add pyproject.toml packages/devclikit/pyproject.toml uv.lock
     * git commit -m "Published <version>"
     * git push
"""
```

## Implementation Sequence

### Step 1: Update Version Management (Low Risk)
- [ ] Add `PackageInfo` dataclass
- [ ] Add `discover_workspace_packages()`
- [ ] Add `validate_version_consistency()`
- [ ] Update `synchronize_versions()` to handle multiple packages
- [ ] Update git status filtering to exclude `packages/devclikit/pyproject.toml`
- [ ] Test with `--dry-run`

**Verification**: Script discovers both packages, validates versions, simulates bumping both.

### Step 2: Update Build Process (Medium Risk)
- [ ] Add `build_package()` function
- [ ] Add `build_all_packages()` function
- [ ] Add `validate_build_artifacts()` function
- [ ] Test building both packages locally
- [ ] Verify artifacts in dist/ directory

**Verification**: Both packages build successfully, all artifacts present.

### Step 3: Update Publishing Process (High Risk - TEST THOROUGHLY)
- [ ] Add `publish_package()` function
- [ ] Add `wait_for_pypi_availability()` function
- [ ] Add `publish_all_packages()` function
- [ ] Update `main()` to use new workflow
- [ ] **TEST WITH --dry-run EXTENSIVELY**
- [ ] Consider test publish to TestPyPI first

**Verification**: Dry-run shows correct sequence, test publish to TestPyPI succeeds.

### Step 4: Update Git Integration (Low Risk)
- [ ] Update `commit_changes()` to include both pyproject.toml files
- [ ] Update commit message to mention both packages
- [ ] Test commit with `--dry-run`

**Verification**: Git commit includes all necessary files.

### Step 5: Testing & Documentation (Low Risk)
- [ ] Add unit tests for new functions
- [ ] Update integration tests
- [ ] Update script docstring with recovery guide
- [ ] Test full workflow with `--dry-run`
- [ ] Review error messages for clarity

**Verification**: All tests pass, error messages are helpful.

### Step 6: First Production Run (High Risk - BE CAREFUL)
- [ ] Review entire workflow one more time
- [ ] Run with `--dry-run` to verify output
- [ ] Run without `--dry-run` to publish
- [ ] Monitor PyPI for both packages
- [ ] Verify versions match
- [ ] Test installing both packages

**Verification**: Both packages on PyPI, installation works, versions match.

## Testing Strategy

### Unit Tests
- Version parsing and bumping
- Package discovery
- Git status filtering with multiple pyproject files
- Build artifact validation

### Integration Tests
- Full workflow in isolated environment
- Failure scenarios with cleanup
- Dry-run mode completeness

### Manual Testing
1. **Dry-run test**: Run with `--dry-run`, verify all output
2. **TestPyPI test**: Modify to publish to TestPyPI first
3. **Version validation**: Ensure both packages have same version
4. **Dependency test**: Install workstack, verify it pulls correct devclikit version
5. **Rollback test**: Manually trigger failures at each step, verify recovery

## Open Questions & Decisions

### Q1: Independent vs Locked Versioning
**Options**:
- A) **Locked versioning** (planned): Both packages always same version
- B) Independent versioning: Each package has own version

**Decision**: Start with locked versioning (simpler). Can add independent versioning later if needed.

### Q2: PyPI Availability Wait Time
**Options**:
- A) Fixed 5-second wait (planned)
- B) Configurable wait time via CLI flag
- C) Active polling with timeout

**Decision**: Start with fixed 5 seconds. Add active polling if issues occur.

### Q3: Dry-Run Build Behavior
**Options**:
- A) **Full dry-run** (planned): Skip builds, just simulate
- B) Build-only dry-run: Build but don't publish
- C) Two modes: `--dry-run` (no builds) and `--build-only` (build but don't publish)

**Decision**: Start with full dry-run (no builds). Consider adding `--build-only` later.

### Q4: Emergency Publishing Options
**Options**:
- A) No emergency options (planned)
- B) Add `--skip-devclikit` flag for workstack-only publish
- C) Add `--packages` flag to select which packages to publish

**Decision**: Start without emergency options. Add if production issues require them.

### Q5: Build Strategy
**Options**:
- A) **Sequential builds** (planned): One after another
- B) Parallel builds: Use `--all-packages` flag

**Decision**: Start with sequential using `--package` for clarity. Can optimize to `--all-packages` later.

### Q6: Publish Tool
**Current**: Uses `uvx uv-publish`

**Investigation needed**: Does `uv-publish` support publishing specific packages from dist/ directory? May need to filter artifacts or run multiple times.

**Proposed solution**:
```python
# Publish each package's artifacts separately
def publish_package(package: PackageInfo, staging_dir: Path, version: str, dry_run: bool) -> None:
    # Filter to only this package's artifacts
    artifacts = list(staging_dir.glob(f"{package.name}-{version}*"))

    # Publish using uv-publish with specific files
    run_command(
        ["uvx", "uv-publish"] + [str(a) for a in artifacts],
        cwd=staging_dir,
        description=f"publish {package.name}",
    )
```

**Decision**: Test `uv-publish` behavior and adjust implementation accordingly.

## Risk Assessment

### Low Risk
- Package discovery (read-only operations)
- Version validation (read-only operations)
- Git status filtering updates (no side effects)
- Dry-run testing (no modifications)

### Medium Risk
- Version bumping both files (reversible with git)
- Building both packages (local operations)
- Commit message updates (cosmetic)

### High Risk
- Publishing to PyPI (irreversible - can't unpublish, only yank)
- Partial publish scenarios (devclikit succeeds, workstack fails)
- PyPI propagation delays (could break workstack install)

### Mitigation Strategies

**High Risk Items**:
1. **Test with TestPyPI first**: Validate entire flow in test environment
2. **Extensive dry-run testing**: Verify output before running
3. **Version validation**: Pre-flight check that versions match
4. **Artifact validation**: Verify all builds before any publish
5. **Dependency order**: Always publish devclikit first
6. **Clear error messages**: Guide recovery at each failure point
7. **Manual recovery procedures**: Document steps for each failure scenario

## Success Criteria

### Must Have
- [ ] Both packages publish with same version number
- [ ] Packages publish in dependency order (devclikit first)
- [ ] Git commit includes both pyproject.toml files
- [ ] Dry-run mode works without making any changes
- [ ] Clear error messages for all failure scenarios
- [ ] Tests pass for new functionality

### Should Have
- [ ] PyPI availability wait time prevents dependency resolution failures
- [ ] Build artifact validation catches missing files before publish
- [ ] Recovery guide helps with manual intervention when needed

### Nice to Have
- [ ] Active PyPI polling instead of fixed wait
- [ ] Rollback automation for failed publishes
- [ ] TestPyPI integration for testing
- [ ] Configurable wait times

## Future Enhancements

### Post-MVP Features
1. **Active PyPI Polling**: Check package availability instead of fixed wait
2. **TestPyPI Integration**: `--test-pypi` flag to publish to test instance
3. **Version Validation**: Ensure workstack's devclikit dependency version matches published version
4. **Selective Publishing**: `--packages` flag to choose which packages to publish
5. **Independent Versioning**: Support different versions for each package
6. **Automatic Yanking**: Roll back PyPI on failure (requires PyPI API integration)
7. **CI/CD Integration**: GitHub Actions workflow for automated publishing
8. **Changelog Generation**: Auto-update CHANGELOG.md with version changes

### Monitoring & Observability
1. **Publish Metrics**: Track publish times, failure rates
2. **Version Drift Detection**: Alert if versions become desynchronized
3. **Dependency Health**: Monitor if published devclikit version matches workstack dependency

## Appendix A: File Changes Summary

### Files to Modify
- `src/workstack/dev_cli/commands/publish_to_pypi/script.py` (major changes)
- `tests/dev_cli/test_publish_to_pypi.py` (add new tests)
- `Makefile` (optional - add convenience targets)

### Files to Create
- None (all changes to existing files)

### Configuration Changes
- None (no config file changes needed)

## Appendix B: Command Examples

### Production Publishing
```bash
# From repo root
uv run workstack-dev publish-to-pypi

# Output:
Discovering workspace packages...
  ✓ Found 2 packages: devclikit, workstack

Starting synchronized publish workflow...

✓ Pulled latest changes
  ✓ Current version: 0.1.10 (consistent)

Bumping version: 0.1.10 → 0.1.11
  ✓ Updated devclikit: 0.1.10 → 0.1.11
  ✓ Updated workstack: 0.1.10 → 0.1.11
✓ Dependencies synced

Building packages...
  ✓ Built devclikit
  ✓ Built workstack
  ✓ All artifacts validated

Publishing to PyPI...
  ✓ Published devclikit 0.1.11
  ⏳ Waiting 5s for PyPI propagation...
  ✓ Published workstack 0.1.11

✓ Committed: a1b2c3d "Published 0.1.11"
✓ Pushed to origin

✅ Successfully published:
  • devclikit 0.1.11
  • workstack 0.1.11
```

### Dry-Run Testing
```bash
# Test workflow without making changes
uv run workstack-dev publish-to-pypi --dry-run

# Output:
[DRY RUN MODE - No changes will be made]

Discovering workspace packages...
  ✓ Found 2 packages: devclikit, workstack

[DRY RUN] Would run: git pull
[DRY RUN] Would update packages/devclikit/pyproject.toml: version = "0.1.10" -> version = "0.1.11"
[DRY RUN] Would update pyproject.toml: version = "0.1.10" -> version = "0.1.11"
[DRY RUN] Would run: uv sync
[DRY RUN] Would run: uv build --package devclikit -o dist
[DRY RUN] Would run: uv build --package workstack -o dist
[DRY RUN] Would validate artifacts exist
[DRY RUN] Would publish devclikit to PyPI
[DRY RUN] Would wait for devclikit 0.1.11 on PyPI
[DRY RUN] Would publish workstack to PyPI
[DRY RUN] Would run: git add packages/devclikit/pyproject.toml pyproject.toml uv.lock
[DRY RUN] Would run: git commit -m "Published 0.1.11..."
[DRY RUN] Would run: git push
```

## Appendix C: Recovery Procedures

### Scenario 1: Build Failure
**Symptoms**: Error during `uv build`

**Recovery**:
```bash
# Revert version changes
git checkout -- pyproject.toml packages/devclikit/pyproject.toml uv.lock

# Fix build issue (e.g., syntax error, missing dependency)
# Then retry
uv run workstack-dev publish-to-pypi
```

### Scenario 2: devclikit Publish Failure
**Symptoms**: Error during `uv-publish` for devclikit

**Recovery**:
```bash
# Revert version changes
git checkout -- pyproject.toml packages/devclikit/pyproject.toml uv.lock

# Investigate PyPI issue (credentials, network, etc)
# Fix and retry
uv run workstack-dev publish-to-pypi
```

### Scenario 3: workstack Publish Failure
**Symptoms**: devclikit published successfully, workstack failed

**State**: devclikit 0.1.11 on PyPI, workstack still at 0.1.10

**Recovery**:
```bash
# DO NOT revert version bumps
# Fix the workstack publish issue

# Manual publish of workstack only
cd dist
uvx uv-publish workstack-0.1.11*

# Verify on PyPI, then commit and push
git add pyproject.toml packages/devclikit/pyproject.toml uv.lock
git commit -m "Published 0.1.11"
git push
```

### Scenario 4: Git Push Failure
**Symptoms**: Both packages published, commit succeeded, push failed

**State**: Both packages at 0.1.11 on PyPI, local commit not pushed

**Recovery**:
```bash
# Retry push
git push

# If still failing, investigate network/remote issues
# Packages are already published, just need to sync git
```

### Scenario 5: Version Mismatch Detected
**Symptoms**: `validate_version_consistency` fails

**Recovery**:
```bash
# Check current versions
grep '^version = ' pyproject.toml
grep '^version = ' packages/devclikit/pyproject.toml

# Manually fix the mismatch to match the lower version
# Then retry publish workflow
```

## Appendix D: Testing Checklist

### Pre-Implementation Testing
- [ ] Review all code changes
- [ ] Run static type checking (`uv run pyright`)
- [ ] Run linter (`uv run ruff check`)
- [ ] Run formatter (`uv run ruff format`)

### Unit Testing
- [ ] Test package discovery
- [ ] Test version consistency validation (matching)
- [ ] Test version consistency validation (mismatched)
- [ ] Test version synchronization
- [ ] Test git status filtering with multiple pyproject files
- [ ] Test build artifact validation
- [ ] All existing tests still pass

### Integration Testing
- [ ] Full dry-run completes without errors
- [ ] Dry-run output is accurate and helpful
- [ ] Version bumping updates both files correctly
- [ ] Build process creates all expected artifacts
- [ ] Git commit includes all necessary files

### Manual Testing (TestPyPI)
- [ ] Modify script to use TestPyPI
- [ ] Run full publish workflow
- [ ] Verify both packages on TestPyPI
- [ ] Install both packages from TestPyPI
- [ ] Verify workstack can import from devclikit
- [ ] Clean up TestPyPI test packages

### Production Validation
- [ ] Final dry-run review
- [ ] Publish to production PyPI
- [ ] Verify both packages visible on PyPI
- [ ] Verify versions match
- [ ] Install both packages: `pip install workstack devclikit`
- [ ] Verify installation works correctly
- [ ] Check git commit and push succeeded

## Timeline Estimate

### Phase 1-2 (Version Management): 2-3 hours
- Implementation: 1 hour
- Testing: 1 hour
- Dry-run validation: 30 min

### Phase 3-4 (Build & Publish): 3-4 hours
- Implementation: 1.5 hours
- Testing: 1 hour
- TestPyPI validation: 1 hour
- Dry-run validation: 30 min

### Phase 5-6 (Git & Workflow): 1-2 hours
- Implementation: 30 min
- Testing: 30 min
- Full workflow dry-run: 30 min

### Phase 7-8 (Makefile & Tests): 2-3 hours
- Test writing: 1.5 hours
- Makefile updates: 30 min
- Test execution: 30 min

### Phase 9 (Error Handling): 1-2 hours
- Implementation: 1 hour
- Documentation: 30 min
- Manual failure testing: 30 min

### Production Deployment: 1-2 hours
- Final review: 30 min
- TestPyPI validation: 30 min
- Production publish: 15 min
- Verification: 15 min
- Buffer for issues: 30 min

**Total Estimate**: 10-16 hours

## Approval & Sign-off

- [ ] Plan reviewed by maintainer
- [ ] Open questions answered
- [ ] Risk mitigation accepted
- [ ] Testing strategy approved
- [ ] Ready for implementation

---

**End of Implementation Plan**
