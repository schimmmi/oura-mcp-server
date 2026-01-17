# Oura MCP Server

A Model Context Protocol (MCP) server that provides AI assistants with structured, semantic access to your Oura Ring health data.

## Features

### 🧠 Intelligence Layer (v0.3.1) ✅
- **Recovery Detection**: Multi-signal recovery assessment with weighted scoring
- **Training Readiness**: Sport-specific recommendations (general, endurance, strength, HIIT)
- **Correlation Analysis**: Discover relationships between metrics (Pearson correlation)
- **Anomaly Detection**: Statistical detection of concerning patterns with severity classification

### 📊 Data Access Tools (v0.3.0+) ✅
- **Detailed Sleep Sessions**: Exact sleep/wake times, biphasic/polyphasic tracking
- **Heart Rate Monitoring**: Time-series data with HR zones and activity breakdown
- **Workout Sessions**: Complete workout history with metrics
- **Stress & Recovery**: Daily stress levels and recovery time tracking
- **SpO2 Monitoring**: Blood oxygen saturation trends
- **VO2 Max**: Cardiorespiratory fitness estimates
- **User Tags**: Custom notes and activity tracking

### 🏥 Health Resources (v0.2.0+) ✅
- **Sleep Analysis**: Detailed sleep stages, efficiency, scores
- **Readiness Metrics**: HRV, temperature, recovery indicators
- **Activity Tracking**: Steps, calories, activity scores
- **HRV Insights**: Baseline comparison and trend detection
- **Personal Info**: Age, weight, height, biological sex

### 🔧 Core Features ✅
- **Modular Architecture**: Clean separation of concerns (v0.3.1)
- **Smart Caching**: Respects Oura API rate limits
- **Privacy Controls**: Configurable access levels and audit logging
- **Comprehensive Testing**: 100% test coverage for all features

## Project Structure

```
oura-mcp-server/
├── src/oura_mcp/
│   ├── api/
│   │   └── client.py              # Oura API v2 client
│   ├── core/
│   │   └── server.py              # MCP server orchestration (930 lines)
│   ├── resources/                 # MCP Resources (health data endpoints)
│   │   ├── formatters.py          # Data formatting utilities
│   │   ├── health_resources.py    # Sleep, readiness, activity, HRV
│   │   └── metrics_resources.py   # Personal info, stress, SpO2
│   ├── tools/                     # MCP Tools (analysis functions)
│   │   ├── data_tools.py          # Data access (sessions, HR, workouts)
│   │   ├── intelligence_tools.py  # Recovery, training, correlations
│   │   └── debug_tools.py         # Debugging and utilities
│   └── utils/
│       ├── baselines.py           # Baseline tracking (30-day averages)
│       ├── anomalies.py           # Anomaly detection engine
│       ├── interpretation.py      # Health insights interpreter
│       ├── config.py              # Configuration management
│       └── logging.py             # Structured logging
├── tests/
│   ├── test_server.py             # Basic server tests
│   ├── test_advanced_features.py  # Intelligence features tests
│   └── test_api.py                # API integration tests
├── docs/                          # Comprehensive documentation
├── config/                        # Configuration templates
└── main.py                        # Server entry point
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

**Detailed Data (NEW in v0.3.0):**
- "Show me my sleep sessions for the last 3 days"
- "What was my heart rate during my workout yesterday?"
- "Get my stress levels for the past week"
- "Show me my blood oxygen levels"
- "What's my VO2 Max?"
- "Show me the tags I created this week"

**Intelligence & Analysis (Phase 2):**
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

- [x] **v0.1.0 - v0.2.0**: Core MVP (basic resources + authentication)
- [x] **v0.3.0**: Complete API coverage (all Oura v2 endpoints) ✅ **2025-01-15**
- [x] **v0.3.1**: Code refactoring & modular architecture ✅ **2026-01-17**
- [ ] **v0.4.0**: Advanced intelligence (predictions, sleep debt, pattern recognition)
- [ ] **v0.5.0**: Polish (comprehensive logging, performance optimization)

## License

MIT

## Contributing

This is a personal project, but suggestions and improvements are welcome via issues.
