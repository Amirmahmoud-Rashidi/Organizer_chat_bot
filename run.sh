#!/usr/bin/env bash
# ===========================================================================
# Organizer Chat Bot — Linux / macOS runner
# Usage:  ./run.sh
# ===========================================================================
set -euo pipefail
cd "$(dirname "$0")"

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "[error] python3 not found on PATH." >&2
    exit 1
fi

if [[ ! -f ".venv/bin/python" ]]; then
    echo "[setup] Creating virtual environment..."
    "$PYTHON_BIN" -m venv .venv
fi

echo "[setup] Installing/upgrading dependencies..."
.venv/bin/python -m pip install --quiet --upgrade pip
.venv/bin/python -m pip install --quiet -r requirements.txt

if [[ ! -f ".env" ]]; then
    echo ""
    echo "[setup] No .env found. Copying from .env.example..."
    cp .env.example .env
    echo ""
    echo "IMPORTANT: Edit .env and fill in your real credentials"
    echo "before running the bot again. See README.md for guidance."
    echo ""
    exit 1
fi

echo "[run] Starting Organizer Chat Bot..."
exec .venv/bin/python -m src.main