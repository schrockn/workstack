"""Package validation to ensure integrity and structure."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from dot_agent_kit.packages.models import Package


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """A validation issue found in a package."""

    severity: Literal["error", "warning"]
    message: str
    file_path: str | None = None


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Result of validating a package."""

    package_name: str
    valid: bool
    issues: tuple[ValidationIssue, ...]

    @property
    def errors(self) -> list[ValidationIssue]:
        """Return only error-level issues."""
        return [issue for issue in self.issues if issue.severity == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        """Return only warning-level issues."""
        return [issue for issue in self.issues if issue.severity == "warning"]


class PackageValidator:
    """Validator for package structure and metadata."""

    def validate_package(self, package: Package) -> ValidationResult:
        """Validate a package's structure and metadata.

        Args:
            package: Package to validate

        Returns:
            ValidationResult with any issues found.
        """
        issues: list[ValidationIssue] = []

        # Check package directory exists
        if not package.path.exists():
            issues.append(
                ValidationIssue(
                    severity="error",
                    message=f"Package directory does not exist: {package.path}",
                )
            )
            return ValidationResult(
                package_name=package.name,
                valid=False,
                issues=tuple(issues),
            )

        # Check package has files
        if not package.files:
            issues.append(
                ValidationIssue(
                    severity="warning",
                    message="Package contains no files",
                )
            )

        # Package is valid if there are no errors
        has_errors = any(issue.severity == "error" for issue in issues)

        return ValidationResult(
            package_name=package.name,
            valid=not has_errors,
            issues=tuple(issues),
        )

    def validate_namespace_structure(self, packages_dir: Path) -> list[ValidationIssue]:
        """Validate the namespace directory structure.

        Args:
            packages_dir: Path to the packages directory

        Returns:
            List of validation issues found.
        """
        issues: list[ValidationIssue] = []

        if not packages_dir.exists():
            return issues

        # Check for conflicting package names
        seen_names: set[str] = set()
        for item in packages_dir.rglob("*"):
            if not item.is_dir():
                continue

            # Get relative path from packages_dir
            relative = item.relative_to(packages_dir)
            parts = relative.parts

            if len(parts) == 1:
                # Root-level package
                name = parts[0]
            elif len(parts) == 2:
                # Namespaced package
                name = f"{parts[0]}/{parts[1]}"
            else:
                # Too deep - warn about it
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        message=f"Unexpected nesting depth: {relative}",
                    )
                )
                continue

            if name in seen_names:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        message=f"Duplicate package name: {name}",
                    )
                )
            seen_names.add(name)

        return issues
