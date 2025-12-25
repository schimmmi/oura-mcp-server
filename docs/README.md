# Documentation Overview

Complete documentation for the Oura MCP Server.

---

## 📖 Getting Started

**New to the project?** Start here:

1. **[Main README](../README.md)** - Project overview and quick setup
2. **[SETUP.md](SETUP.md)** - Detailed installation instructions
3. **[DOCKER.md](DOCKER.md)** - Docker deployment guide 🐳
4. **[CLAUDE_DESKTOP_SETUP.md](CLAUDE_DESKTOP_SETUP.md)** - Claude Desktop integration

**New to Phase 2 Intelligence Features?**

👉 **[Phase 2 Quick Start Guide](PHASE2_QUICKSTART.md)** - Everything you need to know about the new intelligence features

---

## 📚 Core Documentation

### User Guides
- **[Phase 2 Quick Start Guide](PHASE2_QUICKSTART.md)** ⭐ NEW
  - New intelligence features explained
  - All tools and resources documented
  - Real-world use cases
  - Troubleshooting guide
  - 30+ supported metrics listed

### Technical Documentation
- **[MCP Design](MCP_DESIGN.md)** - Architecture and design decisions
  - MCP resources specification
  - Tool implementations
  - Semantic layer design
  - Security & privacy controls
  - Configuration schema

- **[Implementation Summary](IMPLEMENTATION_SUMMARY.md)** ⭐ NEW
  - Phase 2 complete implementation details
  - All components documented
  - Test results
  - Real-world insights
  - Production readiness checklist

### API Documentation
- **[Oura API Research](OURA_API_RESEARCH.md)** - Oura Ring API documentation
  - Available endpoints
  - Data structures
  - Authentication
  - Rate limits
  - Best practices

---

## 🐛 Issues & Updates

- **[Bug Fixes](BUGFIXES.md)** ⭐ NEW
  - Known bugs and their fixes
  - Known limitations
  - How to report bugs
  - Future improvements planned

- **[Release Notes](RELEASE_NOTES.md)** ⭐ NEW
  - Version history
  - Feature releases
  - Breaking changes
  - Upgrade guides

- **[Test Results](TEST_RESULTS.md)** - Validation and testing
  - Phase 1 test results
  - All features validated
  - Known edge cases

---

## 📋 Documentation by Topic

### Installation & Setup
1. [Main README](../README.md) - Quick start
2. [SETUP.md](../SETUP.md) - Detailed setup
3. [CLAUDE_DESKTOP_SETUP.md](../CLAUDE_DESKTOP_SETUP.md) - Claude integration
4. [Configuration](MCP_DESIGN.md#configuration-schema) - config.yaml reference

### Using the Server
1. [Phase 2 Quick Start](PHASE2_QUICKSTART.md) - New features guide
2. [Example Queries](../README.md#example-queries) - What to ask Claude
3. [Available Resources](MCP_DESIGN.md#mcp-resources-read-only-data-access) - Data endpoints
4. [Available Tools](MCP_DESIGN.md#mcp-tools-actions--analysis) - Analysis functions

### Understanding the Data
1. [Metric Correlations](PHASE2_QUICKSTART.md#3-metric-correlation-analysis) - How metrics relate
2. [HRV Analysis](PHASE2_QUICKSTART.md#hrv-interpretation) - Understanding HRV
3. [Recovery State](PHASE2_QUICKSTART.md#recovery-score-calculation) - How recovery is calculated
4. [Training Readiness](PHASE2_QUICKSTART.md#2-training-readiness-assessment) - Sport-specific guidance

### Development
1. [MCP Design](MCP_DESIGN.md) - Architecture
2. [Implementation Summary](IMPLEMENTATION_SUMMARY.md) - Technical details
3. [Test Results](TEST_RESULTS.md) - Validation
4. [Bug Fixes](BUGFIXES.md) - Known issues

---

## 🗂️ File Structure

```
docs/
├── README.md                      # This file
├── MCP_DESIGN.md                  # Architecture documentation
├── OURA_API_RESEARCH.md           # Oura API documentation
├── PHASE2_QUICKSTART.md           # Phase 2 user guide (NEW)
├── IMPLEMENTATION_SUMMARY.md      # Phase 2 technical docs (NEW)
├── RELEASE_NOTES.md               # Version history (NEW)
├── BUGFIXES.md                    # Bug tracking (NEW)
└── TEST_RESULTS.md                # Test validation

Root Directory:
├── README.md                      # Main project overview
├── SETUP.md                       # Installation guide
├── CLAUDE_DESKTOP_SETUP.md        # Claude Desktop setup
├── main.py                        # Server entry point
├── requirements.txt               # Python dependencies
├── config/                        # Configuration files
├── src/oura_mcp/                  # Source code
└── tests/                         # Test files
```

---

## 🎯 Quick Navigation

### I want to...

**...get started quickly**
→ [Main README](../README.md) → [SETUP.md](../SETUP.md)

**...use the new intelligence features**
→ [Phase 2 Quick Start](PHASE2_QUICKSTART.md)

**...understand how recovery is calculated**
→ [Recovery Score Calculation](PHASE2_QUICKSTART.md#recovery-score-calculation)

**...find correlation between metrics**
→ [Metric Correlation Guide](PHASE2_QUICKSTART.md#3-metric-correlation-analysis)

**...assess training readiness**
→ [Training Readiness Tool](PHASE2_QUICKSTART.md#2-training-readiness-assessment)

**...detect anomalies in my data**
→ [Anomaly Detection](PHASE2_QUICKSTART.md#4-anomaly-detection)

**...understand the architecture**
→ [MCP Design](MCP_DESIGN.md)

**...report a bug**
→ [Bug Reporting Guide](BUGFIXES.md#reporting-bugs)

**...see what's new**
→ [Release Notes](RELEASE_NOTES.md)

**...integrate with Claude Desktop**
→ [Claude Desktop Setup](../CLAUDE_DESKTOP_SETUP.md)

---

## 📦 Documentation Versions

- **Phase 1 (v0.1.0)** - Core MVP
  - Basic resources and tools
  - Initial MCP implementation

- **Phase 2 (v0.2.0)** - Intelligence Layer ⭐ Current
  - Baseline tracking
  - Recovery detection
  - Training readiness
  - Correlation analysis
  - Anomaly detection

---

## 🤝 Contributing to Documentation

Found an issue or want to improve the docs?

- Typos/errors: Submit PR with corrections
- Missing info: Create issue describing what's needed
- Unclear sections: Open discussion for clarification

---

## 📜 License

All documentation is licensed under MIT License - See [LICENSE](../LICENSE) file.

---

*Last updated: 2025-12-25*
*Documentation version: 0.2.0*
