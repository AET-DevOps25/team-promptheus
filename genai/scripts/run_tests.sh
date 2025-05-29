#!/bin/bash

# Test Runner Script for Prompteus GenAI Service
# This script ensures Meilisearch is running and then runs the tests

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🧪 Prompteus GenAI Test Runner${NC}"
echo "=================================="

# Check if we're in the genai directory
if [ ! -f "app.py" ]; then
    echo -e "${RED}Error: This script must be run from the genai directory${NC}"
    echo "Current directory: $(pwd)"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed or not in PATH${NC}"
    exit 1
fi

# Start Meilisearch if not running
echo -e "${YELLOW}📡 Checking Meilisearch service...${NC}"
if docker compose ps meilisearch | grep -q "Up"; then
    echo -e "${GREEN}✓ Meilisearch service is running${NC}"
else
    echo -e "${YELLOW}🚀 Starting Meilisearch service...${NC}"
    docker compose up -d meilisearch
    
    # Wait for Meilisearch to be ready
    echo -e "${YELLOW}⏳ Waiting for Meilisearch to be ready...${NC}"
    for i in {1..30}; do
        if docker compose exec meilisearch curl -s http://localhost:7700/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Meilisearch is ready${NC}"
            break
        fi
        if [ $i -eq 30 ]; then
            echo -e "${RED}Error: Meilisearch failed to start within 30 seconds${NC}"
            exit 1
        fi
        sleep 1
    done
fi

# Set up Meilisearch indices
echo -e "${YELLOW}🔧 Setting up Meilisearch indices...${NC}"
docker compose run --rm genai python scripts/setup_meilisearch.py --reset

# Run the tests, with coverage, forwarding the arguments to pytest
echo -e "${YELLOW}🧪 Running tests...${NC}"
docker compose run --rm genai python -m pytest tests/ "$@"

echo -e "${GREEN}✅ All tests completed!${NC}" 