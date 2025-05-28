#!/bin/bash

# get port from gf_conn.yaml
CONFIG_FILE="a_EverythingNeedToChange/gf_conn.yaml"
GF_PORT=$(yq '.GF_PORT' "$CONFIG_FILE" | tr -d "'\"")
GF_PORT=$((GF_PORT))
GF_USER=$(yq '.GF_USER' "$CONFIG_FILE")
GF_PASS=$(yq '.GF_PASS' "$CONFIG_FILE")

# navigate to grafana directory
cd ~/grafana-v12.0.0/bin || { echo "Grafana not found"; exit 1; }

echo "Starting Grafana...(≧∇≦)"

# Set enviornment
export GF_SECURITY_ADMIN_USER="$GF_USER"
export GF_SECURITY_ADMIN_PASSWORD="$GF_PASS"

export GF_USERS_SIGN_UP=false

export GF_AUTH_ANONYMOUS_ENABLED=true
export GF_AUTH_ANONYMOUS_ORG_ROLE=Viewer

export GF_AUTOFILL_PASSWORD=true

# Kill any previous Grafana instance on port 3000 
if lsof -i :$GF_PORT > /dev/null; then
    echo "Port $GF_PORT already in use (#ﾟдﾟ), killing previous process..."
    kill -9 $(lsof -ti :"$GF_PORT")
fi

# Start Grafana server
./grafana server web > ../grafana_start.log 2>&1 &

# Wait to give it time to start
sleep 2

# Check if Grafana actually started (check port or process)
if lsof -i :$GF_PORT > /dev/null; then
    echo "Grafana started successfully. ᕕ( ᐛ )ᕗ"
else
    echo "Grafana failed to start. Σ(ﾟдﾟ;)"
    exit 1
fi