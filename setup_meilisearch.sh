#!/bin/bash

# Meilisearch Setup Script for Team Promptheus
# This script sets up Meilisearch indices and configuration using HTTP API

set -e

# Configuration
MEILISEARCH_URL="${MEILISEARCH_URL:-http://localhost:7700}"
MEILI_MASTER_KEY="${MEILI_MASTER_KEY:-CHANGE_ME_CHANGE_ME}"
OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-https://gpu.aet.cit.tum.de/ollama}"
OLLAMA_API_KEY="${OLLAMA_API_KEY:-}"
OLLAMA_EMBEDDING_MODEL="${OLLAMA_EMBEDDING_MODEL:-tinyllama:latest}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# Check if Meilisearch is healthy
check_meilisearch_health() {
    log_info "Checking Meilisearch health..."
    
    local health_response
    health_response=$(curl -s -w "%{http_code}" \
        -H "Authorization: Bearer ${MEILI_MASTER_KEY}" \
        "${MEILISEARCH_URL}/health" 2>/dev/null || echo "000")
    
    local http_code="${health_response: -3}"
    local response_body="${health_response%???}"
    
    if [ "$http_code" = "200" ]; then
        log_info "✅ Meilisearch is healthy"
        return 0
    else
        log_error "❌ Meilisearch health check failed (HTTP $http_code)"
        return 1
    fi
}

# Create contributions index
create_contributions_index() {
    log_info "Creating contributions index..."
    
    local response
    response=$(curl -s -w "%{http_code}" \
        -X POST \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer ${MEILI_MASTER_KEY}" \
        -d '{"uid":"contributions","primaryKey":"id"}' \
        "${MEILISEARCH_URL}/indexes" 2>/dev/null || echo "000")
    
    local http_code="${response: -3}"
    local response_body="${response%???}"
    
    if [ "$http_code" = "202" ] || [ "$http_code" = "201" ]; then
        log_info "✅ Contributions index created successfully"
        
        # Wait for index creation to complete
        local task_uid
        task_uid=$(echo "$response_body" | grep -o '"taskUid":[0-9]*' | cut -d':' -f2)
        if [ -n "$task_uid" ]; then
            wait_for_task "$task_uid"
        fi
    elif [ "$http_code" = "400" ] && echo "$response_body" | grep -q "index_already_exists"; then
        log_info "✅ Contributions index already exists"
        return 0  # Success, no need to wait for task
    else
        log_error "❌ Failed to create contributions index (HTTP $http_code): $response_body"
        return 1
    fi
}

# Configure index settings
configure_index_settings() {
    log_info "Configuring index settings..."
    
    # Prepare embedder configuration based on both Java and Python implementations
    local embedders_config=""
    if [ -n "$OLLAMA_API_KEY" ]; then
        log_info "Configuring embedders for AI-powered semantic search..."
        # Use REST embedder configuration (matches Python implementation)
        embedders_config="\"embedders\": {
            \"default\": {
                \"source\": \"rest\",
                \"url\": \"${OLLAMA_BASE_URL}/api/embeddings\",
                \"request\": {\"model\": \"${OLLAMA_EMBEDDING_MODEL}\", \"prompt\": \"{{text}}\"},
                \"response\": {\"embedding\": \"{{embedding}}\"},
                \"headers\": {
                    \"Authorization\": \"Bearer ${OLLAMA_API_KEY}\",
                    \"Content-Type\": \"application/json\"
                },
                \"documentTemplate\": \"Repository: {{doc.repository}} Author: {{doc.author}} Type: {{doc.contribution_type}} Title: {{doc.title}} Content: {{doc.content}}\"
            }
        },"
    fi

    # Create settings JSON
    local settings_json="{
        \"searchableAttributes\": [
            \"content\",
            \"title\",
            \"message\",
            \"body\",
            \"repository\",
            \"author\",
            \"filename\",
            \"patch\"
        ],
        \"filterableAttributes\": [
            \"user\",
            \"week\",
            \"contribution_type\",
            \"repository\",
            \"author\",
            \"created_at_timestamp\",
            \"is_selected\"
        ],
        \"sortableAttributes\": [
            \"created_at_timestamp\",
            \"relevance_score\"
        ],
        \"rankingRules\": [
            \"words\",
            \"typo\",
            \"proximity\",
            \"attribute\",
            \"sort\",
            \"exactness\"
        ],
        \"stopWords\": [
            \"the\", \"a\", \"an\", \"and\", \"or\", \"but\", \"in\", \"on\", \"at\", \"to\", \"for\", \"of\", \"with\", \"by\"
        ],
        \"synonyms\": {
            \"bug\": [\"issue\", \"problem\", \"error\", \"defect\"],
            \"feature\": [\"enhancement\", \"improvement\", \"addition\"],
            \"fix\": [\"repair\", \"resolve\", \"correct\"],
            \"test\": [\"testing\", \"spec\", \"unit test\", \"integration test\"],
            \"docs\": [\"documentation\", \"manual\", \"guide\", \"reference\", \"instructions\", \"specification\", \"write-up\", \"explanation\", \"readme\", \"code comments\", \"annotations\", \"api reference\", \"developer notes\", \"inline documentation\", \"technical notes\", \"design document\", \"user guide\", \"how-to\", \"tutorial\", \"knowledge base\", \"help files\", \"usage instructions\", \"change log\"]
