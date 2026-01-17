# Refactoring Phase 2 - Complete Instructions

## Context
Phase 1 completed: Extracted formatters and health resources.
Now need to extract remaining code from server.py (1856 lines).

## GitHub Issue
Track progress: https://github.com/schimmmi/oura-mcp-server/issues/1

## Current Status
✅ **Completed (Phase 1)**:
- `resources/formatters.py` (280 lines)
- `resources/health_resources.py` (145 lines)

🔄 **To Do (Phase 2)**:
- `resources/metrics_resources.py`
- `tools/data_tools.py`
- `tools/intelligence_tools.py`
- `tools/debug_tools.py`
- Update `server.py` to import and use these modules

---

## Step-by-Step Instructions

### Step 1: Create `resources/metrics_resources.py`

**Extract from server.py lines 645-762**:

```python
"""Metrics-related MCP resources (stress, SpO2, personal info)."""

from datetime import date, timedelta
from typing import Dict, Any

from ..api.client import OuraClient


class MetricsResourceProvider:
    """Provides metrics-related MCP resources."""

    def __init__(self, oura_client: OuraClient):
        self.oura_client = oura_client

    async def get_personal_info_resource(self) -> str:
        """Get personal information resource."""
        # Copy implementation from server.py lines 645-668

    async def get_stress_resource(self, period: str) -> str:
        """Get stress resource data."""
        # Copy implementation from server.py lines 670-721

    async def get_spo2_resource(self, period: str) -> str:
        """Get SpO2 resource data."""
        # Copy implementation from server.py lines 723-762
```

### Step 2: Create `tools/data_tools.py`

**Extract from server.py lines 798-1112**:

```python
"""Data access tools for Oura MCP server."""

from datetime import date, datetime, timedelta
from typing import Any, Dict

from ..api.client import OuraClient


class DataToolProvider:
    """Provides data access tools."""

    def __init__(self, oura_client: OuraClient):
        self.oura_client = oura_client

    async def get_sleep_sessions(self, days: int) -> str:
        """Get detailed sleep sessions."""
        # Copy from server.py lines 788-796

    async def get_heart_rate_data(self, hours: int) -> str:
        """Get time-series heart rate data."""
        # Copy from server.py lines 798-866

    async def get_workout_sessions(self, days: int) -> str:
        """Get detailed workout sessions."""
        # Copy from server.py lines 868-931

    async def get_daily_stress(self, days: int) -> str:
        """Get daily stress data."""
        # Copy from server.py lines 933-977

    async def get_spo2_data(self, days: int) -> str:
        """Get SpO2 data."""
        # Copy from server.py lines 979-1026

    async def get_vo2_max(self, days: int) -> str:
        """Get VO2 Max data."""
        # Copy from server.py lines 1028-1075

    async def get_tags(self, days: int) -> str:
        """Get user-created tags."""
        # Copy from server.py lines 1077-1112
```

### Step 3: Create `tools/intelligence_tools.py`

**Extract from server.py lines 1114-1577**:

```python
"""Intelligence tools for health analysis."""

from datetime import date, timedelta
from typing import Any, Dict

from ..api.client import OuraClient
from ..utils.baselines import BaselineManager
from ..utils.anomalies import AnomalyDetector
from ..utils.interpretation import InterpretationEngine


class IntelligenceToolProvider:
    """Provides intelligence and analysis tools."""

    def __init__(
        self,
        oura_client: OuraClient,
        baseline_manager: BaselineManager,
        anomaly_detector: AnomalyDetector,
        interpreter: InterpretationEngine
    ):
        self.oura_client = oura_client
        self.baseline_manager = baseline_manager
        self.anomaly_detector = anomaly_detector
        self.interpreter = interpreter

    async def detect_recovery_status(self) -> str:
        """Detect current recovery status."""
        # Copy from server.py lines 1114-1238

    async def assess_training_readiness(self, training_type: str) -> str:
        """Assess readiness for specific training type."""
        # Copy from server.py lines 1240-1295

    async def correlate_metrics(self, metric1: str, metric2: str, days: int) -> str:
        """Find correlations between two metrics."""
        # Copy from server.py lines 1297-1433

    async def detect_anomalies(self, metric_type: str, days: int) -> str:
        """Detect anomalies in specified metric type."""
        # Copy from server.py lines 1435-1575
```

