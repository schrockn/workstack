#!/usr/bin/env python3
# /// script
# dependencies = [
#   "click>=8.1.7",
# ]
# requires-python = ">=3.13"
# ///
"""Generate shell completion scripts for workstack-dev."""

# pyright: reportMissingImports=false

import os
import shutil
import subprocess
import sys


def main() -> None:
    """Generate completion script for the specified shell."""
    if len(sys.argv) != 2:
        print("Usage: script.py [bash|zsh|fish]", file=sys.stderr)
        raise SystemExit(1)

    shell = sys.argv[1]
    if shell not in ("bash", "zsh", "fish"):
        print(f"Error: Unknown shell '{shell}'", file=sys.stderr)
        print("Supported shells: bash, zsh, fish", file=sys.stderr)
        raise SystemExit(1)

    # Find workstack-dev executable
    workstack_dev = shutil.which("workstack-dev")
    if workstack_dev is None:
        # Fallback to running via python module
        cmd = [sys.executable, "-m", "workstack.dev_cli.__main__"]
    else:
        cmd = [workstack_dev]

    # Set environment variable to trigger completion generation
    env = os.environ.copy()
    env["_WORKSTACK_DEV_COMPLETE"] = f"{shell}_source"

    # Run workstack-dev with completion environment variable
    # Use check=False and manually check return code (LBYL pattern)
    result = subprocess.run(
        cmd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    # Output the completion script to stdout
    sys.stdout.write(result.stdout)

    # Forward any errors to stderr
    if result.stderr:
        sys.stderr.write(result.stderr)

    # Exit with the subprocess return code
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