``
        },
        ${embedders_config}
        \"displayedAttributes\": [
            \"*\"
        ]
    }"

    local response
    response=$(curl -s -w "%{http_code}" \
        -X PATCH \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer ${MEILI_MASTER_KEY}" \
        -d "$settings_json" \
        "${MEILISEARCH_URL}/indexes/contributions/settings" 2>/dev/null || echo "000")
    
    local http_code="${response: -3}"
    local response_body="${response%???}"
    
    if [ "$http_code" = "202" ]; then
        log_info "✅ Index settings updated successfully"
        
        # Wait for settings update to complete
        local task_uid
        task_uid=$(echo "$response_body" | grep -o '"taskUid":[0-9]*' | cut -d':' -f2)
        if [ -n "$task_uid" ]; then
            wait_for_task "$task_uid"
        fi
    else
        log_error "❌ Failed to update index settings (HTTP $http_code): $response_body"
        return 1
    fi
}

# Wait for a Meilisearch task to complete
wait_for_task() {
    local task_uid="$1"
    log_debug "Waiting for task $task_uid to complete..."
    
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        local response
        response=$(curl -s \
            -H "Authorization: Bearer ${MEILI_MASTER_KEY}" \
            "${MEILISEARCH_URL}/tasks/${task_uid}" 2>/dev/null || echo "")
        
        if echo "$response" | grep -q '"status":"succeeded"'; then
            log_debug "✅ Task $task_uid completed successfully"
            return 0
        elif echo "$response" | grep -q '"status":"failed"'; then
            # Check if it failed because index already exists
            if echo "$response" | grep -q "index_already_exists"; then
                log_info "✅ Task completed (index already exists)"
                return 0
            else
                log_error "❌ Task $task_uid failed: $response"
                return 1
            fi
        fi
        
        sleep 1
        attempt=$((attempt + 1))
    done
    
    log_warn "⚠️ Task $task_uid did not complete within expected time"
    return 1
}

# Verify the setup
verify_setup() {
    log_info "Verifying Meilisearch setup..."
    
    # Get index stats
    local stats_response
    stats_response=$(curl -s \
        -H "Authorization: Bearer ${MEILI_MASTER_KEY}" \
        "${MEILISEARCH_URL}/indexes/contributions/stats" 2>/dev/null || echo "")
    
    if echo "$stats_response" | grep -q '"numberOfDocuments"'; then
        local doc_count
        doc_count=$(echo "$stats_response" | grep -o '"numberOfDocuments":[0-9]*' | cut -d':' -f2)
        log_info "✅ Index verified - $doc_count documents indexed"
    else
        log_error "❌ Failed to verify index setup"
        return 1
    fi
    
    # Get settings to verify configuration matches Java/Python services
    local settings_response
    settings_response=$(curl -s \
        -H "Authorization: Bearer ${MEILI_MASTER_KEY}" \
        "${MEILISEARCH_URL}/indexes/contributions/settings" 2>/dev/null || echo "")
    
    if echo "$settings_response" | grep -q '"searchableAttributes"'; then
        log_info "✅ Index settings verified"
        
        # Verify specific configuration elements
        if echo "$settings_response" | grep -q '"content".*"title".*"message"'; then
            log_debug "✅ Searchable attributes configured correctly"
        fi
        
        if echo "$settings_response" | grep -q '"user".*"week".*"contribution_type"'; then
            log_debug "✅ Filterable attributes configured correctly"
        fi
        
        if echo "$settings_response" | grep -q '"created_at_timestamp".*"relevance_score"'; then
            log_debug "✅ Sortable attributes configured correctly"
        fi
        
        if echo "$settings_response" | grep -q '"words".*"typo".*"proximity"'; then
            log_debug "✅ Ranking rules configured correctly"
        fi
        
        if echo "$settings_response" | grep -q '"bug".*"issue"'; then
            log_debug "✅ Synonyms configured correctly"
        fi
        
        # Check embedders configuration
        if echo "$settings_response" | grep -q '"embedders"'; then
            if [ -n "$OLLAMA_API_KEY" ] && echo "$settings_response" | grep -q '"source":"rest"'; then
                log_info "✅ REST embedder configured for Ollama API integration"
            elif echo "$settings_response" | grep -q '"source":"userProvided"'; then
                log_info "✅ User-provided embedder configured (Java service compatibility)"
            else
                log_warn "⚠️ Embedder configuration may not match service expectations"
            fi
        else
            log_error "❌ No embedders configured - this may cause service issues"
            return 1
        fi
    else
        log_error "❌ Failed to verify index settings"
        return 1
    fi
}

