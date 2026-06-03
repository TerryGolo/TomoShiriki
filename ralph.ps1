# Ralph Loop - Host Launcher (Windows)
# Usage: .\ralph.ps1 [-MaxIterations <int>]
#
# This script builds the dev container image and launches a single long-lived
# container that runs the entire loop inside it. You authenticate agy once
# at startup, then all iterations run hands-free within the same container session.

param (
    [int]$MaxIterations = 15
)

Write-Host "==========================================" -ForegroundColor Green
Write-Host "       TomoShiriki Ralph Loop Launcher    " -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

# --- Step 1: Build the dev container image ---
Write-Host "`nBuilding tomoshiriki-dev image..." -ForegroundColor Cyan
docker build -t tomoshiriki-dev -f .devcontainer/Dockerfile .
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to build Docker image 'tomoshiriki-dev'. Make sure Docker is running." -ForegroundColor Red
    exit 1
}

# --- Step 2: Prepare git config mount ---
$GitConfigMount = ""
$HomeDir = $env:USERPROFILE
if (Test-Path "$HomeDir\.gitconfig") {
    $GitConfigMount = "-v `"$HomeDir\.gitconfig:/home/vscode/.gitconfig:ro`""
    Write-Host "Mounting host .gitconfig into container." -ForegroundColor Gray
}

# --- Step 3: Launch a single long-lived container ---
Write-Host "`nLaunching dev container..." -ForegroundColor Cyan
$DockerCmd = "docker run -it --rm -v `"${PWD}:/workspace`" -w /workspace $GitConfigMount tomoshiriki-dev bash /workspace/ralph_entrypoint.sh $MaxIterations"
Invoke-Expression $DockerCmd
