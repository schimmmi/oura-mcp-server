# Docker Deployment Guide 🐳

Run the Oura MCP Server in a Docker container for easy deployment and isolation.

---

## 🚀 Quick Start

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- Oura Access Token

### 1. Build and Run with Docker Compose (Recommended)

```bash
# Set your Oura token
export OURA_ACCESS_TOKEN="your_token_here"

# Build and start
docker-compose up -d

# View logs
docker-compose logs -f oura-mcp

# Stop
docker-compose down
```

### 2. Build and Run with Docker CLI

```bash
# Build image
docker build -t oura-mcp-server:latest .

# Run container
docker run -d \
  --name oura-mcp-server \
  -e OURA_ACCESS_TOKEN="your_token_here" \
  -v $(pwd)/config:/app/config:ro \
  -v $(pwd)/logs:/app/logs \
  --restart unless-stopped \
  oura-mcp-server:latest

# View logs
docker logs -f oura-mcp-server

# Stop
docker stop oura-mcp-server
docker rm oura-mcp-server
```

---

## 📋 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
OURA_ACCESS_TOKEN=your_token_here
```

Then use with Docker Compose:

```bash
docker-compose up -d
```

### Volume Mounts

The container uses these volumes:

| Host Path | Container Path | Purpose | Mode |
|-----------|---------------|---------|------|
| `./config` | `/app/config` | Configuration files | Read-only |
| `./logs` | `/app/logs` | Application logs | Read-write |

### Configuration File

Edit `config/config.yaml` before starting:

```yaml
oura:
  api:
    access_token: "${OURA_ACCESS_TOKEN}"  # Will be substituted from env var

logging:
  output: "file"  # Use file output for Docker
  file_path: "/app/logs/oura_mcp.log"
```

---

## 🔧 Advanced Usage

### Custom Configuration

Use a different config file:

```bash
docker run -d \
  --name oura-mcp-server \
  -e OURA_ACCESS_TOKEN="your_token" \
  -e OURA_MCP_CONFIG=/app/config/custom.yaml \
  -v $(pwd)/config:/app/config:ro \
  oura-mcp-server:latest
```

### Resource Limits

Docker Compose already sets reasonable limits. To adjust:

```yaml
# docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '1.0'        # Max 1 CPU core
      memory: 1G         # Max 1GB RAM
    reservations:
      cpus: '0.5'        # Reserved 0.5 CPU
      memory: 512M       # Reserved 512MB
```

### Debug Mode

Run with debug logging:

```bash
docker run -it --rm \
  -e OURA_ACCESS_TOKEN="your_token" \
  -v $(pwd)/config:/app/config:ro \
  oura-mcp-server:latest \
  python main.py --log-level debug
```

---

## 🔍 Monitoring

### View Logs

**Docker Compose:**
```bash
# Follow logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Specific service
docker-compose logs -f oura-mcp
```

**Docker CLI:**
```bash
docker logs -f oura-mcp-server
docker logs --tail=100 oura-mcp-server
```

### Health Check

**Check container health:**
```bash
docker inspect --format='{{.State.Health.Status}}' oura-mcp-server
```

**Manual health check:**
```bash
docker exec oura-mcp-server python -c "
import sys
sys.path.insert(0, '/app/src')
from oura_mcp.utils.config import get_config
get_config()
print('Healthy')
"
```

### Resource Usage

```bash
# Real-time stats
docker stats oura-mcp-server

# One-time snapshot
docker stats --no-stream oura-mcp-server
```

---

## 🧪 Testing in Docker

### Run Tests

```bash
# Run all tests
docker run --rm \
  -e OURA_ACCESS_TOKEN="your_token" \
  -v $(pwd)/config:/app/config:ro \
  oura-mcp-server:latest \
  python tests/test_advanced_features.py

# Run specific test
docker run --rm \
  -e OURA_ACCESS_TOKEN="your_token" \
  -v $(pwd)/config:/app/config:ro \
  oura-mcp-server:latest \
  python tests/test_api.py
```

### Interactive Shell

```bash
# Start bash in container
docker exec -it oura-mcp-server bash

# Or start new container with shell
docker run -it --rm \
  -e OURA_ACCESS_TOKEN="your_token" \
  -v $(pwd)/config:/app/config:ro \
  oura-mcp-server:latest \
  bash
