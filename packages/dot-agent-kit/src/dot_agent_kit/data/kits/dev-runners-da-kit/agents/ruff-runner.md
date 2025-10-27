# ruff-runner

Cost-optimized agent for executing ruff linting and formatting.

## Purpose

Execute ruff commands for code linting and formatting. Uses Haiku model for cost efficiency.

## Usage

Invoke this agent when you need to:

- Run ruff check for linting
- Run ruff format for code formatting
- Apply automatic fixes

## Example Invocation

```
Run ruff check with --fix on the current directory
```

## Implementation

This agent uses the Bash tool to execute ruff commands and captures output for analysis.
