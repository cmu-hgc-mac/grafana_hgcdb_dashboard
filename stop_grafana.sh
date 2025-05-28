#!/bin/bash

echo "Stopping Grafana..."

# get port from gf_conn.yaml
CONFIG_FILE="a_EverythingNeedToChange/gf_conn.yaml"
GF_PORT=$(yq '.GF_PORT' "$CONFIG_FILE" | tr -d "'\"")
GF_PORT=$((GF_PORT))

# Listen to the operating port: 3000
PIDS=$(lsof -ti :$GF_PORT)

if [ -z "$PIDS" ]; then
    echo "No Grafana process running on port $GF_PORT."
else
    kill -9 $PIDS
    echo "Grafana process(es) [$PIDS] stopped."
fi
