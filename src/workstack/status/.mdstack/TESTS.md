# Tests

## Child Packages

- **collectors**: No test files found in this scope
- **models**: No test files found in this scope
- **renderers**: No test files found in this scope

## Tests in This Scope

No test files found in the `/workstack/status` scope.

## Related Tests

No related test files were identified in a separate `tests/` directory for this scope.

## Testing Gaps

The status command implementation currently lacks test coverage. The following areas would benefit from test files:

### StatusOrchestrator (orchestrator.py)
- Parallel collector execution and timeout handling
- Error boundary behavior when collectors fail or timeout
- Worktree information collection and resolution
- Related worktrees discovery and filtering
- Result aggregation from multiple collectors
- Type validation of collector results

### Status Collectors (collectors/)
- Availability checking logic for each collector type
- Data collection from git, GitHub, Graphite, and filesystem sources
- Graceful degradation when data sources are unavailable
- Fallback mechanisms (e.g., GitHub PR collector fallback from Graphite to GitHub API)
- Error handling and None returns on collection failures

### Status Models (models/)
- Data model instantiation and immutability
- Optional field handling
- Model composition and hierarchical structure

### Status Renderers (renderers/)
- Console output formatting and styling
- Section-based rendering for each status component
- Null-checking and defensive rendering
- Color and styling application via Click library
- File list truncation and display limits