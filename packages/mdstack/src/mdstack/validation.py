from mdstack.hashing import compute_hash
from mdstack.manifest import load_manifest
from mdstack.models import Scope


class TamperDetectionError(Exception):
    """Raised when manual edits are detected in .mdstack/ directory."""

    pass


def validate_no_tampering(scope: Scope) -> None:
    """
    Verify that generated files match manifest hashes.

    Raises TamperDetectionError if files have been manually edited.
    """
    manifest = load_manifest(scope)

    if not manifest:
        # No manifest = nothing to validate
        return

    # Check TESTS.md
    tests_file = scope.mdstack_dir / "TESTS.md"
    if tests_file.exists():
        tests_content = tests_file.read_text(encoding="utf-8")
        tests_hash = compute_hash(tests_content)

        if tests_hash != manifest.tests_hash:
            raise TamperDetectionError(
                f"TESTS.md has been manually edited in {scope.path}. "
                f"Please revert changes or regenerate with 'mdstack generate'."
            )

    # Check LOOKUP.md
    lookup_file = scope.mdstack_dir / "LOOKUP.md"
    if lookup_file.exists():
        lookup_content = lookup_file.read_text(encoding="utf-8")
        lookup_hash = compute_hash(lookup_content)

        if lookup_hash != manifest.lookup_hash:
            raise TamperDetectionError(
                f"LOOKUP.md has been manually edited in {scope.path}. "
                f"Please revert changes or regenerate with 'mdstack generate'."
            )

    # Check OBSERVED_ARCHITECTURE.md
    architecture_file = scope.mdstack_dir / "OBSERVED_ARCHITECTURE.md"
    if architecture_file.exists():
        architecture_content = architecture_file.read_text(encoding="utf-8")
        architecture_hash = compute_hash(architecture_content)

        if architecture_hash != manifest.architecture_hash:
            raise TamperDetectionError(
                f"OBSERVED_ARCHITECTURE.md has been manually edited in {scope.path}. "
                f"Please revert changes or regenerate with 'mdstack generate'."
            )


def check_all_scopes(scopes: list[Scope]) -> list[tuple[Scope, TamperDetectionError]]:
    """
    Check all scopes for tampering.

    Returns list of (scope, error) tuples for scopes with tampering detected.
    """
    tampered = []

    for scope in scopes:
        try:
            validate_no_tampering(scope)
        except TamperDetectionError as e:
            tampered.append((scope, e))

    return tampered
