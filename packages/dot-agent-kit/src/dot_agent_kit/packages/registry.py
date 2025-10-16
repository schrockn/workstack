"""Tool registry for CLI command → package mapping."""

import re
from dataclasses import dataclass
from pathlib import Path

from dot_agent_kit.packages.manager import PackageManager
from dot_agent_kit.packages.models import Package


@dataclass(frozen=True, slots=True)
class ToolInfo:
    """Information about a tool package."""

    package_name: str
    cli_command: str


@dataclass(frozen=True, slots=True)
class ToolContext:
    """Context for a specific tool."""

    tool_name: str
    package: Package
    files: list[str]


class ToolRegistry:
    """Registry for mapping CLI commands to tool packages."""

    def __init__(self, agent_dir: Path):
        """Initialize the tool registry.

        Args:
            agent_dir: Path to the .agent directory
        """
        self.agent_dir = agent_dir
        self.manager = PackageManager(agent_dir)
        self._tool_mappings: dict[str, str] = {}
        self._refresh_mappings()

    def _refresh_mappings(self) -> None:
        """Refresh the CLI command → package name mappings.

        Uses convention-based discovery: tools/{name}/ maps to CLI command {name}.
        """
        self._tool_mappings.clear()

        packages = self.manager.discover_packages()
        for pkg_name, package in packages.items():
            # Only map packages in the tools/ namespace
            if package.namespace != "tools":
                continue

            # Convention: directory name = CLI command
            cli_command = package.package_name
            self._tool_mappings[cli_command] = pkg_name

    def register_cli_mapping(self, cli_name: str, package_name: str) -> None:
        """Register a CLI command to package mapping.

        Args:
            cli_name: CLI command name (e.g., "gt")
            package_name: Full package name (e.g., "tools/gt")
        """
        self._tool_mappings[cli_name] = package_name

    def detect_tool_mention(self, text: str) -> list[str]:
        """Detect CLI tool references in text.

        Args:
            text: Input text to scan for tool mentions

        Returns:
            List of detected tool names (CLI commands).
        """
        detected: set[str] = set()

        # Check for exact command matches
        for cli_name in self._tool_mappings:
            # Match CLI name as a word boundary
            pattern = rf"\b{re.escape(cli_name)}\b"
            if re.search(pattern, text, re.IGNORECASE):
                detected.add(cli_name)

        return sorted(detected)

    def get_tool_context(self, tool_name: str) -> ToolContext | None:
        """Retrieve context for a specific tool.

        Args:
            tool_name: CLI command name (e.g., "gt")

        Returns:
            ToolContext or None if tool not found.
        """
        package_name = self._tool_mappings.get(tool_name)
        if package_name is None:
            return None

        packages = self.manager.discover_packages()
        package = packages.get(package_name)
        if package is None:
            return None

        files = sorted(package.files.keys())

        return ToolContext(
            tool_name=tool_name,
            package=package,
            files=files,
        )

    def list_available_tools(self) -> list[ToolInfo]:
        """List all available tool packages.

        Returns:
            List of ToolInfo for each tool package.
        """
        tools: list[ToolInfo] = []

        packages = self.manager.discover_packages()
        for pkg_name, package in packages.items():
            # Only list packages in the tools/ namespace
            if package.namespace != "tools":
                continue

            # Convention: directory name = CLI command
            cli_command = package.package_name
            tools.append(
                ToolInfo(
                    package_name=pkg_name,
                    cli_command=cli_command,
                )
            )

        return sorted(tools, key=lambda t: t.cli_command)
