# Observed Architecture

## Overview

The `renderers` scope provides a pluggable rendering system for displaying status information to users. It abstracts the presentation layer from status data models, allowing different output formats to be implemented independently. Currently, it provides a single `SimpleRenderer` implementation that formats status data as colored terminal output using the Click library.

## Module Organization

### simple.py
**Responsibility**: Implements the primary text-based status renderer that converts structured status data into formatted console output with colors and styling.

**Key exports**: `SimpleRenderer` class

### __init__.py
**Responsibility**: Package initialization that exposes the public API for the renderers module.

**Key exports**: `SimpleRenderer`

## Core Abstractions

### SimpleRenderer
**Location**: simple.py (scope-relative)

**Purpose**: Renders `StatusData` objects as formatted, colored terminal output. Provides a complete visual representation of worktree status including git state, PR information, stack position, and related worktrees.

**Type**: Concrete class (not abstract, but designed as an extensible renderer implementation)

**Key characteristics**:
- Single public method: `render(status: StatusData) -> None`
- Organized into private rendering methods for each status section
- Uses Click library for terminal styling and output
- Implements a hierarchical rendering pattern with section-specific methods

## Architectural Patterns

### Renderer Pattern
The `SimpleRenderer` follows a **renderer/presenter pattern** where:
- Input: Structured `StatusData` objects (from `workstack.status.models.status_data`)
- Processing: Decomposed into focused rendering methods for each logical section
- Output: Formatted text written directly to console via Click

### Section-Based Rendering
The renderer breaks down status display into logical sections, each with a dedicated private method:
- `_render_header()` - Worktree name, location, and branch
- `_render_plan()` - Plan file content preview
- `_render_stack()` - Graphite stack position and visualization
- `_render_pr_status()` - Pull request information
- `_render_git_status()` - Git working tree state
- `_render_related_worktrees()` - Other worktrees in the same repository

### Utility Methods
- `_render_file_list()` - Reusable helper for displaying file lists with truncation

### Styling Conventions
Consistent use of Click styling throughout:
- **Colors**: green (success/root), red (errors/detached), yellow (warnings/branches), cyan (secondary info), blue (section headers), magenta (special sections)
- **Emphasis**: bold for headers and important states, dim for supplementary info
- **Symbols**: ◉ for current branch, ◯ for other branches in stack

## Data Flow

1. **Input**: `StatusData` object containing all status information
2. **Processing**: `render()` method orchestrates section rendering in order
3. **Section Rendering**: Each `_render_*()` method:
   - Checks if data exists (defensive null checks)
   - Extracts relevant fields from status object
   - Formats with appropriate styling
   - Writes to console via `click.echo()`
4. **Output**: Formatted text appears in terminal with colors and structure

## Dependencies

### External Dependencies
- **click**: Terminal styling and output (`click.echo()`, `click.style()`)

### Internal Dependencies
- **workstack.status.models.status_data**: `StatusData` class (input data model)

## Extension Points

### Adding New Renderers
To create alternative renderers (e.g., JSON, HTML, Markdown):
1. Create a new module in this scope (e.g., `json_renderer.py`)
2. Implement a class with a `render(status: StatusData) -> None` method
3. Export from `__init__.py`
4. Follow the same input contract: accept `StatusData` objects

### Modifying Rendering Output
To change how sections are displayed:
- Edit the corresponding `_render_*()` method in `SimpleRenderer`
- Adjust styling via Click color/style parameters
- Modify truncation limits (e.g., `max_files` parameter in `_render_file_list()`)

### Adding New Status Sections
If `StatusData` is extended with new fields:
1. Add a new `_render_new_section()` method to `SimpleRenderer`
2. Call it from the `render()` method in appropriate order
3. Follow existing patterns for null-checking and styling

## Key Concepts Explained

### StatusData
The input contract for renderers. Contains all information about a worktree's current state, including git status, PR information, stack position, and related worktrees. Renderers should be defensive about missing fields (many are optional).

### Worktree
A Git worktree concept - a separate working directory linked to the same repository. The renderer displays information about the current worktree and lists related ones.

### Stack Position (Graphite)
Represents a branch's position in a Graphite stack - a linear chain of dependent branches. The renderer visualizes this hierarchy with parent/child relationships and a visual stack diagram.

### Section-Based Output
The renderer organizes output into logical sections (header, plan, stack, PR, git status, related worktrees) rather than a flat list, making the output scannable and hierarchical.

## Common Agent Tasks

### Modifying Styling or Colors
- Locate the relevant `_render_*()` method
- Adjust `click.style()` calls with different `fg=` (foreground color) or `bold=True`/`dim=True` parameters
- Test by running the renderer with sample `StatusData`

### Adding a New Status Field Display
- Identify which section the field belongs to
- Add display logic to the corresponding `_render_*()` method
- Include null-checking: `if status.field_name is None: return`
- Follow existing styling patterns for consistency

### Creating an Alternative Renderer
- Create new file in this scope (e.g., `markdown_renderer.py`)
- Implement class with `render(status: StatusData) -> None` method
- Use same section-based approach or alternative structure
- Export from `__init__.py`
- No need to modify `SimpleRenderer` - renderers are independent

### Debugging Output Issues
- Check if `StatusData` object has the expected fields populated
- Verify null-checks in `_render_*()` methods (sections silently skip if data missing)
- Test individual `_render_*()` methods with sample data
- Adjust `click.echo()` calls or styling parameters