### Step 4: Create `tools/debug_tools.py`

**Extract from server.py lines 766-850**:

```python
"""Debug and utility tools."""

from datetime import date, timedelta
from typing import Any, Dict

from ..api.client import OuraClient


class DebugToolProvider:
    """Provides debug and utility tools."""

    def __init__(self, oura_client: OuraClient):
        self.oura_client = oura_client

    async def generate_daily_brief(self) -> str:
        """Generate daily health brief."""
        # Copy from server.py lines 766-718

    async def analyze_sleep_trend(self, days: int) -> str:
        """Analyze sleep trend."""
        # Copy from server.py lines 820-844

    async def get_raw_sleep_data(self, days: int) -> str:
        """Get raw sleep data for debugging."""
        # Copy from server.py lines 746-786
```

### Step 5: Update `server.py`

**Replace method implementations with delegation**:

```python
from .resources.formatters import HealthDataFormatter
from .resources.health_resources import HealthResourceProvider
from .resources.metrics_resources import MetricsResourceProvider
from .tools.data_tools import DataToolProvider
from .tools.intelligence_tools import IntelligenceToolProvider
from .tools.debug_tools import DebugToolProvider


class OuraMCPServer:
    def __init__(self, config: Config):
        # ... existing init code ...

        # Initialize formatter
        self.formatter = HealthDataFormatter(
            self.baseline_manager,
            self.interpreter
        )

        # Initialize resource providers
        self.health_resources = HealthResourceProvider(
            self.oura_client,
            self.formatter
        )
        self.metrics_resources = MetricsResourceProvider(
            self.oura_client
        )

        # Initialize tool providers
        self.data_tools = DataToolProvider(self.oura_client)
        self.intelligence_tools = IntelligenceToolProvider(
            self.oura_client,
            self.baseline_manager,
            self.anomaly_detector,
            self.interpreter
        )
        self.debug_tools = DebugToolProvider(self.oura_client)

    # Then delegate all method calls:
    async def _get_sleep_resource(self, period: str) -> str:
        return await self.health_resources.get_sleep_resource(period)

    # ... etc for all other methods ...
```

### Step 6: Remove Old Methods

After confirming delegation works, delete the old method implementations from server.py.

### Step 7: Test

```bash
# Run tests
python3 tests/test_server.py
python3 tests/test_advanced_features.py

# Test with Claude Desktop
# Ask Claude to test each tool/resource
```

### Step 8: Verify Line Counts

```bash
wc -l src/oura_mcp/core/server.py
# Should be ~200 lines (down from 1856)

wc -l src/oura_mcp/resources/*.py
wc -l src/oura_mcp/tools/*.py
# Total should be ~1400-1500 lines distributed
```

### Step 9: Commit and Release

```bash
git add -A
git commit -m "Complete refactoring: Modularize server.py (v0.3.1)

- Extracted all remaining methods to dedicated modules
- server.py: 1856 → ~200 lines (orchestration only)
- Improved code organization and maintainability

Closes #1"

git tag -a v0.3.1 -m "Release v0.3.1 - Code Refactoring"
git push && git push --tags

gh release create v0.3.1 --title "v0.3.1 - Code Refactoring" \
  --notes "Complete modularization of server.py for better maintainability."
```

---

## Expected Final Structure

```
src/oura_mcp/
├── core/
│   └── server.py (~200 lines) ⬅️ Orchestration only
├── resources/
│   ├── formatters.py (280 lines) ✅ Phase 1
│   ├── health_resources.py (145 lines) ✅ Phase 1
│   └── metrics_resources.py (150 lines) ⬅️ Phase 2
├── tools/
│   ├── data_tools.py (400 lines) ⬅️ Phase 2
│   ├── intelligence_tools.py (500 lines) ⬅️ Phase 2
│   └── debug_tools.py (100 lines) ⬅️ Phase 2
└── utils/ (unchanged)
```

---

## Tips

1. **Copy-paste carefully**: Preserve indentation and async/await
2. **Update self references**: Methods now live in provider classes
3. **Import dependencies**: Each module needs its own imports
4. **Test incrementally**: Test after each file creation
5. **Keep server.py working**: Don't break existing functionality

## Questions?

See GitHub Issue #1 or check `docs/REFACTORING_v0.3.1.md` for the original plan.

---

**Good luck with Phase 2! 🚀**
