#!/bin/bash
# Financial MCP Server Startup Script

cd "$(dirname "$0")/../.."
source venv/bin/activate

export PYTHONPATH="$(pwd):$PYTHONPATH"

echo "Starting Financial MCP Server..."
python servers/financial/server.py