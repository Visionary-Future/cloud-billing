#!/bin/bash

# Script to serve documentation locally for development

set -e

echo "Starting MkDocs development server..."
echo "Documentation will be available at http://127.0.0.1:8000"
echo "Press Ctrl+C to stop the server"

# Check if poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "Poetry is not installed. Please install Poetry first."
    exit 1
fi

# Install dependencies if needed
if [ ! -d ".venv" ]; then
    echo "Installing dependencies..."
    poetry install
fi

# Serve the documentation
poetry run mkdocs serve --dev-addr 127.0.0.1:8000
