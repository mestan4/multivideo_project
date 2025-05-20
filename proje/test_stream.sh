#!/bin/bash


SERVER_PORT=8000
SERVER_LOG="server.log"
CAM_ID="video1"
DEVICE_ID=1

echo " Checking if Flask server is already running on port $SERVER_PORT..."
if lsof -i:$SERVER_PORT -t >/dev/null; then
    echo " Flask server already running. Skipping server start."
else
    echo " Starting main server in background..."
    nohup python3 main_server.py > "$SERVER_LOG" 2>&1 &
    SERVER_PID=$!
    echo " Server started with PID $SERVER_PID"

    echo " Waiting for server to become available..."
    until curl -s "http://localhost:$SERVER_PORT/status" > /dev/null; do
        sleep 1
    done
    echo " Server is up."
fi

# Open dashboard in browser
echo " Opening dashboard at http://localhost:$SERVER_PORT/dashboard"
xdg-open "http://localhost:$SERVER_PORT/dashboard" > /dev/null 2>&1 &

# Auto-start camera stream
echo " Auto-starting stream '${CAM_ID}' on device ${DEVICE_ID}..."
curl -s -X POST http://localhost:$SERVER_PORT/stream/start \
     -H "Content-Type: application/json" \
     -d "{\"id\": \"${CAM_ID}\", \"url\": ${DEVICE_ID}}" > /dev/null

echo " Stream '${CAM_ID}' started."
echo " You can manage more streams on the dashboard UI."
