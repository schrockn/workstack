# pytest-runner

Cost-optimized agent for executing pytest test suites.

## Purpose

Execute pytest commands and parse test results. Uses Haiku model for cost efficiency.

## Usage

Invoke this agent when you need to run pytest tests. The agent will:
- Execute the pytest command
- Parse test results
- Return structured output

## Example Invocation

```
Run pytest in the current directory with verbose output
```

## Implementation

This agent uses the Bash tool to execute pytest commands and captures output for analysis.
