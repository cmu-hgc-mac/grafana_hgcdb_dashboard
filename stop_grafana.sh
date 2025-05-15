#!/bin/bash

echo "Stopping Grafana..."

# 查找监听 3000 端口的所有进程
PIDS=$(lsof -ti :3000)

if [ -z "$PIDS" ]; then
    echo "No Grafana process running on port 3000."
else
    kill -9 $PIDS
    echo "Grafana process(es) [$PIDS] stopped."
fi