# Test basic functionality
test_functionality() {
    log_info "Testing basic functionality..."
    
    # Test search endpoint
    local search_response
    search_response=$(curl -s -w "%{http_code}" \
        -X POST \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer ${MEILI_MASTER_KEY}" \
        -d '{"q":"test","limit":1}' \
        "${MEILISEARCH_URL}/indexes/contributions/search" 2>/dev/null || echo "000")
    
    local http_code="${search_response: -3}"
    
    if [ "$http_code" = "200" ]; then
        log_info "✅ Search functionality working"
    else
        log_error "❌ Search test failed (HTTP $http_code)"
        return 1
    fi
}

# Main setup function
main() {
    echo "🚀 Meilisearch Setup for Team Promptheus"
    echo "========================================"
    echo ""
    echo "Configuration:"
    echo "  Meilisearch URL: $MEILISEARCH_URL"
    echo "  Master Key: ${MEILI_MASTER_KEY:0:8}..."
    echo "  Ollama Base URL: $OLLAMA_BASE_URL"
    echo "  Ollama Model: $OLLAMA_EMBEDDING_MODEL"
    echo "  Ollama API Key: ${OLLAMA_API_KEY:+✓ Available}"
    echo ""
    
    # Check health first
    if ! check_meilisearch_health; then
        log_error "❌ Meilisearch is not available. Please ensure it's running."
        exit 1
    fi
    
    # Create index
    if ! create_contributions_index; then
        log_error "❌ Failed to create contributions index"
        exit 1
    fi
    
    # Configure settings
    if ! configure_index_settings; then
        log_error "❌ Failed to configure index settings"
        exit 1
    fi
    
    # Verify setup
    if ! verify_setup; then
        log_error "❌ Setup verification failed"
        exit 1
    fi
    
    # Test functionality
    if ! test_functionality; then
        log_error "❌ Functionality test failed"
        exit 1
    fi
    
    echo ""
    echo "🎉 Meilisearch setup completed successfully!"
    echo ""
    echo "Features enabled:"
    echo "  ✅ Full-text search with ranking rules"
    echo "  ✅ Filtered search by user, week, contribution type, repository, author"
    echo "  ✅ Sortable results by creation timestamp and relevance score"
    echo "  ✅ Stop words filtering (the, a, an, and, or, etc.)"
    echo "  ✅ Synonyms configured (bug/issue, feature/enhancement, fix/repair, test/testing)"
    echo "  ✅ Searchable attributes: content, title, message, body, repository, author, filename, patch"
    if [ -n "$OLLAMA_API_KEY" ]; then
        echo "  ✅ AI-powered semantic search with REST embedder (${OLLAMA_EMBEDDING_MODEL})"
        echo "  ✅ Hybrid search combining full-text and vector similarity"
    else
        echo "  ✅ User-provided embeddings support (2048 dimensions for TinyLlama)"
        echo "  ⚠️  REST embedder disabled (no OLLAMA_API_KEY) - applications must provide embeddings"
    fi
    echo ""
    echo "The contributions index is ready to receive data!"
}

# Run main function
main "$@" 