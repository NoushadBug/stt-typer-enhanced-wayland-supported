#!/bin/bash

# STT Typer Toggle Script
# Checks if the speech-to-text process is running and toggles it
# Session type detection happens during installation (install-wayland.sh)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="/tmp/stt_typer.pid"

# Check if process is running
if pgrep -f "stt-typer.*main.py" > /dev/null; then
    echo "STT Typer is running. Stopping gracefully..."
    pkill -f "stt-typer.*main.py"

    # Wait for process to finish current transcription
    echo "Waiting for process to complete..."
    while pgrep -f "stt-typer.*main.py" > /dev/null; do
        sleep 1
    done

    rm -f "$PID_FILE"
    echo "STT Typer stopped."
else
    echo "STT Typer is not running. Starting..."
    cd "$SCRIPT_DIR"
    nohup uv run main.py > /tmp/stt_typer.log 2>&1 &
    echo $! > "$PID_FILE"
    echo "STT Typer started. PID: $(cat $PID_FILE)"
    echo "Log file: /tmp/stt_typer.log"
fi
