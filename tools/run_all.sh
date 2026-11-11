#!/bin/bash
# Runs every app and rebuilds and executes the notebook. Needs GEMINI_API_KEY.
set -e
cd "$(dirname "$0")/.."
python apps/01_receipts/audit.py
python apps/02_screen_checks/agent.py
python apps/02_screen_checks/live_todo.py
python apps/03_voice_reflex/reflex.py
python apps/03_voice_reflex/stream.py
python tools/build_notebook.py --run
