# Refactoring Plan for v0.3.1

## Current State
- `server.py`: 1856 lines (too large)
- All logic in one file

## Completed (Phase 1)
- ✅ Created `resources/formatters.py` (280 lines)
- ✅ Created `resources/health_resources.py` (145 lines)
- ✅ Extracted all semantic formatters
- ✅ Extracted core health resources

## Remaining Work (Phase 2 - Due to token limits, document approach)

### Create metrics_resources.py
Extract from server.py (lines 645-762):
- `_get_personal_info_resource()`
- `_get_stress_resource()`
- `_get_spo2_resource()`

### Create tools/data_tools.py  
Extract from server.py (lines 798-1112):
- `_tool_get_sleep_sessions()`
- `_tool_get_heart_rate_data()`
- `_tool_get_workout_sessions()`
- `_tool_get_daily_stress()`
- `_tool_get_spo2_data()`
- `_tool_get_vo2_max()`
- `_tool_get_tags()`

### Create tools/intelligence_tools.py
Extract from server.py (lines 1114-1577):
- `_tool_detect_recovery_status()`
- `_tool_assess_training_readiness()`
- `_tool_correlate_metrics()`
- `_tool_detect_anomalies()`

### Create tools/debug_tools.py
Extract from server.py (lines 766-850):
- `_tool_generate_daily_brief()`
- `_tool_analyze_sleep_trend()`
- `_tool_get_raw_sleep_data()`

### Update server.py
1. Import new modules
2. Delegate to resource/tool providers
3. Remove extracted methods
4. Keep only orchestration logic (~200 lines)

## Alternative: Simplified Refactoring
Given the current large size, we can:
1. Keep current formatters + health_resources extraction
2. Document remaining refactoring for future
3. Mark as technical debt
4. Release v0.3.1 as "partial refactoring"

This reduces server.py from 1856 → ~1400 lines (better, but not complete).
