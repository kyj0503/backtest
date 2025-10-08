# Project Overview

This project is a web-based backtesting application for financial trading strategies. It consists of a Python FastAPI backend and a React frontend.

## Backend (`backtest_be_fast`)

The backend is a FastAPI application that provides an API for running backtests, managing data, and handling user authentication. It uses `yfinance` to fetch financial data, `backtesting.py` to run the backtests, and `SQLAlchemy` to interact with a database.

### Key Technologies

*   **Framework:** FastAPI
*   **Data:** yfinance, Pandas
*   **Backtesting:** backtesting.py
*   **Database:** SQLAlchemy

## Frontend (`backtest_fe`)

The frontend is a React application built with Vite. It provides a user interface for creating and running backtests, visualizing results, and managing portfolios. It uses Tailwind CSS for styling and Recharts for charting.

### Key Technologies

*   **Framework:** React
*   **Build Tool:** Vite
*   **Language:** TypeScript
*   **Styling:** Tailwind CSS
*   **Charting:** Recharts

# Building and Running

The entire application can be run using Docker Compose.

## Development

To run the application in development mode, use the following command:

```bash
docker compose -f compose.dev.yaml up -d --build
```

This will start both the backend and frontend services with hot-reloading enabled.

*   **Backend:** Available at `http://localhost:8000`
*   **Frontend:** Available at `http://localhost:5173`

## Production

To run the application in production mode, use the following command:

```bash
docker compose -f compose.server.yaml up -d --build
```

# Development Conventions

## Backend

*   **Code Style:** The project uses `black` for code formatting and `isort` for import sorting.
*   **Testing:** Tests are written with `pytest`. Run tests with the `pytest` command.

## Frontend

*   **Code Style:** The project uses `eslint` for linting. Run the linter with `npm run lint`.
*   **Testing:** Tests are written with `vitest`. Run tests with `npm run test`.
