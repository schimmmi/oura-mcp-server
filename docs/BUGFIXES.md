# Bug Fixes & Improvements

## 2025-12-25

### ✅ Fixed: correlate_metrics not recognizing sleep contributor metrics

**Issue:**
The `correlate_metrics` tool was not recognizing sleep contributor metrics like `deep_sleep`, `rem_sleep`, etc., resulting in "0 values" errors.

**Root Cause:**
The metric extraction logic only checked for a few explicit metrics and didn't handle the full list of contributor scores from the Oura API.

**Fix:**
Added comprehensive lists of all contributor metrics:
- **Sleep Contributors:** `deep_sleep`, `rem_sleep`, `light_sleep`, `total_sleep`, `efficiency`, `restfulness`, `latency`, `timing`
- **Readiness Contributors:** `hrv_balance`, `resting_heart_rate`, `body_temperature`, `activity_balance`, `previous_day_activity`, `previous_night`, `recovery_index`, `sleep_balance`, `sleep_regularity`
- **Activity Contributors:** `meet_daily_targets`, `move_every_hour`, `recovery_time`, `stay_active`, `training_frequency`, `training_volume`

**Location:** `src/oura_mcp/core/server.py:710-741`

**Verified:**
```bash
# Test correlations now work
correlate_metrics("deep_sleep", "sleep_score", 14)
# Result: +0.332 correlation (weak positive)

correlate_metrics("rem_sleep", "readiness_score", 14)
# Result: +0.020 correlation (very weak)
```

**Impact:**
Users can now analyze correlations between ALL Oura metrics, including granular sleep stage contributors.

---

## Known Limitations

### 1. Baseline Period Required
- Minimum 7 days of data needed for accurate baselines
- Anomaly detection improves with 14+ days
- Correlations need at least 2 data points

### 2. Oura API Rate Limits
- 60 requests per minute
- 5000 requests per day
- Server respects these limits automatically

### 3. Data Synchronization
- Requires Oura Ring to sync with cloud
- Sleep data appears the morning after
- Activity/readiness updated throughout the day

### 4. Metric Availability
- Some metrics may not be available for all users
- Depends on Oura Ring generation and subscription
- Missing data handled gracefully with "N/A" values

---

## Future Improvements

### Planned
- [ ] Caching layer for frequently accessed data
- [ ] Redis support for persistent cache
- [ ] SQLite audit logging
- [ ] More sophisticated anomaly detection algorithms
- [ ] Predictive models (recovery time, sleep debt)

### Under Consideration
- [ ] Export functionality (JSON, CSV, PDF reports)
- [ ] Historical trend comparison (week-over-week)
- [ ] Integration with other health platforms
- [ ] Custom alert thresholds
- [ ] Mobile notifications for anomalies

---

## Reporting Bugs

Found a bug? Please create an issue with:
1. **Description:** What happened vs what you expected
2. **Reproduction:** Steps to reproduce the issue
3. **Data:** Example metric names or query that failed
4. **Environment:** Python version, OS, Oura Ring generation

**Example Bug Report:**
```
Title: correlate_metrics fails for "xyz_metric"

Description:
When running correlate_metrics("xyz_metric", "sleep_score", 30),
I get "0 values" error.

Reproduction:
1. Call correlate_metrics with metric "xyz_metric"
2. Error returned: "Insufficient data: xyz_metric: 0 values"

Expected:
Should analyze correlation or indicate metric not supported

Environment:
- Python 3.11
- macOS 14.0
- Oura Ring Gen 3
```

---

*Last Updated: 2025-12-25*
