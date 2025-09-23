#!/bin/bash

# Production deployment script for backtest platform
# This script should be run on the production server

set -e

# Configuration
DEPLOY_DIR="/opt/backtest"
GITHUB_REPOSITORY="capstone-backtest/backtest"
COMPOSE_FILE="compose/compose.prod.yaml"

echo "Starting deployment..."

# Ensure we're in the correct directory
cd $DEPLOY_DIR

# Create necessary directories
mkdir -p logs
mkdir -p nginx/ssl
mkdir -p monitoring

# Backup current deployment (optional)
if [ -f "$COMPOSE_FILE" ]; then
    echo "Creating backup..."
    docker compose -f $COMPOSE_FILE ps > logs/deployment-$(date +%Y%m%d-%H%M%S).log
fi

# Pull latest code
echo "Pulling latest code..."
git pull origin main

# Pull latest images
echo "Pulling latest images..."
docker pull ghcr.io/$GITHUB_REPOSITORY/backtest-be-fast:latest
docker pull ghcr.io/$GITHUB_REPOSITORY/backtest-be-spring:latest
docker pull ghcr.io/$GITHUB_REPOSITORY/backtest-fe:latest

# Stop existing services
echo "Stopping existing services..."
docker compose -f $COMPOSE_FILE down --remove-orphans

# Start services
echo "Starting services..."
docker compose -f $COMPOSE_FILE up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 30

# Health checks
echo "Running health checks..."

# Check FastAPI
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "FastAPI is healthy"
else
    echo "FastAPI health check failed"
    exit 1
fi

# Check Spring Boot
if curl -f http://localhost:8080/actuator/health > /dev/null 2>&1; then
    echo "Spring Boot is healthy"
else
    echo "Spring Boot health check failed"
    exit 1
fi

# Check Frontend
if curl -f http://localhost/ > /dev/null 2>&1; then
    echo "Frontend is healthy"
else
    echo "Frontend health check failed"
    exit 1
fi

# Cleanup old images
echo "Cleaning up old images..."
docker system prune -f

# Show status
echo "Deployment status:"
docker compose -f $COMPOSE_FILE ps

echo "Deployment completed successfully!"
echo "Application is available at: http://$(hostname -I | awk '{print $1}')"