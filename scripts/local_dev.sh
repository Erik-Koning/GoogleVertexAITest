#!/bin/bash
# Local development script

set -e

# Check for .env file
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "Please edit .env with your configuration and run this script again."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run the application
echo "Starting local development server..."
echo "API will be available at http://localhost:8080"
echo "API docs at http://localhost:8080/docs"
echo ""
uvicorn src.main:app --reload --host 0.0.0.0 --port 8080
