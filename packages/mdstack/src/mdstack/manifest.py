import json

from mdstack.models import Manifest, Scope

MANIFEST_FILENAME = ".manifest.json"


def load_manifest(scope: Scope) -> Manifest | None:
    """Load manifest from scope's .mdstack/ directory."""
    manifest_path = scope.mdstack_dir / MANIFEST_FILENAME

    if not manifest_path.exists():
        return None

    data = json.loads(manifest_path.read_text(encoding="utf-8"))

    # Backward compatibility: add architecture_hash if missing
    if "architecture_hash" not in data:
        data["architecture_hash"] = ""

    return Manifest(**data)


def save_manifest(scope: Scope, manifest: Manifest) -> None:
    """Save manifest to scope's .mdstack/ directory."""
    scope.mdstack_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = scope.mdstack_dir / MANIFEST_FILENAME

    data = {
        "content_hash": manifest.content_hash,
        "generated_at": manifest.generated_at,
        "llm_provider": manifest.llm_provider,
        "llm_model": manifest.llm_model,
        "generator_version": manifest.generator_version,
        "tests_hash": manifest.tests_hash,
        "lookup_hash": manifest.lookup_hash,
        "architecture_hash": manifest.architecture_hash,
    }

    manifest_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def is_stale(scope: Scope) -> bool:
    """
    Check if scope's documentation needs regeneration.

    A scope is stale if:
    - No manifest exists
    - Generated files are missing
    - Files don't match manifest hashes (tamper detection handled separately)
    """
    manifest = load_manifest(scope)

    if not manifest:
        # No manifest = needs generation
        return True

    # Check if generated files exist
    required_files = ["TESTS.md", "LOOKUP.md", "OBSERVED_ARCHITECTURE.md"]
    for filename in required_files:
        if not (scope.mdstack_dir / filename).exists():
            return True

    return False
