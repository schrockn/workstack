from pathlib import Path

from mdstack.models import Scope


def discover_scopes(root: Path | None = None) -> list[Scope]:
    """
    Find all CLAUDE.md files and build Scope hierarchy.

    Returns scopes in dependency order (parents before children).
    """
    if root is None:
        root = Path.cwd()

    # Find all CLAUDE.md files
    claude_files = sorted(root.rglob("CLAUDE.md"))

    # Build scopes without parents first
    scopes = []
    scope_map = {}  # path -> Scope

    for claude_md_path in claude_files:
        scope_path = claude_md_path.parent
        mdstack_dir = scope_path / ".mdstack"

        scope = Scope.create(
            path=scope_path, claude_md_path=claude_md_path, mdstack_dir=mdstack_dir
        )

        scopes.append(scope)
        scope_map[scope_path] = scope

    # Second pass: set parent relationships
    scopes_with_parents = []
    for scope in scopes:
        parent_scope = find_parent_scope(scope, scope_map)

        # Create new instance with parent (frozen dataclass)
        scope_with_parent = Scope.create(
            path=scope.path,
            claude_md_path=scope.claude_md_path,
            mdstack_dir=scope.mdstack_dir,
            parent_scope=parent_scope,
        )
        scopes_with_parents.append(scope_with_parent)

    return scopes_with_parents


def find_parent_scope(scope: Scope, scope_map: dict[Path, Scope]) -> Scope | None:
    """Find the nearest parent directory with CLAUDE.md."""
    current = scope.path.parent

    while current != current.parent:  # Stop at filesystem root
        if current in scope_map:
            return scope_map[current]
        current = current.parent

    return None


def find_scope_by_path(path: Path, scopes: list[Scope]) -> Scope | None:
    """Find scope containing the given path."""
    path = path.resolve()

    # Find most specific scope (longest path match)
    best_match = None
    best_match_depth = -1

    for scope in scopes:
        scope_path = scope.path.resolve()

        try:
            # Check if path is relative to scope
            path.relative_to(scope_path)

            depth = len(scope_path.parts)
            if depth > best_match_depth:
                best_match = scope
                best_match_depth = depth
        except ValueError:
            # path not relative to scope_path
            continue

    return best_match


def find_child_scopes(parent_scope: Scope, all_scopes: list[Scope]) -> list[Scope]:
    """Find all direct child scopes of a given parent scope."""
    children = []
    for scope in all_scopes:
        if scope.parent_scope and scope.parent_scope.path == parent_scope.path:
            children.append(scope)
    return children


def find_scope_and_descendants(target_scope: Scope, all_scopes: list[Scope]) -> list[Scope]:
    """
    Find target scope and all descendant scopes under it.

    Returns a list containing the target scope and all scopes whose paths
    are under the target scope's path in the directory tree.
    """
    target_path = target_scope.path.resolve()
    result = []

    for scope in all_scopes:
        scope_path = scope.path.resolve()

        # Include the target scope itself
        if scope_path == target_path:
            result.append(scope)
            continue

        # Include scopes under the target path
        try:
            scope_path.relative_to(target_path)
            result.append(scope)
        except ValueError:
            # scope_path is not under target_path
            continue

    return result
