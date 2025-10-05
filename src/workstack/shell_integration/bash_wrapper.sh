# Workstack shell integration for bash
# This function wraps the workstack CLI to provide seamless worktree switching

workstack() {
  # Don't intercept if we're doing shell completion
  if [ -n "$_WORKSTACK_COMPLETE" ]; then
    command workstack "$@"
  elif [ "$1" = "switch" ]; then
    # Check if __switch returns the passthrough marker
    shift
    local output
    output=$(command workstack __switch "$@")
    if [ "$output" = "__WORKSTACK_PASSTHROUGH__" ]; then
      # Pass through to regular command
      command workstack switch "$@"
    else
      # Eval the activation script
      eval "$output"
    fi
  else
    # Pass through all other commands
    command workstack "$@"
  fi
}
