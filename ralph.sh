#!/bin/bash
# Ralph Loop Bash Script
# Usage: ./ralph.sh [--no-docker] [max_iterations]
#
# Authentication: Set ANTIGRAVITY_API_KEY in your environment before running.
# Example: export ANTIGRAVITY_API_KEY=your_key_here && ./ralph.sh

# Defaults
USE_DOCKER=true
MAX_ITERATIONS=15

# Configure host git to avoid dubious ownership warnings inside WSL
git config --global --add safe.directory "$(pwd)" 2>/dev/null || true

# Check for API key
if [ -z "$ANTIGRAVITY_API_KEY" ]; then
    echo -e "\e[33mWarning: ANTIGRAVITY_API_KEY is not set.\e[0m"
    echo -e "\e[33mThe agent will prompt for interactive OAuth login on every container iteration.\e[0m"
    echo -e "\e[33mTo fix this, run: export ANTIGRAVITY_API_KEY=your_key_here\e[0m"
    echo ""
fi

for arg in "$@"; do
    case $arg in
        --no-docker)
        USE_DOCKER=false
        shift
        ;;
        *)
        if [[ "$arg" =~ ^[0-9]+$ ]]; then
            MAX_ITERATIONS=$arg
        fi
        ;;
    esac
done

TASKS_FILE="docs/tasks.md"

echo -e "\e[32m==========================================\e[0m"
echo -e "\e[32m       Starting TomoShiriki Ralph Loop    \e[0m"
echo -e "\e[32m==========================================\e[0m"
echo -e "Max Iterations: $MAX_ITERATIONS"
echo -e "Docker Sandbox: $USE_DOCKER"

GIT_CONFIG_MOUNT=""
if [ "$USE_DOCKER" = true ]; then
    echo -e "Docker Sandbox enabled. Building/verifying container image..."
    echo -e "\n\e[36mBuilding tomoshiriki-dev image...\e[0m"
    docker build -t tomoshiriki-dev -f .devcontainer/Dockerfile .
    if [ $? -ne 0 ]; then
        echo -e "\e[31mError: Failed to build Docker image 'tomoshiriki-dev'.\e[0m"
        exit 1
    fi
    
    if [ -f "$HOME/.gitconfig" ]; then
        GIT_CONFIG_MOUNT="-v $HOME/.gitconfig:/home/vscode/.gitconfig:ro"
        echo -e "Mounted host .gitconfig to container."
    fi
else
    echo -e "\e[33mRunning natively on WSL/Host environment.\e[0m"
fi

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

    if [ "$USE_DOCKER" = true ]; then
        # Dynamically detect if we are running in an interactive terminal (TTY)
        DOCKER_FLAGS="-i --rm"
        if [ -t 0 ] && [ -t 1 ]; then
            DOCKER_FLAGS="-it --rm"
        fi

        # Pass the API key into the container via -e flag, mount workspace, configure git
        docker run $DOCKER_FLAGS \
          -e ANTIGRAVITY_API_KEY="${ANTIGRAVITY_API_KEY}" \
          -v "$(pwd):/workspace" \
          -w /workspace \
          $GIT_CONFIG_MOUNT \
          tomoshiriki-dev \
          sh -c "
            if [ -f /home/vscode/.gitconfig ]; then
                cp /home/vscode/.gitconfig /tmp/.gitconfig
                export GIT_CONFIG_GLOBAL=/tmp/.gitconfig
            fi
            git config --global --add safe.directory /workspace
            exec agy -p --dangerously-skip-permissions \"$Prompt\"
          "
    else
        agy -p --dangerously-skip-permissions "$Prompt"
    fi

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
