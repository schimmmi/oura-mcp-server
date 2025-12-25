# Oura MCP Server - Dockerfile
# Multi-stage build for optimal image size

# Build stage
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Create non-root user for security
RUN useradd -m -u 1000 oura && \
    chown -R oura:oura /app

# Copy Python dependencies from builder
COPY --from=builder --chown=oura:oura /root/.local /home/oura/.local

# Copy application code
COPY --chown=oura:oura . .

# Add local Python packages to PATH
ENV PATH=/home/oura/.local/bin:$PATH
ENV PYTHONPATH=/app/src:$PYTHONPATH

# Switch to non-root user
USER oura

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.path.insert(0, '/app/src'); from oura_mcp.utils.config import get_config; get_config()" || exit 1

# Default command
CMD ["python", "main.py"]

# Labels
LABEL maintainer="Oura MCP Server"
LABEL version="0.2.0"
LABEL description="Model Context Protocol server for Oura Ring health data"
