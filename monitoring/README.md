# Monitoring System Documentation

This directory contains the independent monitoring stack for the Backtest Service, featuring **Prometheus** (data collection) and **Grafana** (visualization).

## 📂 Structure

- **`compose.dev.yaml`**: Development setup (Standard ports: 3000, 9090)
- **`compose.prod.yaml`**: Production setup (Configurable ports to avoid conflicts)
- **`prometheus.yml`**: Prometheus scrape configuration (configured for `host.docker.internal`)
- **`custom_dashboard.json`**: Pre-configured Grafana dashboard for FastAPI
- **`custom_metrics.py`**: (Located in Backend) Defines business logic metrics

---

## 🚀 How to Run

### Development Environment
Standard setup for local development.

```bash
docker compose -f compose.dev.yaml up -d
```
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090

### Production (Home Server)
Use this if `port 3000` is already taken or for long-running instances.

1. **Configure Environment (Optional)**
   Copy `.env.example` to `.env` and set custom ports/passwords.
   ```bash
   cp .env.example .env
   vi .env
   ```

2. **Run Stack**
   ```bash
   docker compose -f compose.prod.yaml up -d
   ```
   (Default ports: **Grafana 3001**, **Prometheus 9091** unless changed in .env)

---

## 📊 Metrics Overview

### 1. System Metrics (Standard)
Collected via `prometheus-fastapi-instrumentator`.
- **RPS (Requests Per Second)**
- **Latency (p50, p95, p99)**
- **Error Rates (4xx, 5xx)**
- **CPU / Memory Usage**

### 2. Business Metrics (Custom)
Implemented in `app/services/portfolio_manager_service.py`.
- **`backtest_execution_total`**: Count of executed backtests (Success/Failure status).
- **`ticker_popularity_total`**: Count of requested tickers (e.g., TSLA, AAPL).
- **`backtest_processing_seconds`**: Pure calculation time histogram.

---

## 🔧 Maintenance

### Persistence
- Grafana data (dashboards, users) is persisted in the `grafana_data` volume.
- Prometheus data is persisted in the `prometheus_data` volume.
- **Note:** If you set `GF_SECURITY_ADMIN_PASSWORD` in `compose.yaml`, it will overwrite the DB password on every restart. For production, remove that line after first login.

### Adding New Metrics
1. Define metric in `app/monitoring/custom_metrics.py`.
2. Instrument code in services.
3. Update `custom_dashboard.json` or edit in Grafana UI.
