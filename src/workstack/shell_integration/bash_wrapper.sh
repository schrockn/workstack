# Workstack shell integration for bash
# This function wraps the workstack CLI to provide seamless worktree switching

workstack() {
  # Don't intercept if we're doing shell completion
  if [ -n "$_WORKSTACK_COMPLETE" ]; then
    command workstack "$@"
    return $?
  fi

  local output
  output=$(command workstack __shell "$@")
  local status=$?

  if [ "$output" = "__WORKSTACK_PASSTHROUGH__" ]; then
    command workstack "$@"
    return $?
  fi

  if [ $status -ne 0 ]; then
    return $status
  fi

  if [ -n "$output" ]; then
    eval "$output"
  fi

  return 0
}
