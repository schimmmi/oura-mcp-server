.PHONY: help build up down logs restart test clean shell health

# Default target
help:
	@echo "Oura MCP Server - Docker Commands"
	@echo ""
	@echo "Usage:"
	@echo "  make build        - Build Docker image"
	@echo "  make up           - Start containers"
	@echo "  make down         - Stop containers"
	@echo "  make logs         - View logs"
	@echo "  make restart      - Restart containers"
	@echo "  make test         - Run tests in container"
	@echo "  make shell        - Open shell in container"
	@echo "  make health       - Check container health"
	@echo "  make clean        - Remove containers and images"
	@echo ""
	@echo "Prerequisites:"
	@echo "  - Docker and Docker Compose installed"
	@echo "  - OURA_ACCESS_TOKEN environment variable set"

# Build Docker image
build:
	@echo "Building Docker image..."
	docker-compose build

# Start containers
up:
	@echo "Starting containers..."
	docker-compose up -d
	@echo "Server started. Use 'make logs' to view logs."

# Stop containers
down:
	@echo "Stopping containers..."
	docker-compose down

# View logs
logs:
	docker-compose logs -f

# Restart containers
restart: down up

# Run tests
test:
	@echo "Running tests in container..."
	docker-compose exec oura-mcp python tests/test_api.py
	docker-compose exec oura-mcp python tests/test_advanced_features.py

# Open shell in container
shell:
	docker-compose exec oura-mcp bash

# Check health
health:
	@echo "Checking container health..."
	@docker inspect --format='{{.State.Health.Status}}' oura-mcp-server || echo "Container not running"

# Clean up
clean:
	@echo "Cleaning up..."
	docker-compose down -v
	docker rmi oura-mcp-server:latest 2>/dev/null || true
	@echo "Cleanup complete."

# Quick check
status:
	@echo "Container status:"
	@docker ps -a --filter name=oura-mcp-server
	@echo ""
	@echo "Image info:"
	@docker images oura-mcp-server
