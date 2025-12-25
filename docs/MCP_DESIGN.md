# Oura MCP Server Design

## MCP Resources (Read-Only Data Access)

Resources provide contextual data that AI models can read and understand.

### Sleep Resources

```
oura://sleep/today
oura://sleep/yesterday
oura://sleep/last_7_days
oura://sleep/last_30_days
oura://sleep/date/{YYYY-MM-DD}
oura://sleep/summary/week
oura://sleep/summary/month
```

**Data Structure (Semantic, LLM-friendly)**:
```json
{
  "date": "2025-12-25",
  "sleep_score": 82,
  "interpretation": "Good - above your 30-day average of 78",
  "total_sleep": {
    "minutes": 421,
    "hours_formatted": "7h 1m",
    "vs_optimal": "Slightly below 8h target"
  },
  "sleep_stages": {
    "deep_minutes": 92,
    "deep_percentage": 21.8,
    "deep_assessment": "Excellent - above 15% threshold",
    "rem_minutes": 101,
    "rem_percentage": 24.0,
    "rem_assessment": "Optimal - within 20-25% range",
    "light_minutes": 228,
    "light_percentage": 54.2
  },
  "efficiency": {
    "percentage": 87,
    "assessment": "Good - above 85% threshold"
  },
  "timing": {
    "bedtime": "23:15",
    "wake_time": "06:45",
    "consistency_note": "15 minutes later than average"
  },
  "context": {
    "previous_night_comparison": "+5 points",
    "7_day_trend": "improving",
    "anomalies": []
  }
}
```

### Readiness Resources

```
oura://readiness/today
oura://readiness/yesterday
oura://readiness/trend/7_days
oura://readiness/trend/30_days
```

**Data Structure**:
```json
{
  "date": "2025-12-25",
  "readiness_score": 75,
  "interpretation": "Moderate - adequate for light activities",
  "recommendation": "Consider lighter training today; focus on recovery",
  "contributing_factors": {
    "sleep_score": {
      "value": 82,
      "contribution": "Positive",
      "weight": "High"
    },
    "hrv_balance": {
      "value": "Balanced",
      "note": "HRV at 98% of baseline"
    },
    "resting_hr": {
      "value": 52,
      "baseline": 51,
      "deviation": "+1 bpm (normal variation)"
    },
    "temperature": {
      "deviation": "+0.2°C",
      "interpretation": "Normal - within typical range",
      "alert": null
    },
    "recovery_index": {
      "value": 68,
      "interpretation": "Moderate recovery"
    },
    "activity_balance": {
      "status": "Good",
      "note": "Activity level appropriate for recovery"
    }
  },
  "actionable_insights": [
    "HRV is balanced - body has recovered from yesterday",
    "Temperature slightly elevated but normal",
    "Consider postponing high-intensity training"
  ]
}
```

### Activity Resources

```
oura://activity/today
oura://activity/yesterday
oura://activity/week
oura://activity/summary/30_days
```

### HRV Resources

```
oura://hrv/latest
oura://hrv/trend/7_days
oura://hrv/trend/30_days
oura://hrv/baseline
```

**Data Structure**:
```json
{
  "date": "2025-12-25",
  "hrv_avg": 48,
  "baseline_30_day": 52,
  "deviation": {
    "absolute": -4,
    "percentage": -7.7,
    "interpretation": "Slightly below baseline"
  },
  "assessment": "Moderately recovered - slight stress response",
  "context": {
    "trend_7_day": "declining",
    "consecutive_days_below_baseline": 2,
    "possible_factors": [
      "Accumulated training load",
      "Sleep debt",
      "Stress or illness onset"
    ]
  },
  "recommendation": "Monitor for further decline; prioritize recovery"
}
```

### Metrics Resources

```
oura://metrics/overview/today
oura://metrics/temperature/trend
oura://metrics/resting_hr/trend
oura://metrics/all/baseline
```

---

## MCP Tools (Actions & Analysis)

Tools allow AI to perform computations and generate insights.

### Analysis Tools

#### `analyze_sleep_trend`
```python
@mcp.tool()
def analyze_sleep_trend(days: int = 7) -> dict:
    """
    Analyze sleep patterns over specified period.
    
    Returns:
    - Trend direction (improving/declining/stable)
    - Average score
    - Consistency metrics
    - Anomalies detected
    - Recommendations
    """
```

**Output**:
```json
{
  "period": "7 days",
  "average_score": 79,
  "trend": "improving",
  "trend_details": {
    "score_change": "+6 points vs previous week",
    "direction": "positive",
    "consistency": "High - scores within 10 point range"
  },
  "anomalies": [
    {
      "date": "2025-12-22",
      "issue": "Sleep score 62 (17 points below average)",
      "possible_cause": "Late bedtime (1:30 AM) + low deep sleep"
    }
  ],
  "recommendations": [
    "Maintain current bedtime consistency",
    "Deep sleep percentage is optimal",
    "Consider earlier bedtime if possible"
  ]
}
```

