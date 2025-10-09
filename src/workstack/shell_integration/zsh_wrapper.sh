# Workstack shell integration for zsh
# This function wraps the workstack CLI to provide seamless worktree switching

workstack() {
  # Don't intercept if we're doing shell completion
  [ -n "$_WORKSTACK_COMPLETE" ] && { command workstack "$@"; return; }

  local output exit_status
  output=$(command workstack __shell "$@")
  exit_status=$?

  # Passthrough mode: run the original command directly
  [ "$output" = "__WORKSTACK_PASSTHROUGH__" ] && { command workstack "$@"; return; }

  # If __shell returned non-zero, error messages are already sent to stderr
  [ $exit_status -ne 0 ] && return $exit_status

  # Execute the shell script output (eval handles empty strings safely)
  eval "$output"
}
