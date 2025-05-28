#!/bin/bash

# load info
CONFIG_FILE="a_EverythingNeedToChange/gf_conn.yaml"     # define path
GF_PORT=$(yq '.GF_PORT' "$CONFIG_FILE" | tr -d "'\"")   # port
GF_PORT=$((GF_PORT))    # convert to int
GF_USER=$(yq '.GF_USER' "$CONFIG_FILE")     # user name
GF_PASS=$(yq '.GF_PASS' "$CONFIG_FILE")     # user password

# navigate to grafana directory
cd ~/grafana-v12.0.0/bin || { echo "Grafana not found"; exit 1; }

echo "Starting Grafana...(≧∇≦)"

# Set enviornment
export GF_SECURITY_ADMIN_USER="$GF_USER"
export GF_SECURITY_ADMIN_PASSWORD="$GF_PASS"    # auto login

export GF_USERS_SIGN_UP=false   # skip sign up

export GF_AUTH_ANONYMOUS_ENABLED=true
export GF_AUTH_ANONYMOUS_ORG_ROLE=Viewer    # allow anonymous connetion

export GF_AUTOFILL_PASSWORD=true    # auto sign up

# Kill any previous Grafana instance on port
if lsof -i :$GF_PORT > /dev/null; then
    echo "Port $GF_PORT already in use (#ﾟдﾟ), killing previous process..."
    kill -9 $(lsof -ti :"$GF_PORT")
fi

# Start Grafana server
./grafana server web > ../grafana_start.log 2>&1 &

# Wait to give time to start
sleep 2

# Check if Grafana actually started (check port or process)
if lsof -i :$GF_PORT > /dev/null; then
    echo "Grafana started successfully. ᕕ( ᐛ )ᕗ"
else
    echo "Grafana failed to start. Σ(ﾟдﾟ;)"
    exit 1
fi