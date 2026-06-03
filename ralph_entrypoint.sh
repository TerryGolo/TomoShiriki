#!/bin/bash
# Ralph Loop - Container Entrypoint
# This script runs INSIDE the dev container. It initializes the keyring session,
# pre-authenticates agy, then runs the task loop. All iterations share the same
# container process, so auth persists.

set -e

MAX_ITERATIONS=${1:-15}
TASKS_FILE="docs/tasks.md"

echo -e "\e[32m==========================================\e[0m"
echo -e "\e[32m   TomoShiriki Ralph Loop (Container)     \e[0m"
echo -e "\e[32m==========================================\e[0m"
echo -e "Max Iterations: $MAX_ITERATIONS"

# --- Step 1: Configure git ---
if [ -f /home/vscode/.gitconfig ]; then
    cp /home/vscode/.gitconfig /tmp/.gitconfig
    export GIT_CONFIG_GLOBAL=/tmp/.gitconfig
fi
git config --global --add safe.directory /workspace

# --- Step 2: Initialize keyring session for persistent auth ---
echo -e "\e[36mInitializing D-Bus session and keyring...\e[0m"
eval "$(dbus-launch --sh-syntax)"
eval "$(printf '\n' | gnome-keyring-daemon --unlock 2>/dev/null)"
eval "$(printf '\n' | gnome-keyring-daemon --start --components=secrets 2>/dev/null)"
echo -e "\e[32mKeyring session active.\e[0m"

# --- Step 3: Pre-authenticate agy ---
echo -e "\n\e[36mPre-authenticating agy (you may need to paste an OAuth code)...\e[0m"
agy -p "Say 'ready' and nothing else."
if [ $? -ne 0 ]; then
    echo -e "\e[31mError: agy authentication failed. Please try again.\e[0m"
    exit 1
fi
echo -e "\e[32magy authenticated successfully! Starting loop...\e[0m"

# --- Step 4: Run the task loop ---
ITERATION=0

while [ $ITERATION -lt $MAX_ITERATIONS ]; do
    let ITERATION++
    echo -e "\n\e[36m--- Iteration $ITERATION of $MAX_ITERATIONS ---\e[0m"

    if [ ! -f "$TASKS_FILE" ]; then
        echo -e "\e[31mError: $TASKS_FILE not found!\e[0m"
        exit 1
    fi

    # Check for remaining unchecked tasks
    if ! grep -q '\- \[[ ]\]' "$TASKS_FILE"; then
        echo -e "\e[32mAll tasks completed! Terminating Ralph Loop.\e[0m"
        break
    fi

    # Display pending tasks
    echo -e "\e[33mCurrent pending tasks:\e[0m"
    grep '\- \[[ ]\]' "$TASKS_FILE"

    echo -e "\n\e[36mInvoking AI coding agent...\e[0m"
    Prompt="Read docs/PRD.md, docs/ralph_agent_instructions.md, and docs/tasks.md. Identify the next incomplete task, implement it, write unit tests in core/tests.py, verify tests pass, mark the task as complete in docs/tasks.md, commit the changes using git, and then exit."

    agy -p --dangerously-skip-permissions "$Prompt"

    # Auto-commit fallback
    if [ -n "$(git status --porcelain)" ]; then
        echo -e "\e[33mDetected uncommitted changes after agent execution. Committing...\e[0m"
        git add .
        git commit -m "ralph: auto-commit iteration $ITERATION"
    fi

    # Brief delay
    sleep 3
done

echo -e "\n\e[32m==========================================\e[0m"
echo -e "\e[32m       Ralph Loop Execution Finished       \e[0m"
echo -e "\e[32m==========================================\e[0m"