#### `detect_recovery_status`
```python
@mcp.tool()
def detect_recovery_status() -> dict:
    """
    Assess current recovery state based on multiple signals.
    
    Combines:
    - Readiness score
    - HRV vs baseline
    - Resting HR vs baseline
    - Temperature deviation
    - Sleep quality
    - Activity load
    
    Returns: Recovery state with confidence and recommendations
    """
```

**Output**:
```json
{
  "recovery_state": "moderate",
  "confidence": 0.85,
  "signals": {
    "readiness": {"value": 75, "weight": 0.3, "status": "moderate"},
    "hrv": {"deviation": -7.7, "weight": 0.25, "status": "slightly_low"},
    "resting_hr": {"deviation": +1, "weight": 0.2, "status": "normal"},
    "temperature": {"deviation": +0.2, "weight": 0.15, "status": "normal"},
    "sleep": {"score": 82, "weight": 0.1, "status": "good"}
  },
  "interpretation": "Body is adequately recovered but not optimally primed",
  "training_recommendation": {
    "intensity": "Moderate (60-75% max effort)",
    "type": "Aerobic/technique work preferred over high-intensity",
    "caution": "Avoid max effort or long duration"
  },
  "recovery_actions": [
    "Prioritize sleep tonight (aim for 8+ hours)",
    "Consider active recovery or rest day",
    "Monitor HRV tomorrow - if still low, take rest day"
  ]
}
```

#### `correlate_metrics`
```python
@mcp.tool()
def correlate_metrics(
    metric1: str,  # e.g., "activity_score", "deep_sleep", "hrv_balance"
    metric2: str,  # e.g., "sleep_score", "readiness_score"
    days: int = 30
) -> dict:
    """
    Find correlations between two metrics over specified period.

    Useful for understanding how behavior impacts recovery.

    Supported metrics:
    - Sleep: sleep_score, deep_sleep, rem_sleep, light_sleep, total_sleep,
             efficiency, restfulness, latency, timing
    - Readiness: readiness_score, hrv_balance, resting_heart_rate,
                 body_temperature, activity_balance, previous_day_activity,
                 previous_night, recovery_index, sleep_balance, sleep_regularity
    - Activity: activity_score, steps, total_calories, active_calories
    """
```

#### `detect_anomalies`
```python
@mcp.tool()
def detect_anomalies(
    metric: str,  # e.g., "hrv", "temperature", "resting_hr"
    days: int = 7,
    threshold_std_dev: float = 1.5
) -> dict:
    """
    Detect statistical anomalies in a specific metric.
    
    Returns:
    - Dates with anomalies
    - Magnitude of deviation
    - Potential causes
    - Patterns detected
    """
```

### Summary Tools

#### `generate_daily_brief`
```python
@mcp.tool()
def generate_daily_brief() -> dict:
    """
    Generate comprehensive daily health brief.
    
    Includes:
    - Overall status
    - Key metrics
    - Trends
    - Recommendations
    - Alerts
    """
```

#### `compare_periods`
```python
@mcp.tool()
def compare_periods(
    period1_start: str,
    period1_end: str,
    period2_start: str,
    period2_end: str
) -> dict:
    """
    Compare two time periods across all metrics.
    
    Useful for:
    - Before/after intervention analysis
    - Training block comparisons
    - Seasonal variation
    """
```

### Contextual Tools

#### `explain_metric_change`
```python
@mcp.tool()
def explain_metric_change(
    metric: str,
    date: str
) -> dict:
    """
    Explain why a specific metric changed on a given date.
    
    Analyzes:
    - Historical context
    - Related metrics
    - Known patterns
    - Possible external factors
    """
```

#### `assess_training_readiness`
```python
@mcp.tool()
def assess_training_readiness(
    training_type: str = "general"  # or "endurance", "strength", "high_intensity"
) -> dict:
    """
    Specific assessment for training readiness.
    
    Returns:
    - Go/No-go recommendation
    - Suggested modifications
    - Warning signs
    - Optimal training window
    """
```

### Predictive Tools

#### `estimate_sleep_debt`
```python
@mcp.tool()
def estimate_sleep_debt() -> dict:
    """
    Calculate accumulated sleep debt over recent period.
    
    Returns:
    - Total debt (hours)
    - Recovery timeline
    - Impact on performance
    - Repayment strategy
    """
```

#### `predict_recovery_time`
```python
@mcp.tool()
def predict_recovery_time(current_state: dict) -> dict:
    """
    Estimate time needed for full recovery based on current metrics.
    
    Returns:
    - Estimated days to baseline
    - Confidence interval
    - Factors affecting timeline
    - Acceleration strategies
    """
```

---

## Semantic Layer Design

### Purpose
Transform raw API data into interpretable insights that:
1. Reduce hallucination (provide context, not just numbers)
2. Save tokens (pre-computed interpretations)
3. Enable better reasoning (relationships and patterns)

### Components

#### 1. Baseline Manager
```python
class BaselineManager:
    """
    Maintains rolling baselines for all metrics.
    - 30-day rolling average
    - Standard deviation
    - Personal ranges (min/max)
    - Seasonal adjustments
    """
```

