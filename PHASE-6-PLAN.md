# Phase 6: Embedded Kits and Advanced Features - Implementation Plan

## Overview

Phase 6 extends dot-agent to support kits embedded within larger Python packages, enabling:

- Multiple kits per package
- Kits as optional features of tools
- Entry point discovery
- Resource-based artifact loading

## Key Components

### 1. Abstract Base Class for Sources

**File: `src/dot_agent/sources/base.py`**

```python
from abc import ABC, abstractmethod
from pathlib import Path
from dot_agent.models.kit import KitManifest

class KitSourceOps(ABC):
    """Abstract base class for kit sources."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the source is available."""
        ...

    @abstractmethod
    def get_manifest(self) -> KitManifest | None:
        """Get the kit manifest from the source."""
        ...

    @abstractmethod
    def get_artifact_content(self, source_path: str) -> bytes | None:
        """Get artifact content from the source."""
        ...

    @abstractmethod
    def list_kits(self) -> list[str]:
        """List available kits from this source."""
        ...
```

### 2. Embedded Source Implementation

**File: `src/dot_agent/sources/embedded.py`**

Key features:

- Discover kits via Python entry points
- Load manifests from package resources
- Support multiple kits per package
- Use `importlib.resources` for artifact access

```python
class EmbeddedSource(KitSourceOps):
    def __init__(self, package_name: str, kit_id: str | None = None):
        # Support discovering specific kit or all kits in package
        ...
```

### 3. Entry Point Configuration

Packages expose kits via `pyproject.toml`:

```toml
[project.entry-points."dot_agent.kits"]
graphite = "gt_tool.kits:graphite_kit"
advanced-graphite = "gt_tool.kits:advanced_kit"
```

### 4. Enhanced Resolver

Update `src/dot_agent/sources/resolver.py`:

```python
def resolve_from_embedded(self, package_name: str, kit_id: str | None) -> EmbeddedSource | None:
    """Resolve an embedded kit source."""
    source = EmbeddedSource(package_name, kit_id)
    if source.is_available():
        return source
    return None

def list_embedded_kits(self, package_name: str) -> list[str]:
    """List all embedded kits in a package."""
    source = EmbeddedSource(package_name)
    return source.list_kits()
```

### 5. Enhanced Commands

#### List Command (new)

**File: `src/dot_agent/commands/list.py`**

```python
@click.command()
@click.option("--package", help="List kits from specific package")
@click.option("--all", is_flag=True, help="List from all installed packages")
def list(package: str | None, all: bool) -> None:
    """List available embedded kits."""
    ...
```

#### Enhanced Init Command

Add support for embedded kits:

```python
@click.option("--embedded", help="Package:kit_id for embedded kit")
def init(..., embedded: str | None) -> None:
    if embedded:
        package, _, kit_id = embedded.partition(":")
        source = resolver.resolve_from_embedded(package, kit_id or None)
```

### 6. Resource Management

**File: `src/dot_agent/utils/resources.py`**

```python
import importlib.resources as resources
from pathlib import Path

def read_package_resource(package: str, resource_path: str) -> bytes | None:
    """Read a resource from a Python package."""
    try:
        # Python 3.13+ approach
        files = resources.files(package)
        resource = files.joinpath(resource_path)
        return resource.read_bytes()
    except Exception:
        return None

def list_package_resources(package: str, prefix: str) -> list[str]:
    """List resources in a package with given prefix."""
    ...
```

### 7. Package Structure for Embedded Kits

Example package with embedded kits:

```
my-tool/
├── pyproject.toml
├── src/
│   └── my_tool/
│       ├── __init__.py
│       ├── cli.py           # Main tool CLI
│       └── kits/
│           ├── __init__.py
│           ├── basic/       # Basic kit
│           │   ├── kit.yaml
│           │   └── commands/
│           │       └── basic.md
│           └── advanced/    # Advanced kit
│               ├── kit.yaml
│               └── commands/
│                   └── advanced.md
```

### 8. Conflict Resolution

Enhanced conflict handling for multiple kits:

**File: `src/dot_agent/operations/merge.py`**

```python
def merge_artifacts(
    existing: str,
    new: str,
    artifact_type: str
) -> str:
    """Merge two artifact files intelligently."""
    if artifact_type == "command":
        # Merge command definitions
        return merge_markdown_sections(existing, new)
    elif artifact_type == "skill":
        # Append skills
        return f"{existing}\n\n{new}"
    else:
        # Default: replace
        return new
```

