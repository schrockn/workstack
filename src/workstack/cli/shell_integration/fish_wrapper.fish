# Workstack shell integration for fish
# This function wraps the workstack CLI to provide seamless worktree switching

function workstack
    # Don't intercept if we're doing shell completion
    if set -q _WORKSTACK_COMPLETE
        command workstack $argv
        return
    end

    set -l script_path (env WORKSTACK_SHELL=fish command workstack __shell $argv)
    set -l exit_status $status

    # Passthrough mode
    if test "$script_path" = "__WORKSTACK_PASSTHROUGH__"
        command workstack $argv
        return
    end

    # If __shell returned non-zero, error messages are already sent to stderr
    if test $exit_status -ne 0
        return $exit_status
    end

    # Source the script file if it exists
    if test -n "$script_path" -a -f "$script_path"
        source "$script_path"
        set -l source_exit $status

        # Clean up unless WORKSTACK_KEEP_SCRIPTS is set
        if not set -q WORKSTACK_KEEP_SCRIPTS
            rm -f "$script_path"
        end

        return $source_exit
    end
end
