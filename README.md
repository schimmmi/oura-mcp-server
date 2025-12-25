# Oura MCP Server

A Model Context Protocol (MCP) server that provides AI assistants with structured, semantic access to your Oura Ring health data.

## Features

### Intelligence Layer (Phase 2) ✅
- **Baseline Tracking**: Personal 30-day rolling averages for all metrics
- **Recovery Detection**: Multi-signal recovery assessment with weighted scoring
- **Training Readiness**: Sport-specific recommendations (general, endurance, strength, HIIT)
- **Anomaly Detection**: Statistical detection of concerning patterns with severity classification
- **Correlation Analysis**: Discover relationships between metrics (Pearson correlation)
- **HRV Insights**: Detailed HRV analysis with baseline comparison and trend detection

### Core Features (Phase 1) ✅
- **Semantic Resources**: Pre-interpreted health metrics (sleep, readiness, HRV, activity)
- **Analysis Tools**: Trend analysis, daily health briefs
- **Privacy Controls**: Configurable access levels and audit logging
- **Smart Caching**: Respects Oura API rate limits

## Project Structure

```
oura-mcp-server/
├── src/oura_mcp/          # Main package
│   ├── api/               # Oura API client
│   ├── core/              # MCP server core
│   ├── resources/         # MCP resources (data endpoints)
│   ├── tools/             # MCP tools (analysis functions)
│   └── utils/             # Utilities (caching, baselines, etc.)
├── tests/                 # Test suite
│   ├── unit/              # Unit tests
│   └── integration/       # Integration tests
├── docs/                  # Documentation
├── config/                # Configuration files
└── main.py                # Server entry point
```

## Quick Start

### Prerequisites
- Python 3.10+ (or Docker)
- Oura Ring with API access
- Personal Access Token from [Oura Cloud](https://cloud.ouraring.com/personal-access-tokens)

### Option 1: Docker (Recommended)

```bash
# Set your token
export OURA_ACCESS_TOKEN="your_token_here"

# Start with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f
```

**See [docs/DOCKER.md](docs/DOCKER.md) for complete Docker documentation.**

### Option 2: Local Python Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Configure your Oura token
export OURA_ACCESS_TOKEN="your_token_here"

# Run the server
python main.py
```

### Configuration

Copy `config/config.example.yaml` to `config/config.yaml` and customize:

```yaml
oura:
  api:
    access_token: "${OURA_ACCESS_TOKEN}"
  cache:
    enabled: true
    ttl_seconds: 3600

mcp:
  server:
    name: "Oura Health MCP"
    transport: "stdio"
```

## Usage with AI Clients

### Claude Desktop

Add to your Claude config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "oura": {
      "command": "python",
      "args": ["/path/to/oura-mcp-server/main.py"]
    }
  }
}
```

### Example Queries

**Basic Queries:**
- "How did I sleep last night?"
- "What's my readiness score today?"
- "Give me my daily health brief"

**Intelligence & Analysis (NEW in Phase 2):**
- "Am I recovered enough for a hard workout today?"
- "Assess my readiness for high-intensity training"
- "What's my HRV trend over the last week?"
- "Is there a correlation between my sleep and activity levels?"
- "Are there any concerning anomalies in my recent data?"
- "Why has my HRV been declining this week?"
- "What factors are limiting my recovery today?"

## Development

```bash
# Run all tests
python3 tests/test_advanced_features.py

# Run API tests
python3 tests/test_api.py

# Run server tests
python3 tests/test_server.py

# Run with debug logging
python main.py --log-level debug

# Type checking
mypy src/

# Linting
ruff check src/
```

## Documentation

- **[Phase 2 Quick Start Guide](docs/PHASE2_QUICKSTART.md)** - User guide for new intelligence features
- **[Implementation Summary](docs/IMPLEMENTATION_SUMMARY.md)** - Complete Phase 2 documentation
- **[MCP Design](docs/MCP_DESIGN.md)** - Architecture and design documentation
- **[Release Notes](docs/RELEASE_NOTES.md)** - Version history and changelog
- **[Bug Fixes](docs/BUGFIXES.md)** - Known issues and fixes
- **[Oura API Research](docs/OURA_API_RESEARCH.md)** - API documentation
- **[Test Results](docs/TEST_RESULTS.md)** - Test validation results

## Security

- Tokens stored in environment variables only
- Audit logging of all MCP requests
- Configurable access levels (summary/standard/full)
- Local-only data processing

## Roadmap

- [x] Phase 1: Core MVP (basic resources + authentication)
- [x] Phase 2: Intelligence (baseline tracking, recovery detection, correlations, anomaly detection) ✅ **COMPLETED 2025-12-25**
- [ ] Phase 3: Advanced (predictions, sleep debt, pattern recognition)
- [ ] Phase 4: Polish (comprehensive logging, optimization)

## License

MIT

## Contributing

This is a personal project, but suggestions and improvements are welcome via issues.
