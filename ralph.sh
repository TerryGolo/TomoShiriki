#!/bin/bash
# Ralph Loop - Host Launcher
# Usage: ./ralph.sh [max_iterations]
#
# This script builds the dev container image and launches a single long-lived
# container that runs the entire loop inside it. You authenticate agy once
# at startup, then all iterations run hands-free within the same container session.

MAX_ITERATIONS=${1:-15}

echo -e "\e[32m==========================================\e[0m"
echo -e "\e[32m       TomoShiriki Ralph Loop Launcher    \e[0m"
echo -e "\e[32m==========================================\e[0m"

# --- Step 1: Build the dev container image ---
echo -e "\n\e[36mBuilding tomoshiriki-dev image...\e[0m"
docker build -t tomoshiriki-dev -f .devcontainer/Dockerfile .
if [ $? -ne 0 ]; then
    echo -e "\e[31mError: Failed to build Docker image 'tomoshiriki-dev'. Make sure Docker is running.\e[0m"
    exit 1
fi

# --- Step 2: Prepare git config mount ---
GIT_CONFIG_MOUNT=""
if [ -f "$HOME/.gitconfig" ]; then
    GIT_CONFIG_MOUNT="-v $HOME/.gitconfig:/home/vscode/.gitconfig:ro"
    echo -e "Mounting host .gitconfig into container."
fi

# --- Step 3: Launch a single long-lived container ---
# The container runs ralph_entrypoint.sh which handles:
#   - D-Bus + keyring initialization (single session for the whole loop)
#   - Pre-authentication of agy (OAuth prompt once)
#   - The full iteration loop
echo -e "\n\e[36mLaunching dev container...\e[0m"
docker run -it --rm \
  -v "$(pwd):/workspace" \
  -w /workspace \
  $GIT_CONFIG_MOUNT \
  tomoshiriki-dev \
  bash /workspace/ralph_entrypoint.sh "$MAX_ITERATIONS"
