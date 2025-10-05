# Workstack shell integration for zsh
# This function wraps the workstack CLI to provide seamless worktree switching

workstack() {
  # Don't intercept if we're doing shell completion
  if [ -n "$_WORKSTACK_COMPLETE" ]; then
    command workstack "$@"
  elif [ "$1" = "switch" ]; then
    # Auto-activate worktree on switch
    shift
    eval "$(command workstack switch --script "$@")"
  else
    # Pass through all other commands
    command workstack "$@"
  fi
}
