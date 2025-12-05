#!/bin/bash
set -e

echo "Khoi tao Smart Cam AI Web UI..."
# Tao thu muc data neu chua co
mkdir -p /data/faces
mkdir -p /data/db

python3 /app.py