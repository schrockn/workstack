# Workstack shell integration for fish
# This function wraps the workstack CLI to provide seamless worktree switching

function workstack
    # Don't intercept if we're doing shell completion
    if set -q _WORKSTACK_COMPLETE
        command workstack $argv
    else if test "$argv[1]" = "switch"
        # Auto-activate worktree on switch
        set -e argv[1]
        eval (command workstack switch --script $argv)
    else
        # Pass through all other commands
        command workstack $argv
    end
end
