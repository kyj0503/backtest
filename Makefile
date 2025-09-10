# Backtest Project Makefile
# Test Strategy Implementation

.PHONY: help install test test-unit test-integration test-e2e test-all lint build clean coverage

# Default target
help:
	@echo "Backtest Project - Test Strategy Commands"
	@echo ""
	@echo "Available targets:"
	@echo "  install         - Install dependencies"
	@echo "  lint           - Run linting and type checks"
	@echo "  test-unit      - Run unit tests only (fast)"
	@echo "  test-integration - Run integration tests"
	@echo "  test-e2e       - Run end-to-end tests"
	@echo "  test-all       - Run all tests"
	@echo "  coverage       - Run tests with coverage report"
	@echo "  build          - Build Docker images"
	@echo "  clean          - Clean up containers and cache"

# Backend targets
install-backend:
	docker build -t backtest-backend-dev ./backend

lint-backend:
	docker build -t backtest-backend-dev ./backend
	docker run --rm backtest-backend-dev python -m black --check app/ tests/
	docker run --rm backtest-backend-dev python -m isort --check-only app/ tests/

test-unit-backend:
	docker build -t backtest-backend-test --build-arg RUN_TESTS=false ./backend
	docker run --rm backtest-backend-test python -m pytest tests/unit/ -v -m unit --tb=short

test-integration-backend:
	docker build -t backtest-backend-test --build-arg RUN_TESTS=false ./backend
	docker run --rm backtest-backend-test python -m pytest tests/integration/ -v -m integration --tb=short

test-e2e-backend:
	docker build -t backtest-backend-test --build-arg RUN_TESTS=false ./backend
	docker run --rm backtest-backend-test python -m pytest tests/e2e/ -v -m e2e --tb=short

test-all-backend:
	docker build -t backtest-backend-test --build-arg RUN_TESTS=false ./backend
	docker run --rm backtest-backend-test python -m pytest tests/ -v --tb=short

coverage-backend:
	docker build -t backtest-backend-test --build-arg RUN_TESTS=false ./backend
	docker run --rm -v $(PWD)/backend/htmlcov:/app/htmlcov backtest-backend-test python -m pytest tests/ --cov=app --cov-report=term-missing --cov-report=html

# Frontend targets
install-frontend:
	docker build -t backtest-frontend-dev ./frontend

lint-frontend:
	docker build -t backtest-frontend-dev ./frontend
	docker run --rm backtest-frontend-dev npm run lint

test-frontend:
	docker build -t backtest-frontend-test --build-arg RUN_TESTS=false ./frontend
	docker run --rm backtest-frontend-test npm test -- --run

# Combined targets
install: install-backend install-frontend

lint: lint-backend lint-frontend

test-unit: test-unit-backend
	@echo "Unit tests completed"

test-integration: test-integration-backend
	@echo "Integration tests completed"

test-e2e: test-e2e-backend
	@echo "E2E tests completed"

test-all: test-all-backend test-frontend
	@echo "All tests completed"

coverage: coverage-backend
	@echo "Coverage report generated in backend/htmlcov/"

# Docker targets
build:
	docker compose -f compose.yml -f compose/compose.dev.yml build

build-prod:
	docker build -t backtest-backend:latest ./backend
	docker build -t backtest-frontend:latest ./frontend

# Development environment
dev-up:
	docker compose -f compose.yml -f compose/compose.dev.yml up --build

dev-down:
	docker compose -f compose.yml -f compose/compose.dev.yml down

# Clean up
clean:
	docker system prune -f
	docker compose -f compose.yml -f compose/compose.dev.yml down --volumes --remove-orphans

# CI pipeline simulation
ci-test: lint test-unit test-integration build test-e2e
	@echo "CI pipeline simulation completed"
