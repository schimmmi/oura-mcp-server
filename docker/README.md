# Docker Utilities

This directory contains Docker-related utilities and helpers.

## Files

- **Makefile** - Convenient make commands for Docker operations
- **docker-test.sh** - Automated testing script
- **.env.docker.example** - Example environment configuration

## Usage

### Using Makefile (from project root)

The Makefile is symlinked to the root directory for convenience:

```bash
make help     # Show all available commands
make up       # Start containers
make down     # Stop containers
make logs     # View logs
make test     # Run tests
make shell    # Open shell in container
```

### Using Test Script

```bash
# Make executable
chmod +x docker/docker-test.sh

# Run tests
export OURA_ACCESS_TOKEN="your_token"
./docker/docker-test.sh
```

### Environment Configuration

```bash
# Copy example
cp docker/.env.docker.example .env

# Edit with your token
nano .env

# Use with docker-compose
docker-compose up -d
```

## Full Documentation

See [../docs/DOCKER.md](../docs/DOCKER.md) for complete Docker deployment documentation.
