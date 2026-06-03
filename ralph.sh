#!/bin/bash
# Ralph Loop Bash Script (WSL Native)
# Usage: ./ralph.sh [max_iterations]
#
# This script runs the entire loop inside a single dbus session on WSL.
# You authenticate agy once at the start, and the session persists for all iterations.

MAX_ITERATIONS=${1:-15}
TASKS_FILE="docs/tasks.md"

# Configure git to avoid dubious ownership warnings inside WSL
git config --global --add safe.directory "$(pwd)" 2>/dev/null || true

echo -e "\e[32m==========================================\e[0m"
echo -e "\e[32m       Starting TomoShiriki Ralph Loop    \e[0m"
echo -e "\e[32m==========================================\e[0m"
echo -e "Max Iterations: $MAX_ITERATIONS"

# --- Step 1: Initialize keyring session for persistent auth ---
# Start dbus and gnome-keyring once for the entire loop lifetime
if command -v dbus-launch &> /dev/null && command -v gnome-keyring-daemon &> /dev/null; then
    echo -e "\e[36mInitializing D-Bus session and keyring...\e[0m"
    eval "$(dbus-launch --sh-syntax)"
    eval "$(printf '\n' | gnome-keyring-daemon --unlock 2>/dev/null)"
    eval "$(printf '\n' | gnome-keyring-daemon --start --components=secrets 2>/dev/null)"
    echo -e "\e[32mKeyring session active. Auth will persist across iterations.\e[0m"
fi

# --- Step 2: Pre-authenticate agy before the loop ---
echo -e "\n\e[36mPre-authenticating agy (you may need to paste an OAuth code)...\e[0m"
agy -p "Say 'ready' and nothing else."
if [ $? -ne 0 ]; then
    echo -e "\e[31mError: agy authentication failed. Please try again.\e[0m"
    exit 1
fi
echo -e "\e[32magy authenticated successfully!\e[0m"

# --- Step 3: Run the loop ---
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
