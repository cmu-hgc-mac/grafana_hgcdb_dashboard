#!/bin/bash

echo "Stopping Grafana..."

# get port from gf_conn.yaml
CONFIG_FILE="a_EverythingNeedToChange/gf_conn.yaml"
GF_PORT=$(yq '.GF_PORT' "$CONFIG_FILE" | tr -d "'\"")   # read from gf_conn
GF_PORT=$((GF_PORT))    # convert to int

# Listen to the operating port
PIDS=$(lsof -ti :$GF_PORT)

if [ -z "$PIDS" ]; then
    echo "No Grafana process running on port $GF_PORT."
else
    kill -9 $PIDS
    echo "Grafana processes stopped. (;´ヮ`)7"
fi