```

---

## 🔐 Security Best Practices

### 1. Environment Variables
**DO:**
- Use `.env` file for secrets (add to `.gitignore`)
- Use Docker secrets in production

**DON'T:**
- Commit `.env` to Git
- Put tokens in docker-compose.yml

### 2. Non-Root User
The Dockerfile creates and uses a non-root user (`oura`) for security.

### 3. Read-Only Mounts
Config directory is mounted read-only to prevent modifications.

### 4. Resource Limits
Always set CPU and memory limits in production.

---

## 🐛 Troubleshooting

### Container Won't Start

**Check logs:**
```bash
docker-compose logs oura-mcp
```

**Common issues:**
1. Missing `OURA_ACCESS_TOKEN`
   ```bash
   # Solution: Set environment variable
   export OURA_ACCESS_TOKEN="your_token"
   ```

2. Config file not found
   ```bash
   # Solution: Check volume mount
   docker-compose config
   ```

3. Port already in use
   ```bash
   # Solution: Stop conflicting container
   docker ps
   docker stop <conflicting_container>
   ```

### Permission Errors

If you get permission errors with logs:

```bash
# Create logs directory with correct permissions
mkdir -p logs
chmod 777 logs  # Or use proper user/group
```

### Config Not Loading

**Verify config mount:**
```bash
docker exec oura-mcp-server ls -la /app/config
docker exec oura-mcp-server cat /app/config/config.yaml
```

---

## 🔄 Updates & Maintenance

### Rebuild Image

After code changes:

```bash
# With Docker Compose
docker-compose build
docker-compose up -d

# With Docker CLI
docker build -t oura-mcp-server:latest .
docker stop oura-mcp-server
docker rm oura-mcp-server
docker run -d ... oura-mcp-server:latest
```

### Update Dependencies

```bash
# Update requirements.txt
# Then rebuild image
docker-compose build --no-cache
docker-compose up -d
```

### Clean Up

```bash
# Stop and remove containers
docker-compose down

# Remove images
docker rmi oura-mcp-server:latest

# Clean up unused resources
docker system prune -a
```

---

## 🚢 Production Deployment

### Docker Compose for Production

```yaml
version: '3.8'

services:
  oura-mcp:
    image: oura-mcp-server:0.2.0  # Use version tag
    container_name: oura-mcp-prod

    environment:
      - OURA_ACCESS_TOKEN=${OURA_ACCESS_TOKEN}

    volumes:
      - /path/to/config:/app/config:ro
      - /path/to/logs:/app/logs

    restart: always  # Always restart

    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G

    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "5"
```

### Health Monitoring

Set up monitoring with:
- Docker health checks (built-in)
- Prometheus + Grafana
- ELK stack for logs
- Uptime monitoring tools

---

## 📊 Multi-Container Setup

### With Redis (Future)

Uncomment Redis section in `docker-compose.yml`:

```yaml
services:
  oura-mcp:
    depends_on:
      - redis
    environment:
      - REDIS_URL=redis://redis:6379

  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data

volumes:
  redis-data:
```

---

## 🌐 Integration with Claude Desktop

Claude Desktop can't directly connect to Docker containers via stdio.

**Options:**

### Option 1: HTTP Transport (Future)
```yaml
# config/config.yaml
mcp:
  server:
    transport: "http"
    http_port: 8080

# docker-compose.yml
ports:
  - "8080:8080"
```

### Option 2: Run Locally
For Claude Desktop integration, run the server locally (not in Docker):
```bash
python main.py
```

### Option 3: Named Pipe (Advanced)
Mount named pipes between host and container (complex setup).

---

## 📦 Image Optimization

Current image size: ~200MB (multi-stage build)

**Further optimizations:**
1. Use `python:3.11-alpine` (smaller base)
2. Remove development dependencies
3. Use `.dockerignore` effectively (already done)

---

## ⚙️ Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OURA_ACCESS_TOKEN` | ✅ Yes | - | Oura API access token |
| `OURA_MCP_CONFIG` | ❌ No | `/app/config/config.yaml` | Config file path |
| `PYTHONUNBUFFERED` | ❌ No | `1` | Disable Python output buffering |

---

## 🎯 Next Steps

1. **Test locally:** `docker-compose up`
2. **Check logs:** `docker-compose logs -f`
3. **Run tests:** `docker exec oura-mcp-server python tests/test_api.py`
4. **Monitor health:** `docker inspect ...`
5. **Deploy to production:** Use version tags and proper secrets management

---

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Main README](README.md)
- [Setup Guide](SETUP.md)

---

*Docker support added in v0.2.0*
