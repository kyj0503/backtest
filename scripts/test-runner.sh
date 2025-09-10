#!/bin/bash
# Test execution scripts for standardized test strategy
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Docker image names
BACKEND_IMAGE="backtest-backend-test"
FRONTEND_IMAGE="backtest-frontend-test"
COMPOSE_TEST_FILE="compose/compose.test.yml"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Build Docker images
build_backend_image() {
    log_info "Building backend Docker image..."
    cd "$PROJECT_ROOT"
    docker build -t $BACKEND_IMAGE backend/
}

build_frontend_image() {
    log_info "Building frontend Docker image..."
    cd "$PROJECT_ROOT"
    docker build -t $FRONTEND_IMAGE frontend/
}

# Database management
start_test_database() {
    log_info "Starting test database..."
    cd "$PROJECT_ROOT"
    docker-compose -f $COMPOSE_TEST_FILE up -d
    
    # Wait for MySQL to be ready
    log_info "Waiting for MySQL to be ready..."
    timeout=60
    while ! docker exec mysql-test mysqladmin ping -h"localhost" --silent 2>/dev/null && [ $timeout -gt 0 ]; do
        sleep 2
        timeout=$((timeout-2))
    done
    
    if [ $timeout -le 0 ]; then
        log_error "MySQL failed to start within 60 seconds"
        exit 1
    fi
    
    log_success "Test database is ready!"
}

stop_test_database() {
    log_info "Stopping test database..."
    cd "$PROJECT_ROOT"
    docker-compose -f $COMPOSE_TEST_FILE down -v 2>/dev/null || true
    log_success "Test database stopped!"
}

# Function to run backend unit tests
run_unit_tests() {
    log_info "Running unit tests (fast feedback)..."
    build_backend_image
    docker run --rm $BACKEND_IMAGE python -m pytest tests/unit/ -v -m unit --tb=short -q
    log_success "Unit tests completed"
}

# Function to run backend integration tests
run_integration_tests() {
    log_info "Running integration tests (DB/routing validation)..."
    build_backend_image
    start_test_database
    
    # Run integration tests with database connection
    docker run --rm --network compose_test_network \
        -e DATABASE_URL="mysql+pymysql://test_user:test_password@mysql-test:3306/stock_data_cache" \
        -e REDIS_URL="redis://redis-test:6379" \
        $BACKEND_IMAGE python -m pytest tests/integration/ -v -m integration --tb=short -q
    
    stop_test_database
    log_success "Integration tests completed"
}

# Function to run E2E tests
run_e2e_tests() {
    log_info "Running E2E tests (golden path validation)..."
    build_backend_image
    start_test_database
    
    # Run E2E tests with full environment
    docker run --rm --network compose_test_network \
        -e DATABASE_URL="mysql+pymysql://test_user:test_password@mysql-test:3306/stock_data_cache" \
        -e REDIS_URL="redis://redis-test:6379" \
        $BACKEND_IMAGE python -m pytest tests/e2e/ -v -m e2e --tb=short -q
    
    stop_test_database
    log_success "E2E tests completed"
}

# Function to run frontend tests
run_frontend_tests() {
    log_info "Running frontend tests..."
    build_frontend_image
    docker run --rm $FRONTEND_IMAGE npm test -- --run
    log_success "Frontend tests completed"
}

# Function to run coverage
run_coverage() {
    log_info "Running tests with coverage..."
    build_backend_image
    start_test_database
    
    # Run coverage with database for integration tests
    docker run --rm --network compose_test_network \
        -e DATABASE_URL="mysql+pymysql://test_user:test_password@mysql-test:3306/stock_data_cache" \
        -e REDIS_URL="redis://redis-test:6379" \
        $BACKEND_IMAGE python -m pytest --cov=app --cov-report=term-missing --cov-report=html
    
    stop_test_database
    log_success "Coverage report generated"
}

# Function to run linting
run_lint() {
    log_info "Running linting and type checks..."
    
    # Backend linting
    build_backend_image
    log_info "Checking backend code formatting..."
    docker run --rm $BACKEND_IMAGE python -m black --check app/ tests/ || (log_error "Black formatting check failed" && exit 1)
    
    log_info "Checking backend import sorting..."
    docker run --rm $BACKEND_IMAGE python -m isort --check-only app/ tests/ || (log_error "isort check failed" && exit 1)
    
    # Frontend linting
    log_info "Running frontend linting..."
    build_frontend_image
    docker run --rm $FRONTEND_IMAGE npm run lint || (log_error "Frontend linting failed" && exit 1)
    
    log_success "All linting checks passed"
}

# Cleanup function
cleanup() {
    log_warning "Cleaning up test environment..."
    stop_test_database 2>/dev/null || true
}

# Trap cleanup on script exit
trap cleanup EXIT

# Main execution based on arguments
case "${1:-help}" in
    "unit")
        run_unit_tests
        ;;
    "integration")
        run_integration_tests
        ;;
    "e2e")
        run_e2e_tests
        ;;
    "frontend")
        run_frontend_tests
        ;;
    "all")
        run_lint
        run_unit_tests
        run_integration_tests
        run_frontend_tests
        run_e2e_tests
        ;;
    "coverage")
        run_coverage
        ;;
    "lint")
        run_lint
        ;;
    "ci")
        log_info "Running full CI pipeline simulation..."
        run_lint
        run_unit_tests
        run_integration_tests
        run_frontend_tests
        
        # Health check similar to verify-before-commit.sh
        log_info "Building and health-checking backend..."
        build_backend_image
        cid=$(docker run -d -p 8001:8000 --rm $BACKEND_IMAGE)
        cleanup_health_check() { docker stop "$cid" >/dev/null 2>&1 || true; }
        trap cleanup_health_check EXIT
        
        # Wait for server health
        for i in {1..30}; do
            if curl -fsS http://localhost:8001/health >/dev/null 2>&1; then
                log_success "Backend health check passed"
                break
            fi
            sleep 1
            if [ "$i" -eq 30 ]; then
                log_error "Backend health check failed - server not responsive"
                exit 1
            fi
        done
        
        docker stop "$cid" >/dev/null 2>&1 || true
        run_e2e_tests
        log_success "Full CI pipeline completed successfully"
        ;;
    "help"|*)
        echo "Usage: $0 {unit|integration|e2e|frontend|all|coverage|lint|ci|help}"
        echo ""
        echo "Test execution modes:"
        echo "  unit        - Run unit tests only (fast feedback)"
        echo "  integration - Run integration tests (DB/routing validation)"
        echo "  e2e         - Run E2E tests (golden path validation)"
        echo "  frontend    - Run frontend tests"
        echo "  all         - Run all tests"
        echo "  coverage    - Run tests with coverage report"
        echo "  lint        - Run linting and type checks"
        echo "  ci          - Run full CI pipeline simulation"
        echo "  help        - Show this help message"
        ;;
esac
