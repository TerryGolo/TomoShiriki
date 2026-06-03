#!/bin/bash
# Ralph Loop Bash Script
# Usage: ./ralph.sh [max_iterations]

MAX_ITERATIONS=${1:-15}
TASKS_FILE="docs/tasks.md"

echo -e "\e[32m==========================================\e[0m"
echo -e "\e[32m       Starting TomoShiriki Ralph Loop    \e[0m"
echo -e "\e[32m==========================================\e[0m"
echo -e "Max Iterations: $MAX_ITERATIONS"

# Step 1: Detect if Docker is available and running
USE_DOCKER=false
if command -v docker &> /dev/null; then
    docker ps &> /dev/null
    if [ $? -eq 0 ]; then
        USE_DOCKER=true
    fi
fi

GIT_CONFIG_MOUNT=""
if [ "$USE_DOCKER" = true ]; then
    echo -e "Docker is running. Running in containerized sandbox mode."
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
    echo -e "\e[33mDocker is not running/available. Falling back to native host execution.\e[0m"
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
        docker run --rm -v "$(pwd):/workspace" -w /workspace $GIT_CONFIG_MOUNT tomoshiriki-dev agy -p --dangerously-skip-permissions "$Prompt"
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
