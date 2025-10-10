# Workstack shell integration for zsh
# This function wraps the workstack CLI to provide seamless worktree switching

workstack() {
  # Don't intercept if we're doing shell completion
  [ -n "$_WORKSTACK_COMPLETE" ] && { command workstack "$@"; return; }

  local script_path exit_status

  # Debug: log invocation
  if [ "$WORKSTACK_DEBUG" = "1" ]; then
    echo "[$(date -Iseconds)] Wrapper: Calling __shell with args: $@" >> /tmp/workstack-debug.log
  fi

  script_path=$(command workstack __shell "$@")
  exit_status=$?

  # Debug: log result
  if [ "$WORKSTACK_DEBUG" = "1" ]; then
    echo "[$(date -Iseconds)] Wrapper: Got script_path=$script_path, exit=$exit_status" >> /tmp/workstack-debug.log
    if [ -f "$script_path" ]; then
      echo "[$(date -Iseconds)] Wrapper: Script exists, size=$(wc -c < "$script_path")" >> /tmp/workstack-debug.log
    else
      echo "[$(date -Iseconds)] Wrapper: Script does NOT exist at $script_path" >> /tmp/workstack-debug.log
    fi
  fi

  # Passthrough mode: run the original command directly
  [ "$script_path" = "__WORKSTACK_PASSTHROUGH__" ] && { command workstack "$@"; return; }

  # If __shell returned non-zero, error messages are already sent to stderr
  [ $exit_status -ne 0 ] && return $exit_status

  # Source the script file if it exists
  if [ -n "$script_path" ] && [ -f "$script_path" ]; then
    # Debug: log before sourcing
    if [ "$WORKSTACK_DEBUG" = "1" ]; then
      echo "[$(date -Iseconds)] Wrapper: About to source $script_path" >> /tmp/workstack-debug.log
      echo "[$(date -Iseconds)] Wrapper: PWD before source: $(pwd)" >> /tmp/workstack-debug.log
    fi

    source "$script_path"
    local source_exit=$?

    # Debug: log after sourcing
    if [ "$WORKSTACK_DEBUG" = "1" ]; then
      echo "[$(date -Iseconds)] Wrapper: After source, exit=$source_exit, PWD=$(pwd)" >> /tmp/workstack-debug.log
    fi

    # Clean up unless WORKSTACK_KEEP_SCRIPTS is set
    if [ -z "$WORKSTACK_KEEP_SCRIPTS" ]; then
      rm -f "$script_path"
    fi

    return $source_exit
  fi
}
