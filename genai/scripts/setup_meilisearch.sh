#!/bin/bash

# Meilisearch Setup Script for Prompteus GenAI Service
# This script sets up Meilisearch indices using Docker Compose

set -e

# Default values
RESET=false
TEST=false
TEST_ONLY=false
MEILISEARCH_URL="http://meilisearch:7700"
MEILI_MASTER_KEY="${MEILI_MASTER_KEY:-CHANGE_ME_CHANGE_ME}"

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Set up Meilisearch indices for Prompteus GenAI service

OPTIONS:
    --reset         Delete existing indices and recreate them
    --test          Run functionality tests after setup
    --test-only     Only run functionality tests (skip setup)
    --host HOST     Meilisearch host URL (default: http://meilisearch:7700)
    --key KEY       Meilisearch master key (default: from MEILI_MASTER_KEY env var)
    --help          Show this help message

EXAMPLES:
    # Basic setup
    $0

    # Reset indices and run tests
    $0 --reset --test

    # Only run tests
    $0 --test-only

    # Setup with custom host and key
    $0 --host http://localhost:7700 --key mykey

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --reset)
            RESET=true
            shift
            ;;
        --test)
            TEST=true
            shift
            ;;
        --test-only)
            TEST_ONLY=true
            shift
            ;;
        --host)
            MEILISEARCH_URL="$2"
            shift 2
            ;;
        --key)
            MEILI_MASTER_KEY="$2"
            shift 2
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Build command arguments
PYTHON_ARGS=""
if [ "$RESET" = true ]; then
    PYTHON_ARGS="$PYTHON_ARGS --reset"
fi
if [ "$TEST" = true ]; then
    PYTHON_ARGS="$PYTHON_ARGS --test"
fi
if [ "$TEST_ONLY" = true ]; then
    PYTHON_ARGS="$PYTHON_ARGS --test-only"
fi

# Set environment variables
export MEILISEARCH_URL="$MEILISEARCH_URL"
export MEILI_MASTER_KEY="$MEILI_MASTER_KEY"

echo "Setting up Meilisearch for Prompteus GenAI service..."
echo "Host: $MEILISEARCH_URL"
echo "Reset: $RESET"
echo "Test: $TEST"
echo "Test Only: $TEST_ONLY"
echo ""

# Check if we're in the genai directory
if [ ! -f "scripts/setup_meilisearch.py" ]; then
    echo "Error: This script must be run from the genai directory"
    echo "Current directory: $(pwd)"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed or not in PATH"
    exit 1
fi

# Check if Meilisearch service is running
echo "Checking if Meilisearch service is running..."
if docker compose ps meilisearch | grep -q "Up"; then
    echo "✓ Meilisearch service is running"
else
    echo "Starting Meilisearch service..."
    docker compose up -d meilisearch
    
    # Wait for Meilisearch to be ready
    echo "Waiting for Meilisearch to be ready..."
    for i in {1..30}; do
        if docker compose exec meilisearch curl -s http://localhost:7700/health > /dev/null 2>&1; then
            echo "✓ Meilisearch is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            echo "Error: Meilisearch failed to start within 30 seconds"
            exit 1
        fi
        sleep 1
    done
fi

# Run the Python setup script using Docker Compose
echo "Running Meilisearch setup..."
docker compose run --rm genai python scripts/setup_meilisearch.py \
    --host "$MEILISEARCH_URL" \
    --key "$MEILI_MASTER_KEY" \
    $PYTHON_ARGS

echo ""
echo "Meilisearch setup completed!" 