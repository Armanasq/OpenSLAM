#!/bin/bash

# OpenSLAM Server Startup Script

echo "========================================="
echo "   OpenSLAM Server Startup"
echo "========================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r api/requirements.txt

# Create required directories
echo "Creating required directories..."
mkdir -p data/uploads
mkdir -p data/results
mkdir -p data/datasets
mkdir -p plugins
mkdir -p connectors

# Check if any plugins exist
if [ -z "$(ls -A plugins 2>/dev/null)" ]; then
    echo ""
    echo "WARNING: No plugins found in 'plugins/' directory"
    echo "Add SLAM plugins to get started with evaluations"
    echo ""
fi

# Start the server
echo ""
echo "========================================="
echo "Starting OpenSLAM API Server..."
echo "========================================="
echo ""
echo "Server will be available at:"
echo "  - API: http://localhost:5000/api"
echo "  - Frontend: Open frontend/index.html in your browser"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd "$(dirname "$0")"
python3 api/server.py
