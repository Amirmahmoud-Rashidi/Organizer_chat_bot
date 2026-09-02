# ===========================================================================
# Organizer Chat Bot — Windows PowerShell runner (recommended on Windows)
# Usage:  .\run.ps1
# What it does:
#   - Creates .venv on first run
#   - Installs requirements into .venv
#   - Runs the bot
# Press Ctrl+C to stop.
# ===========================================================================

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

# Pick a Python interpreter: prefer `py -3.11`, fall back to `python`.
$useLauncher = $false
try {
    & py -3.11 --version *> $null
    if ($LASTEXITCODE -eq 0) { $useLauncher = $true }
} catch { }

if (-not $useLauncher) {
    & python --version *> $null
    if ($LASTEXITCODE -ne 0) {
        Write-Host '[error] Python 3.11+ is required but not found on PATH.' -ForegroundColor Red
        exit 1
    }
}

$venvPython = Join-Path -Path '.venv' -ChildPath 'Scripts\python.exe'

if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Host '[setup] Creating virtual environment...' -ForegroundColor Cyan
    if ($useLauncher) {
        & py -3.11 -m venv .venv
    } else {
        & python -m venv .venv
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Host '[error] Failed to create virtual environment.' -ForegroundColor Red
        exit 1
    }
}

Write-Host '[setup] Installing/upgrading dependencies...' -ForegroundColor Cyan
& $venvPython -m pip install --quiet --upgrade pip
& $venvPython -m pip install --quiet -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host '[error] Failed to install dependencies.' -ForegroundColor Red
    exit 1
}

if (-not (Test-Path -LiteralPath '.env')) {
    Write-Host ''
    Write-Host '[setup] No .env found. Copying from .env.example...' -ForegroundColor Yellow
    Copy-Item -LiteralPath '.env.example' -Destination '.env'
    Write-Host ''
    Write-Host 'IMPORTANT: Edit .env and fill in your real credentials' -ForegroundColor Yellow
    Write-Host 'before running the bot again. See README.md for guidance.' -ForegroundColor Yellow
    Write-Host ''
    exit 1
}

Write-Host '[run] Starting Organizer Chat Bot...' -ForegroundColor Green
& $venvPython -m src.main