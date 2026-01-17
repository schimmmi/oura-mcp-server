# Changelog

All notable changes to the Oura MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.5.0] - 2026-01-17

### 🎉 Added - Personalized Health Insights
- **Chronotype Analysis**: MSF-based scientific chronotype classification (Night Owl, Morning Lark, etc.)
  - Main sleep extraction from biphasic/polyphasic patterns
  - Social jetlag calculation
  - Weekday vs weekend comparison
  - Activity pattern correlation
  - Personalized recommendations by chronotype
- **Personal Sleep Need Calculation**: Auto-detection via readiness correlation
  - Method 1: Readiness correlation (top 25% performance days)
  - Method 2: Sleep score correlation
  - Method 3: Duration percentile (75th)
  - Fallback: Chronotype-based defaults
- **Adaptive Severity Thresholds**: All thresholds now scale to personal sleep need
  - New "elevated" severity level (between moderate and severe)
  - Scale factor pattern: `personal_need / 8.0`
  - Applied to sleep debt, duration alerts, consecutive nights

### 🐛 Fixed
- **Chronotype Misclassification**: Naps no longer skew bedtime averages
- **Consecutive Bad Nights**: Fixed false positives from aggregated sessions with score=0
  - Added efficiency-as-proxy logic when score unavailable
  - Dual criteria: score + duration deficit
- **RHR Data Type Confusion**: Clarified that RHR values are scores (0-100), not BPM
  - Inverted deviation logic (lower score = elevated HR)
  - Updated all reporting with clear labels

### 🔧 Changed
- **Sleep Debt Tracker**: Now auto-detects personal sleep need (no hardcoded 8h)
- **Alert System**: Constructor accepts `personal_sleep_need` parameter
- **Chronotype Analyzer**: Works with raw sessions (not aggregated)
- **Intelligence Tools**: Pass raw sessions to chronotype analyzer

### 📚 Documentation
- Created comprehensive v0.5.0 release notes
- Updated README.md with chronotype examples
- Added scientific basis documentation (MSF methodology)

### ✅ Testing
- Validated with 30+ days of real biphasic sleep data
- Tested night owl chronotype detection
- Verified readiness correlation accuracy
- Confirmed threshold scaling correctness

---

## [0.3.1] - 2026-01-17

### 🏗️ Changed - Major Code Refactoring
- **Modular Architecture**: Reorganized codebase into clean, maintainable modules
- **server.py**: Reduced from 1,856 to 930 lines (50% reduction)
- **Provider Pattern**: Extracted business logic into dedicated provider classes
  - Created `resources/metrics_resources.py` (132 lines)
  - Created `tools/data_tools.py` (408 lines)
  - Created `tools/intelligence_tools.py` (333 lines)
  - Created `tools/debug_tools.py` (114 lines)

### 🐛 Fixed
- **Stress Data Type Safety**: Added `isinstance()` check for `day_summary` to prevent AttributeError
- **VO2 Max Error Handling**: Graceful handling of API 404 with informative user message

### 📚 Documentation
- Updated README.md with new module structure
- Created comprehensive v0.3.1 release notes
- Added refactoring documentation

### ✅ Testing
- All tests pass (100% coverage maintained)
- No breaking changes - fully backward compatible

---

## [0.3.0] - 2025-01-15

### 🎉 Added - Complete Oura API v2 Coverage
- **Sleep Sessions**: Detailed sleep/wake times with biphasic/polyphasic tracking
- **Heart Rate Data**: Time-series HR with zones and activity breakdown
- **Workout Sessions**: Complete workout history with metrics
- **Stress Tracking**: Daily stress levels and recovery time
- **SpO2 Monitoring**: Blood oxygen saturation data
- **VO2 Max**: Cardiorespiratory fitness estimates
- **User Tags**: Custom notes and activity tracking

### 📚 Documentation
- Added comprehensive v0.3.0 release notes
- Updated API documentation

---

## [0.2.1] - 2025-01-14

### 🐛 Fixed
- Sleep sessions tool now correctly handles multiple periods per day
- Improved error messages for missing data

---

## [0.2.0] - 2025-01-12

### 🎉 Added - Intelligence Features
- **Baseline Tracking**: 30-day rolling averages for all metrics
- **Recovery Detection**: Multi-signal recovery assessment
- **Training Readiness**: Sport-specific recommendations
- **Anomaly Detection**: Statistical detection of concerning patterns
- **Correlation Analysis**: Discover relationships between metrics
- **HRV Insights**: Detailed HRV analysis with baseline comparison

### 📚 Documentation
- Added Phase 2 Quick Start Guide
- Added Implementation Summary
- Added comprehensive test results

---

## [0.1.0] - 2025-01-05

### 🎉 Added - Initial Release
- **MCP Server**: Basic Model Context Protocol implementation
- **Oura API Client**: v2 API integration with rate limiting
- **Resources**: Sleep, readiness, activity, HRV
- **Tools**: Daily health brief, sleep trend analysis
- **Configuration**: YAML-based config with environment variables
- **Caching**: Smart caching system with TTL
- **Logging**: Structured logging with rotation
- **Docker**: Docker and docker-compose support

### 🔒 Security
- Environment-based token storage
- Audit logging of all requests
- Configurable access levels

### 📚 Documentation
- Complete README with examples
- Docker documentation
- MCP design documentation
- API research documentation

---

## Version History

- **v0.3.1** (2026-01-17): Code refactoring & modular architecture
- **v0.3.0** (2025-01-15): Complete Oura API v2 coverage
- **v0.2.1** (2025-01-14): Bug fixes for sleep sessions
- **v0.2.0** (2025-01-12): Intelligence features (recovery, training, correlations)
- **v0.1.0** (2025-01-05): Initial release (MVP)

---

## Links

- **Repository**: https://github.com/schimmmi/oura-mcp-server
- **Issues**: https://github.com/schimmmi/oura-mcp-server/issues
- **Releases**: https://github.com/schimmmi/oura-mcp-server/releases
