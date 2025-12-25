#!/bin/bash
# Quick Docker test script for Oura MCP Server

set -e

echo "🐳 Oura MCP Server - Docker Test Script"
echo "========================================"
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker."
    exit 1
fi
echo "✅ Docker found: $(docker --version)"

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose."
    exit 1
fi
echo "✅ Docker Compose found: $(docker-compose --version)"

if [ -z "$OURA_ACCESS_TOKEN" ]; then
    echo "❌ OURA_ACCESS_TOKEN not set."
    echo "   Please set it: export OURA_ACCESS_TOKEN='your_token'"
    exit 1
fi
echo "✅ OURA_ACCESS_TOKEN is set"

echo ""
echo "Building Docker image..."
docker-compose build

echo ""
echo "Starting container..."
docker-compose up -d

echo ""
echo "Waiting for container to be healthy (30s timeout)..."
for i in {1..30}; do
    if docker inspect --format='{{.State.Health.Status}}' oura-mcp-server 2>/dev/null | grep -q "healthy"; then
        echo "✅ Container is healthy!"
        break
    fi
    echo -n "."
    sleep 1
done

echo ""
echo ""
echo "Container status:"
docker ps --filter name=oura-mcp-server

echo ""
echo "Testing API connection..."
if docker-compose exec -T oura-mcp python tests/test_api.py 2>&1 | grep -q "All tests passed"; then
    echo "✅ API tests passed"
else
    echo "⚠️  API tests may have issues (check logs)"
fi

echo ""
echo "Recent logs (last 20 lines):"
docker-compose logs --tail=20 oura-mcp

echo ""
echo "========================================"
echo "✅ Docker test complete!"
echo ""
echo "Useful commands:"
echo "  make logs      - View logs"
echo "  make shell     - Open shell in container"
echo "  make down      - Stop container"
echo "  make test      - Run full test suite"
echo ""
echo "Container is running. Press Ctrl+C to view live logs, or run 'make down' to stop."

# Follow logs
docker-compose logs -f
