#!/bin/bash

# STT Typer Toggle Script
# Checks if the speech-to-text process is running and toggles it

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="/tmp/stt_typer.pid"

if pgrep -f "stt-typer.*main.py" > /dev/null; then
    echo "STT Typer is running. Stopping gracefully..."
    pkill -f "stt-typer.*main.py"

    while pgrep -f "stt-typer.*main.py" > /dev/null; do
        sleep 1
    done

    rm -f "$PID_FILE"
    notify-send -t 500 -h "string:transient:1" "STT Typer" "Stopped"
else
    FLAG_FILE="/tmp/stt_typer_bengali.flag"
    if [ -f "$FLAG_FILE" ]; then
        MODE="bengali"
        BENGALI_MODE=1
    else
        MODE="english"
        BENGALI_MODE=0
    fi
    
    cd "$SCRIPT_DIR"
    nohup env BENGALI_MODE=$BENGALI_MODE uv run main.py > /tmp/stt_typer.log 2>&1 &
    echo $! > "$PID_FILE"
    notify-send -t 500 -h "string:transient:1" "STT Typer" "Started ($MODE mode)"
fi
