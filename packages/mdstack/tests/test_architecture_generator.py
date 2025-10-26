import tempfile
from pathlib import Path
from typing import Any

from mdstack.discovery import discover_scopes
from mdstack.generators.architecture import ArchitectureGenerator
from mdstack.llm.client import LLMClient, LLMResponse


class FakeLLMClient(LLMClient):
    """Fake LLM client that returns canned responses."""

    def __init__(self):
        self.last_prompt = None
        self.last_input_files = None

    def generate(
        self,
        prompt: str,
        max_tokens: int = 4000,
        context: str | None = None,
        input_files: list[str] | None = None,
        verbose: bool = False,
        system_blocks: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        """Capture the prompt and input files, return fake response."""
        self.last_prompt = prompt
        self.last_input_files = input_files or []
        return LLMResponse(
            content="# Observed Architecture\n\nFake architecture doc\n",
            tokens_used=150,
            input_tokens=100,
            output_tokens=50,
            model="fake-model",
            cost_estimate=0.001,
        )

    def get_model_name(self) -> str:
        """Return fake model name."""
        return "fake-model"


def test_find_subpackages_only_includes_one_level():
    """Should only include Python files from immediate subdirectories, not recursively."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # Create a scope with nested subdirectories
        (root / "CLAUDE.md").touch()

        # Create top-level Python files
        (root / "module1.py").write_text("# module1", encoding="utf-8")
        (root / "module2.py").write_text("# module2", encoding="utf-8")

        # Create immediate subdirectory with Python files
        (root / "subpkg").mkdir()
        (root / "subpkg" / "sub1.py").write_text("# sub1", encoding="utf-8")
        (root / "subpkg" / "sub2.py").write_text("# sub2", encoding="utf-8")

        # Create nested subdirectory (should NOT be included)
        (root / "subpkg" / "nested").mkdir()
        (root / "subpkg" / "nested" / "deep1.py").write_text("# deep1", encoding="utf-8")
        (root / "subpkg" / "nested" / "deep2.py").write_text("# deep2", encoding="utf-8")

        # Create another immediate subdirectory
        (root / "another").mkdir()
        (root / "another" / "another1.py").write_text("# another1", encoding="utf-8")

        # Discover scopes
        scopes = discover_scopes(root)
        scope = next(s for s in scopes if s.path == root)

        # Create generator and run
        fake_llm = FakeLLMClient()
        generator = ArchitectureGenerator(fake_llm, verbose=False)

        # Find subpackages
        subpackages = generator._find_subpackages(scope)

        # Should have exactly 2 subpackages (subpkg and another)
        assert len(subpackages) == 2
        assert root / "subpkg" in subpackages
        assert root / "another" in subpackages

        # subpkg should only have immediate files (sub1.py, sub2.py)
        subpkg_files = subpackages[root / "subpkg"]
        assert len(subpkg_files) == 2
        assert root / "subpkg" / "sub1.py" in subpkg_files
        assert root / "subpkg" / "sub2.py" in subpkg_files

        # Should NOT include nested files
        assert root / "subpkg" / "nested" / "deep1.py" not in subpkg_files
        assert root / "subpkg" / "nested" / "deep2.py" not in subpkg_files

        # another should only have immediate files
        another_files = subpackages[root / "another"]
        assert len(another_files) == 1
        assert root / "another" / "another1.py" in another_files


def test_architecture_generation_does_not_include_nested_subpackage_files():
    """Generated architecture should not include files from nested subdirectories.

    This test verifies that subdirectory Python files are NOT included in input_files,
    since they're only listed by name in the prompt (not read as full content).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # Create a fake git repository
        (root / ".git").mkdir()

        # Create a scope with nested subdirectories
        (root / "CLAUDE.md").write_text("# Test Scope\n\nTest documentation", encoding="utf-8")

        # Create top-level Python files
        (root / "module1.py").write_text("# module1", encoding="utf-8")

        # Create immediate subdirectory with Python files
        (root / "subpkg").mkdir()
        (root / "subpkg" / "sub1.py").write_text("# sub1", encoding="utf-8")

        # Create nested subdirectory (should NOT be included in input_files)
        (root / "subpkg" / "nested").mkdir()
        (root / "subpkg" / "nested" / "deep1.py").write_text("# deep1", encoding="utf-8")

        # Discover scopes
        scopes = discover_scopes(root)
        scope = next(s for s in scopes if s.path == root)

        # Create generator and run generation
        fake_llm = FakeLLMClient()
        generator = ArchitectureGenerator(fake_llm, verbose=False)
        _ = generator.generate(scope, all_scopes=scopes)

        # Check that input_files were tracked correctly
        assert fake_llm.last_input_files is not None

        # Should include CLAUDE.md and top-level Python files only
        assert "CLAUDE.md" in fake_llm.last_input_files
        assert "module1.py" in fake_llm.last_input_files

        # Should NOT include subpackage files (even immediate ones)
        # because they're only listed by name, not read into the prompt
        assert "subpkg/sub1.py" not in fake_llm.last_input_files

        # Should NOT include nested subpackage files
        nested_files = [f for f in fake_llm.last_input_files if "nested" in f]
        assert len(nested_files) == 0, f"Found nested files in input: {nested_files}"

        # Should NOT include deep1.py
        assert "subpkg/nested/deep1.py" not in fake_llm.last_input_files
        assert "deep1.py" not in fake_llm.last_input_files

        # Verify the subpackage was still detected
        subpackages = generator._find_subpackages(scope)
        assert root / "subpkg" in subpackages


def test_input_files_logging_does_not_list_subpackage_files():
    """The input_files list for logging should NOT include subpackage Python files.

    When generating architecture docs for a scope with subdirectories containing Python files,
    the input_files list (used for logging) should only include:
    - CLAUDE.md
    - Top-level Python files in the scope directory
    - Child scope OBSERVED_ARCHITECTURE.md files

    It should NOT include the individual Python files from subdirectories, since those
    are only listed by name (not read into the prompt).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # Create a fake git repository
        (root / ".git").mkdir()

        # Create a scope with subdirectories
        (root / "CLAUDE.md").write_text("# Test Scope\n\nTest documentation", encoding="utf-8")

        # Create top-level Python files (should be in input_files)
        (root / "module1.py").write_text("# module1", encoding="utf-8")
        (root / "module2.py").write_text("# module2", encoding="utf-8")

        # Create subdirectories with Python files (should NOT be in input_files)
        (root / "generators").mkdir()
        (root / "generators" / "gen1.py").write_text("# gen1", encoding="utf-8")
        (root / "generators" / "gen2.py").write_text("# gen2", encoding="utf-8")

        (root / "llm").mkdir()
        (root / "llm" / "client.py").write_text("# client", encoding="utf-8")

        # Discover scopes
        scopes = discover_scopes(root)
        scope = next(s for s in scopes if s.path == root)

        # Create generator and run generation
        fake_llm = FakeLLMClient()
        generator = ArchitectureGenerator(fake_llm, verbose=False)
        _ = generator.generate(scope, all_scopes=scopes)

        # Check input_files list
        assert fake_llm.last_input_files is not None

        # Should include CLAUDE.md and top-level Python files
        assert "CLAUDE.md" in fake_llm.last_input_files
        assert "module1.py" in fake_llm.last_input_files
        assert "module2.py" in fake_llm.last_input_files

        # Should NOT include subpackage Python files
        assert "generators/gen1.py" not in fake_llm.last_input_files
        assert "generators/gen2.py" not in fake_llm.last_input_files
        assert "llm/client.py" not in fake_llm.last_input_files

        # Total files should be only: CLAUDE.md + 2 top-level Python files = 3
        assert len(fake_llm.last_input_files) == 3, (
            f"Expected 3 input files, got {len(fake_llm.last_input_files)}: "
            f"{fake_llm.last_input_files}"
        )
