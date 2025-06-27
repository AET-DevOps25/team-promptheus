#!/bin/bash

# Team Promptheus Deployment Validation Script
# This script validates that all components are running correctly after deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
NAMESPACE="team-promptheus"
RELEASE_NAME="team-promptheus"
TIMEOUT=300

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to wait for pods to be ready
wait_for_pods() {
    local namespace=$1
    local label_selector=$2
    local timeout=${3:-300}

    print_status "Waiting for pods with selector '$label_selector' to be ready..."

    if kubectl wait --for=condition=ready pod \
        -l "$label_selector" \
        -n "$namespace" \
        --timeout="${timeout}s" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to check pod health
check_pods() {
    print_header "Checking Pod Health"

    local failed=0

    # Get all pods in namespace
    local pods=$(kubectl get pods -n "$NAMESPACE" -o json | jq -r '.items[].metadata.name')

    if [[ -z "$pods" ]]; then
        print_error "No pods found in namespace $NAMESPACE"
        return 1
    fi

    for pod in $pods; do
        local status=$(kubectl get pod "$pod" -n "$NAMESPACE" -o jsonpath='{.status.phase}')
        local ready=$(kubectl get pod "$pod" -n "$NAMESPACE" -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}')

        if [[ "$status" == "Running" && "$ready" == "True" ]]; then
            print_success "✅ $pod: Running and Ready"
        else
            print_error "❌ $pod: Status=$status, Ready=$ready"

            # Show recent events for failed pods
            echo "Recent events for $pod:"
            kubectl get events --field-selector involvedObject.name="$pod" -n "$NAMESPACE" --sort-by='.lastTimestamp' | tail -5
            echo ""

            failed=$((failed + 1))
        fi
    done

    if [[ $failed -eq 0 ]]; then
        print_success "All pods are healthy"
        return 0
    else
        print_error "$failed pods are not healthy"
        return 1
    fi
}

# Function to check services
check_services() {
    print_header "Checking Service Health"

    local services=("client-service" "server-service" "genai-service" "search-service" "collector-service" "meilisearch-service" "monitoring-service")
    local failed=0

    for service in "${services[@]}"; do
        if kubectl get service "$service" -n "$NAMESPACE" >/dev/null 2>&1; then
            local endpoints=$(kubectl get endpoints "$service" -n "$NAMESPACE" -o jsonpath='{.subsets[*].addresses[*].ip}' | wc -w)
            if [[ $endpoints -gt 0 ]]; then
                print_success "✅ $service: $endpoints endpoint(s)"
            else
                print_error "❌ $service: No endpoints available"
                failed=$((failed + 1))
            fi
        else
            print_warning "⚠️  $service: Service not found (may be disabled)"
        fi
    done

    # Check PostgreSQL service
    if kubectl get service postgres -n "$NAMESPACE" >/dev/null 2>&1; then
        local pg_endpoints=$(kubectl get endpoints postgres -n "$NAMESPACE" -o jsonpath='{.subsets[*].addresses[*].ip}' | wc -w)
        if [[ $pg_endpoints -gt 0 ]]; then
            print_success "✅ postgres: $pg_endpoints endpoint(s)"
        else
            print_error "❌ postgres: No endpoints available"
            failed=$((failed + 1))
        fi
    elif kubectl get cluster postgres-cluster -n "$NAMESPACE" >/dev/null 2>&1; then
        print_success "✅ postgres-cluster: CloudNativePG cluster found"
    else
        print_error "❌ PostgreSQL: Neither traditional service nor CloudNativePG cluster found"
        failed=$((failed + 1))
    fi

    if [[ $failed -eq 0 ]]; then
        print_success "All services are healthy"
        return 0
    else
        print_error "$failed services have issues"
        return 1
    fi
}

# Function to check database connectivity
check_database() {
    print_header "Checking Database Connectivity"

    # Try to find a server pod to test database connection
    local server_pod=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/component=server -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

    if [[ -z "$server_pod" ]]; then
        print_warning "No server pod found, skipping database connectivity test"
        return 0
    fi

    print_status "Testing database connection from $server_pod..."

    # Test database connection
    if kubectl exec "$server_pod" -n "$NAMESPACE" -- sh -c 'echo "SELECT 1;" | timeout 10 psql $DATABASE_URL -t' >/dev/null 2>&1; then
        print_success "✅ Database connection successful"
        return 0
    else
        print_error "❌ Database connection failed"

        # Try to get more details about the database
        print_status "Database connection details:"
        kubectl exec "$server_pod" -n "$NAMESPACE" -- env | grep -E "(POSTGRES|DATABASE)" || true

        return 1
    fi
}

# Function to check MeiliSearch
check_meilisearch() {
    print_header "Checking MeiliSearch"

    local meili_pod=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/component=meilisearch -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

    if [[ -z "$meili_pod" ]]; then
        print_warning "No MeiliSearch pod found, skipping MeiliSearch test"
        return 0
    fi

    print_status "Testing MeiliSearch health from $meili_pod..."

    if kubectl exec "$meili_pod" -n "$NAMESPACE" -- curl -s http://localhost:7700/health >/dev/null 2>&1; then
        print_success "✅ MeiliSearch is healthy"
        return 0
    else
        print_error "❌ MeiliSearch health check failed"
        return 1
    fi
}

# Function to check ingress
check_ingress() {
    print_header "Checking Ingress"

    if kubectl get ingress -n "$NAMESPACE" >/dev/null 2>&1; then
        local ingress_name=$(kubectl get ingress -n "$NAMESPACE" -o jsonpath='{.items[0].metadata.name}')
        local hosts=$(kubectl get ingress "$ingress_name" -n "$NAMESPACE" -o jsonpath='{.spec.rules[*].host}')

        print_success "✅ Ingress '$ingress_name' configured for hosts: $hosts"

        # Check if ingress has an IP/hostname
        local address=$(kubectl get ingress "$ingress_name" -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}{.status.loadBalancer.ingress[0].hostname}')
        if [[ -n "$address" ]]; then
            print_success "✅ Ingress address: $address"
        else
            print_warning "⚠️  Ingress has no external address yet"
        fi

        return 0
    else
        print_warning "⚠️  No ingress found (may be disabled)"
        return 0
    fi
}

# Function to check monitoring
check_monitoring() {
    print_header "Checking Monitoring"

    # Check if ServiceMonitors exist
    if command_exists kubectl && kubectl get crd servicemonitors.monitoring.coreos.com >/dev/null 2>&1; then
        local monitors=$(kubectl get servicemonitor -n "$NAMESPACE" 2>/dev/null | wc -l)
        if [[ $monitors -gt 1 ]]; then  # More than 1 (header line)
            print_success "✅ ServiceMonitors found: $((monitors - 1))"
        else
            print_warning "⚠️  No ServiceMonitors found"
        fi
    else
        print_warning "⚠️  Prometheus Operator not installed, skipping ServiceMonitor check"
    fi

    # Check if monitoring service exists
    if kubectl get service monitoring -n "$NAMESPACE" >/dev/null 2>&1; then
        print_success "✅ Monitoring service found"
    else
        print_warning "⚠️  Monitoring service not found (may be disabled)"
    fi

    return 0
}

# Function to check autoscaling
check_autoscaling() {
    print_header "Checking Autoscaling"

    local hpas=$(kubectl get hpa -n "$NAMESPACE" 2>/dev/null | wc -l)
    if [[ $hpas -gt 1 ]]; then  # More than 1 (header line)
        print_success "✅ HorizontalPodAutoscalers found: $((hpas - 1))"

        # Show HPA status
        kubectl get hpa -n "$NAMESPACE" 2>/dev/null | while read -r line; do
            if [[ "$line" != "NAME"* ]]; then
                print_status "  $line"
            fi
        done
    else
        print_status "ℹ️  No HorizontalPodAutoscalers found (autoscaling may be disabled)"
    fi

    return 0
}

# Function to run connectivity tests
run_connectivity_tests() {
    print_header "Running Connectivity Tests"

    # Test internal service connectivity
    local client_pod=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/component=client -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

    if [[ -n "$client_pod" ]]; then
        print_status "Testing internal service connectivity from $client_pod..."

        # Test server connectivity
        if kubectl exec "$client_pod" -n "$NAMESPACE" -- curl -s -f http://server:8000/health >/dev/null 2>&1; then
            print_success "✅ Client → Server connectivity"
        else
            print_error "❌ Client → Server connectivity failed"
        fi

        # Test MeiliSearch connectivity
        if kubectl exec "$client_pod" -n "$NAMESPACE" -- curl -s -f http://meilisearch:7700/health >/dev/null 2>&1; then
            print_success "✅ Client → MeiliSearch connectivity"
        else
            print_error "❌ Client → MeiliSearch connectivity failed"
        fi
    else
        print_warning "No client pod found, skipping connectivity tests"
    fi
}

# Function to show resource usage
show_resource_usage() {
    print_header "Resource Usage Summary"

    print_status "CPU and Memory usage by pod:"
    if command_exists kubectl && kubectl top pods -n "$NAMESPACE" >/dev/null 2>&1; then
        kubectl top pods -n "$NAMESPACE" | while read -r line; do
            print_status "  $line"
        done
    else
        print_warning "Metrics server not available or kubectl top not working"
    fi

    echo ""
    print_status "Storage usage:"
    kubectl get pvc -n "$NAMESPACE" 2>/dev/null | while read -r line; do
        print_status "  $line"
    done
}

# Function to show summary
show_summary() {
    print_header "Validation Summary"

    local total_checks=7
    local passed_checks=0

    echo "Validation Results:"

    if check_pods; then
        echo "✅ Pod Health: PASSED"
        passed_checks=$((passed_checks + 1))
    else
        echo "❌ Pod Health: FAILED"
    fi

    if check_services; then
        echo "✅ Service Health: PASSED"
        passed_checks=$((passed_checks + 1))
    else
        echo "❌ Service Health: FAILED"
    fi

    if check_database; then
        echo "✅ Database Connectivity: PASSED"
        passed_checks=$((passed_checks + 1))
    else
        echo "❌ Database Connectivity: FAILED"
    fi

    if check_meilisearch; then
        echo "✅ MeiliSearch Health: PASSED"
        passed_checks=$((passed_checks + 1))
    else
        echo "❌ MeiliSearch Health: FAILED"
    fi

    if check_ingress; then
        echo "✅ Ingress Configuration: PASSED"
        passed_checks=$((passed_checks + 1))
    else
        echo "❌ Ingress Configuration: FAILED"
    fi

    if check_monitoring; then
        echo "✅ Monitoring Setup: PASSED"
        passed_checks=$((passed_checks + 1))
    else
        echo "❌ Monitoring Setup: FAILED"
    fi

    if check_autoscaling; then
        echo "✅ Autoscaling Configuration: PASSED"
        passed_checks=$((passed_checks + 1))
    else
        echo "❌ Autoscaling Configuration: FAILED"
    fi

    echo ""
    echo "Overall Result: $passed_checks/$total_checks checks passed"

    if [[ $passed_checks -eq $total_checks ]]; then
        print_success "🎉 All validations passed! Your deployment is healthy."
        return 0
    else
        print_error "⚠️  Some validations failed. Please check the issues above."
        return 1
    fi
}

# Function to show usage
show_usage() {
    echo "Team Promptheus Deployment Validation Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -n, --namespace NAME     Kubernetes namespace [default: team-promptheus]"
    echo "  -r, --release NAME       Helm release name [default: team-promptheus]"
    echo "  -t, --timeout SECONDS    Timeout for operations [default: 300]"
    echo "  -q, --quick              Run quick validation (skip connectivity tests)"
    echo "  -v, --verbose            Verbose output"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Validate default deployment"
    echo "  $0 -n team-promptheus-dev            # Validate development namespace"
    echo "  $0 -q                                # Quick validation"
}

# Parse command line arguments
QUICK_MODE=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -r|--release)
            RELEASE_NAME="$2"
            shift 2
            ;;
        -t|--timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        -q|--quick)
            QUICK_MODE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Check prerequisites
if ! command_exists kubectl; then
    print_error "kubectl is not installed or not in PATH"
    exit 1
fi

if ! command_exists jq; then
    print_warning "jq is not installed. Some features may not work properly."
fi

# Check if namespace exists
if ! kubectl get namespace "$NAMESPACE" >/dev/null 2>&1; then
    print_error "Namespace '$NAMESPACE' does not exist"
    exit 1
fi

# Main execution
print_header "Team Promptheus Deployment Validation - Namespace: $NAMESPACE"

# Wait for pods to be ready first
print_status "Waiting for pods to be ready (timeout: ${TIMEOUT}s)..."
if ! wait_for_pods "$NAMESPACE" "app.kubernetes.io/instance=$RELEASE_NAME" "$TIMEOUT"; then
    print_warning "Some pods may still be starting up. Continuing with validation..."
fi

# Run all validations
if [[ "$QUICK_MODE" == "false" ]]; then
    run_connectivity_tests
    show_resource_usage
fi

# Show final summary
if show_summary; then
    exit 0
else
    exit 1
fi
