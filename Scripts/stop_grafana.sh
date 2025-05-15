#!/bin/bash

echo "Stopping Grafana..."

# Listen to the operating port: 3000
PIDS=$(lsof -ti :3000)

if [ -z "$PIDS" ]; then
    echo "No Grafana process running on port 3000."
else
    kill -9 $PIDS
    echo "Grafana process(es) [$PIDS] stopped."
fi
