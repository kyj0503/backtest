# Backtest Project Makefile
# Unified Test Strategy Commands

.PHONY: help test test-unit test-integration test-e2e test-all lint build clean coverage

# Default target
help:
	@echo "Backtest Project - Test Commands"
	@echo ""
	@echo "Available targets:"
	@echo "  test           - Run unit tests (default, fast feedback)"
	@echo "  test-unit      - Run unit tests only"
	@echo "  test-integration - Run integration tests (with database)"
	@echo "  test-e2e       - Run end-to-end tests"
	@echo "  test-all       - Run all test suites"
	@echo "  coverage       - Generate coverage report"
	@echo "  lint           - Run code quality checks"
	@echo "  build          - Build development environment"
	@echo "  ci             - Run full CI pipeline simulation"
	@echo "  clean          - Clean up containers and cache"

# Test execution using unified test-runner.sh script
test:
	@./scripts/test-runner.sh unit

test-unit:
	@./scripts/test-runner.sh unit

test-integration:
	@./scripts/test-runner.sh integration

test-e2e:
	@./scripts/test-runner.sh e2e

test-all:
	@./scripts/test-runner.sh all

coverage:
	@./scripts/test-runner.sh coverage

lint:
	@./scripts/test-runner.sh lint

# Development environment
build:
	@docker compose -f compose.yml -f compose/compose.dev.yml build

dev-up:
	@docker compose -f compose.yml -f compose/compose.dev.yml up --build

dev-down:
	@docker compose -f compose.yml -f compose/compose.dev.yml down

# CI pipeline simulation (replaces verify-before-commit.sh functionality)
ci:
	@./scripts/test-runner.sh ci

# Clean up
clean:
	@docker system prune -f
	@docker compose -f compose.yml -f compose/compose.dev.yml down --volumes --remove-orphans
	@docker compose -f compose/compose.test.yml down --volumes --remove-orphans
