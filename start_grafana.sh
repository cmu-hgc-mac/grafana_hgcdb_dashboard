#!/bin/bash

# navigate to grafana directory
cd ~/grafana-v12.0.0/bin || { echo "Grafana not found"; exit 1; }

echo "Starting Grafana..."

# Set enviornment
export GF_SECURITY_ADMIN_USER=admin
export GF_SECURITY_ADMIN_PASSWORD=admin

export GF_USERS_SIGN_UP=false

export GF_AUTH_ANONYMOUS_ENABLED=true
export GF_AUTH_ANONYMOUS_ORG_ROLE=Viewer

DB_URL=$(python3 -c "import yaml; file = open('a_EverythingNeedToChange/db_conn.yaml','r'); institution = yaml.safe_load(file)['institution_abbr'];print(f'https://grafana.{institution}.com')")
export GF_SERVER_ROOT_URL=$DB_URL

# Kill any previous Grafana instance on port 3000 
if lsof -i :3000 > /dev/null; then
    echo "Port 3000 already in use, killing previous process..."
    kill -9 $(lsof -ti :3000)
fi

# Start Grafana server
./grafana server web > ../grafana_start.log 2>&1 &

# Wait to give it time to start
sleep 2

# Check if Grafana actually started (check port or process)
if lsof -i :3000 > /dev/null; then
    echo "Grafana started successfully at $GF_SERVER_ROOT_URL"
else
    echo "Grafana failed to start."
    exit 1
fi