### 9. Discovery Command (new)

**File: `src/dot_agent/commands/discover.py`**

```python
@click.command()
@click.option("--json", is_flag=True, help="Output as JSON")
def discover(json: bool) -> None:
    """Discover all available kits in installed packages."""
    # Scan all installed packages for dot_agent.kits entry points
    ...
```

## Implementation Steps

### Step 1: Refactor Existing Sources

1. Create abstract base class `KitSourceOps`
2. Update `StandaloneSource` to inherit from base
3. Add `list_kits()` method to standalone source

### Step 2: Implement Embedded Source

1. Create `EmbeddedSource` class
2. Implement entry point discovery
3. Add resource loading via `importlib.resources`
4. Support kit enumeration

### Step 3: Enhance Commands

1. Add `--embedded` option to init command
2. Create new `list` command
3. Create new `discover` command
4. Update `check` to handle embedded kits

### Step 4: Add Resource Utilities

1. Create resource reading utilities
2. Add resource listing functions
3. Handle package structure variations

### Step 5: Implement Merge Operations

1. Create merge strategies for different artifact types
2. Add merge policy to config
3. Implement intelligent markdown merging

### Step 6: Update Models

1. Add `source_info` field to `InstalledKit`
2. Support embedded source type
3. Add merge policy to `ConflictPolicy` enum

### Step 7: Testing

1. Create fixtures for embedded packages
2. Test entry point discovery
3. Test resource loading
4. Test multiple kit scenarios

## Testing Strategy

### Unit Tests

**File: `tests/test_embedded.py`**

```python
def test_discover_embedded_kits():
    """Test discovering kits via entry points."""

def test_load_embedded_manifest():
    """Test loading manifest from package resources."""

def test_install_embedded_kit():
    """Test installing an embedded kit."""

def test_multiple_kits_per_package():
    """Test package with multiple embedded kits."""
```

### Integration Tests

**File: `tests/test_integration_embedded.py`**

```python
def test_full_embedded_workflow():
    """Test discover → list → install → check → sync workflow."""

def test_embedded_with_standalone():
    """Test mixing embedded and standalone kits."""
```

## Configuration Changes

### Updated dot-agent.toml

```toml
[kits.my-tool-basic]
kit_id = "my-tool-basic"
package_name = "my-tool"
version = "2.0.0"
artifacts = ["commands/basic.md"]
install_date = "2024-01-01T00:00:00"
source_type = "embedded"
source_info = { kit_path = "basic" }
```

### New Registry Entry Format

```yaml
- name: my-tool-kits
  url: https://github.com/example/my-tool
  description: Collection of kits for my-tool
  package_name: my-tool
  embedded: true
  kits:
    - basic
    - advanced
```

## CLI Examples

```bash
# Discover all available embedded kits
dot-agent discover

# List kits in specific package
dot-agent list --package my-tool

# Install specific embedded kit
dot-agent init --embedded my-tool:basic

# Install all kits from package
dot-agent init --embedded my-tool

# Check including embedded kits
dot-agent check --include-embedded
```

## Benefits

1. **Reduced Package Sprawl**: Tools can bundle related kits
2. **Optional Features**: Users choose which kits to activate
3. **Better Organization**: Related kits stay together
4. **Version Synchronization**: Kits update with main tool
5. **Resource Efficiency**: Share common dependencies

## Challenges & Solutions

### Challenge 1: Entry Point Discovery

**Solution**: Cache discovered entry points for performance

### Challenge 2: Resource Access

**Solution**: Use `importlib.resources` with fallback strategies

### Challenge 3: Version Management

**Solution**: Track both package version and kit version

### Challenge 4: Conflict Resolution

**Solution**: Implement intelligent merge strategies

## Success Criteria

- [ ] Can discover embedded kits via entry points
- [ ] Can install individual embedded kits
- [ ] Can list all kits in a package
- [ ] Resource loading works reliably
- [ ] Tests pass with >90% coverage
- [ ] Documentation updated with examples
- [ ] Backward compatibility maintained

## Future Extensions

1. **Kit Dependencies**: Kits can depend on other kits
2. **Conditional Activation**: Enable kits based on environment
3. **Kit Composition**: Combine multiple kits into profiles
4. **Dynamic Loading**: Load kits without installation
5. **Kit Marketplace**: Central registry with ratings/reviews
