#!/bin/bash

# Test script for the Strands MCP Agent

echo "Running tests for Strands MCP Agent..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run tests
echo "Running pytest..."
pytest tests/ -v

# Test the API endpoints if the server is running
echo "Testing API endpoints..."
curl -f http://localhost:8000/health || echo "Server not running - start with 'python app.py'"