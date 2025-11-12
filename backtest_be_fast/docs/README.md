# Backend Technical Documentation

This directory contains technical documentation for backend system architecture, core logic, and troubleshooting guides.

## Directory Structure

- analysis/ - Code quality analysis and findings
- architecture/ - System architecture and design documents
- performance/ - Performance optimization documentation
- refactoring/ - Code refactoring documentation
- testing/ - Test strategies and guides
- troubleshooting/ - Common issues and solutions

## Architecture

- [Backtest Logic Architecture](./architecture/backtest_logic.md)
  - Role of backtesting.py library
  - Custom implementation boundaries
  - Currency conversion and dynamic strategy generation

- [Date Calculation Architecture (Nth Weekday)](./architecture/date_calculation.md)
  - Nth weekday calculation logic for DCA and rebalancing
  - Edge case handling (months without 5th week)

- [Strategy Implementation Guide](./architecture/strategies.md)
  - Trading strategies (SMA, RSI, MACD, etc.)
  - Position management patterns

## Performance

- [Optimization Summary](./performance/optimization-summary.md)
  - N+1 query pattern optimization (10x speedup)
  - Parallel data loading improvements
  - Code quality metrics before/after

## Refactoring

- [Portfolio Function Analysis](./refactoring/portfolio-function-analysis.md)
  - Structural analysis of calculate_dca_portfolio_returns()
  - Complexity metrics and decomposition strategy

- [Function Extraction Specifications](./refactoring/function-extraction-specs.md)
  - Detailed specs for 8 extracted helper functions
  - Input/output contracts and responsibilities

- [Function Structure Diagram](./refactoring/function-structure-diagram.md)
  - Visual representation of function relationships
  - Data flow diagrams

## Analysis

- [Backend Analysis Index](./analysis/backend-analysis-index.md)
  - Overview of all analysis documents
  - Quick navigation to specific findings

- [Code Duplication Report](./analysis/code-duplication-index.md)
  - Duplicate function locations and consolidation plan
  - Data loading pattern analysis

- [Logging Gaps Analysis](./analysis/logging-gaps-detailed.md)
  - Missing logging points identification
  - Operational visibility improvements

- [Error Format Analysis](./analysis/error-format-analysis.md)
  - Error message consistency issues
  - Standardization recommendations

## Troubleshooting

- [Async/Sync Boundary Issues (Race Condition)](./troubleshooting/race_condition.md)
  - First-run backtest corruption causes
  - Proper asyncio.to_thread() usage

- [DB Transaction Isolation Issues](./troubleshooting/transaction_isolation.md)
  - Post-save query failure causes
  - Transaction snapshot refresh patterns

- [Performance Optimization Guide](./troubleshooting/performance.md)
  - Performance bottleneck analysis
  - Applied optimization strategies
  - Future improvement roadmap

## Testing

- [Testing Documentation](./testing/README.md)
  - Test strategies and execution methods
  - Fixtures and test data management

## Quick Reference

For quick lookups:
- Performance metrics: performance/optimization-summary.md
- Common errors: analysis/error-format-analysis.md
- Code duplication: analysis/code-duplication-reference.txt
- Function extraction: refactoring/function-extraction-guide.txt
