# Ralph Loop PowerShell Script for Windows
# Usage: .\ralph.ps1 [-MaxIterations <int>]

param (
    [int]$MaxIterations = 15
)

Write-Host "==========================================" -ForegroundColor Green
Write-Host "       Starting TomoShiriki Ralph Loop    " -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Max Iterations: $MaxIterations" -ForegroundColor Gray

# Step 1: Detect if Docker is available and running
$UseDocker = $false
if (Get-Command docker -ErrorAction SilentlyContinue) {
    docker ps > $null 2>&1
    if ($LASTEXITCODE -eq 0) {
        $UseDocker = $true
    }
}

$GitConfigMount = ""
if ($UseDocker) {
    Write-Host "Docker is running. Running in containerized sandbox mode." -ForegroundColor Green
    Write-Host "`nBuilding tomoshiriki-dev image..." -ForegroundColor Cyan
    docker build -t tomoshiriki-dev -f .devcontainer/Dockerfile .
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to build Docker image 'tomoshiriki-dev'." -ForegroundColor Red
        exit 1
    }
    
    $HomeDir = $env:USERPROFILE
    if (Test-Path "$HomeDir\.gitconfig") {
        $GitConfigMount = "-v `"$HomeDir\.gitconfig:/home/vscode/.gitconfig:ro`""
        Write-Host "Mounted host .gitconfig to container." -ForegroundColor Gray
    }
} else {
    Write-Host "Docker is not running/available. Falling back to native host execution." -ForegroundColor Yellow
}

$Iteration = 0
$TasksFile = "docs/tasks.md"

while ($Iteration -lt $MaxIterations) {
    $Iteration++
    Write-Host "`n--- Iteration $Iteration of $MaxIterations ---" -ForegroundColor Cyan

    if (-not (Test-Path $TasksFile)) {
        Write-Host "Error: $TasksFile not found!" -ForegroundColor Red
        exit 1
    }

    # Read tasks to verify if there are pending items
    $TasksContent = Get-Content -Path $TasksFile -Raw
    if ($TasksContent -notmatch '- \[[ ]\]') {
        Write-Host "All tasks completed! Terminating Ralph Loop." -ForegroundColor Green
        break
    }

    # Display pending tasks
    Write-Host "Current pending tasks:" -ForegroundColor Yellow
    $Lines = Get-Content -Path $TasksFile
    foreach ($Line in $Lines) {
        if ($Line -match '- \[[ ]\]') {
            Write-Host "  $Line" -ForegroundColor Yellow
        }
    }

    Write-Host "`nInvoking AI coding agent..." -ForegroundColor Cyan
    
    # Construct the instruction prompt
    $Prompt = "Read docs/PRD.md, docs/ralph_agent_instructions.md, and docs/tasks.md. Identify the next incomplete task, implement it, write unit tests in core/tests.py, verify tests pass, mark the task as complete in docs/tasks.md, commit the changes using git, and then exit."

    if ($UseDocker) {
        # Run agy inside the docker container
        $DockerCmd = "docker run --rm -v `"${PWD}:/workspace`" -w /workspace $GitConfigMount tomoshiriki-dev agy -p --dangerously-skip-permissions `"$Prompt`""
        Invoke-Expression $DockerCmd
    } else {
        # Run agy directly on host
        agy -p --dangerously-skip-permissions "$Prompt"
    }

    # Safety git auto-commit hook (in case agent completed changes but failed to commit)
    $GitStatus = git status --porcelain
    if ($GitStatus) {
        Write-Host "Detected uncommitted changes after agent execution. Committing..." -ForegroundColor Yellow
        git add .
        git commit -m "ralph: auto-commit iteration $Iteration"
    }

    # Rest for a few seconds to avoid API limit hits
    Start-Sleep -Seconds 3
}

Write-Host "`n==========================================" -ForegroundColor Green
Write-Host "       Ralph Loop Execution Finished       " -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
