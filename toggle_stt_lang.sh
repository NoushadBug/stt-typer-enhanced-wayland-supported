#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="/tmp/stt_typer.pid"
FLAG_FILE="/tmp/stt_typer_bengali.flag"
LOG_FILE="/tmp/stt_typer.log"

if [ -f "$FLAG_FILE" ]; then
    CURRENT_MODE="bengali"
else
    CURRENT_MODE="english"
fi

if pgrep -f "stt-typer.*main.py" > /dev/null; then
    pkill -f "stt-typer.*main.py"
    
    while pgrep -f "stt-typer.*main.py" > /dev/null; do
        sleep 0.5
    done
    
    sleep 1
fi

if [ "$CURRENT_MODE" = "bengali" ]; then
    rm -f "$FLAG_FILE"
    NEW_MODE="english"
    notify-send -t 500 -h "string:transient:1" "STT Typer" "Switched to English"
else
    touch "$FLAG_FILE"
    NEW_MODE="bengali"
    notify-send -t 500 -h "string:transient:1" "STT Typer" "Switched to Bengali"
fi

cd "$SCRIPT_DIR"
nohup env BENGALI_MODE=$( [ "$NEW_MODE" = "bengali" ] && echo 1 || echo 0 ) uv run main.py > "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"

echo "STT Typer started in $NEW_MODE mode. PID: $(cat $PID_FILE)"