#### 2. Interpretation Engine
```python
class InterpretationEngine:
    """
    Converts raw values to semantic meanings.
    
    Examples:
    - HRV 45ms → "7% below baseline, indicates mild stress"
    - Sleep score 82 → "Good, above average"
    - Temperature +0.8°C → "Elevated - possible illness or overtraining"
    """
```

#### 3. Anomaly Detector
```python
class AnomalyDetector:
    """
    Statistical and pattern-based anomaly detection.
    - Z-score analysis
    - Consecutive-day patterns
    - Multi-metric correlations
    - Context-aware alerts
    """
```

#### 4. Recommendation Generator
```python
class RecommendationGenerator:
    """
    Generate actionable advice based on current state.
    - Training modifications
    - Recovery priorities
    - Lifestyle adjustments
    - Warning escalation
    """
```

---

## Security & Privacy Design

### Access Control Levels

#### Level 1: Summary Only
- Access to scores and high-level trends
- No raw physiological data
- No detailed sleep stages

#### Level 2: Standard Access
- All scores and trends
- Aggregated metrics
- Sleep stages
- No minute-by-minute data

#### Level 3: Full Access (Default for personal use)
- All available data
- Raw API responses
- Detailed breakdowns

### Audit Logging

```python
class AuditLogger:
    """
    Track all MCP requests.
    
    Logs:
    - Timestamp
    - Client identifier
    - Resource/tool accessed
    - Parameters
    - Response summary
    """
```

### Data Retention

- Cache duration: Configurable (default 1 hour)
- Historical data: Keep local aggregates
- Raw API responses: Optional persistent cache
- Audit logs: 90 days

---

## Configuration Schema

```yaml
oura:
  api:
    base_url: "https://api.ouraring.com"
    access_token: "${OURA_ACCESS_TOKEN}"
    rate_limit:
      requests_per_minute: 60
      requests_per_day: 5000
  
  cache:
    enabled: true
    ttl_seconds: 3600
    persistent: false
  
  baselines:
    calculation_period_days: 30
    update_frequency: "daily"
  
  security:
    access_level: "full"  # summary | standard | full
    audit_logging: true
    audit_retention_days: 90

mcp:
  server:
    name: "Oura Health MCP"
    version: "0.1.0"
    transport: "stdio"  # or "http"
  
  resources:
    enabled:
      - "sleep"
      - "readiness"
      - "activity"
      - "hrv"
      - "metrics"
  
  tools:
    enabled:
      - "analyze_sleep_trend"
      - "detect_recovery_status"
      - "correlate_metrics"
      - "detect_anomalies"
      - "generate_daily_brief"
      - "assess_training_readiness"
      - "explain_metric_change"
```

---

## Example MCP Client Interaction

### Query 1: Simple Context
```
User → AI: "How did I sleep last night?"

AI → MCP: GET oura://sleep/yesterday

MCP → AI: [Semantic sleep data with interpretation]

AI → User: "You slept well - 7h 45m with good deep sleep (22%). 
Your sleep score of 85 is above your average. 
You went to bed 20 minutes earlier than usual, which helped."
```

### Query 2: Analysis
```
User → AI: "Should I do my long run today?"

AI → MCP: 
  1. GET oura://readiness/today
  2. TOOL assess_training_readiness(training_type="endurance")

MCP → AI: [Readiness data + training recommendation]

AI → User: "Your readiness is 72 (moderate). HRV is slightly low,
suggesting incomplete recovery. Recommendation: Either shorten 
your long run by 30% or postpone to tomorrow. Your sleep was 
good, so recovery is trending positive."
```

### Query 3: Pattern Discovery
```
User → AI: "Why has my HRV been declining this week?"

AI → MCP:
  1. GET oura://hrv/trend/7_days
  2. TOOL explain_metric_change(metric="hrv", date="2025-12-25")
  3. TOOL correlate_metrics("activity_score", "hrv", days=7)

MCP → AI: [Trend data + correlation analysis]

AI → User: "Your HRV has dropped 12% over 7 days. Analysis shows 
strong negative correlation with activity score (r=-0.78). 
You've had 5 consecutive high-activity days without a rest day. 
Your body is accumulating fatigue. Recommendation: Take 1-2 rest 
days to allow HRV to return to baseline."
```

---

## Implementation Priority

### Phase 1: Core (MVP)
1. Basic MCP server setup
2. Oura API client with authentication
3. Essential resources: sleep/today, readiness/today, hrv/latest
4. One analysis tool: generate_daily_brief
5. Simple baseline calculations

### Phase 2: Intelligence
1. All planned resources
2. Key analysis tools (sleep trend, recovery status)
3. Semantic interpretation layer
4. Anomaly detection

### Phase 3: Advanced
1. Predictive tools
2. Correlation analysis
3. Multi-metric insights
4. Recommendation engine

### Phase 4: Polish
1. Comprehensive audit logging
2. Advanced caching strategies
3. Configuration management
4. Performance optimization
