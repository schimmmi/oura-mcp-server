# Oura API v2 Research

## Base URL
```
https://api.ouraring.com/v2/usercollection
```

## Authentication
- **Personal Access Token**: Bearer token in Authorization header
- **OAuth2**: For multi-user applications

## Known Endpoints (v2)

### Daily Data Endpoints

#### Sleep
- **GET** `/v2/usercollection/daily_sleep`
- Returns: Sleep scores, stages (deep, REM, light), efficiency, latency, timing
- Key metrics: total_sleep_time, deep_sleep_time, rem_sleep_time, light_sleep_time, awake_time, sleep_score

#### Readiness
- **GET** `/v2/usercollection/daily_readiness`
- Returns: Overall readiness score and contributing factors
- Key metrics: readiness_score, temperature_deviation, hrv_balance, recovery_index, sleep_balance

#### Activity
- **GET** `/v2/usercollection/daily_activity`
- Returns: Activity scores, steps, calories, movement
- Key metrics: activity_score, steps, total_calories, active_calories, target_calories, met_min_high, met_min_medium, met_min_low

#### Heart Rate
- **GET** `/v2/usercollection/heartrate`
- Returns: Continuous heart rate data
- Key metrics: bpm, source (sleep/awake/rest)

#### HRV (Heart Rate Variability)
- **GET** `/v2/usercollection/daily_readiness` (includes HRV)
- Key metrics: hrv_avg, hrv_balance

### Personal Info
- **GET** `/v2/usercollection/personal_info`
- Returns: Age, weight, height, biological sex

### Sessions/Workouts
- **GET** `/v2/usercollection/session`
- Returns: Tagged activities/workouts

### Tags
- **GET** `/v2/usercollection/tag`
- Returns: User-created tags for activities

## Query Parameters
- `start_date`: YYYY-MM-DD format
- `end_date`: YYYY-MM-DD format
- `next_token`: For pagination

## Response Format
All responses follow this structure:
```json
{
  "data": [...],
  "next_token": "..."
}
```

## Rate Limits
- Personal Access Token: Typical limits around 5000 requests/day
- OAuth apps: May have different limits

## Key Metrics for MCP Server

### Sleep Metrics
- Sleep score (0-100)
- Total sleep duration (minutes)
- Sleep stages: deep, REM, light (minutes)
- Sleep efficiency (%)
- Restfulness
- REM sleep %
- Deep sleep %
- Latency (time to fall asleep)
- Timing (sleep/wake times)

### Readiness Metrics
- Readiness score (0-100)
- HRV balance
- Resting heart rate
- Body temperature deviation
- Recovery index
- Sleep balance
- Activity balance

### Activity Metrics
- Activity score (0-100)
- Steps
- Total calories
- Active calories
- METs (metabolic equivalent)
- Inactivity alerts
- Target goals

### Physiological Metrics
- HRV (ms - RMSSD)
- Resting heart rate (bpm)
- Body temperature (deviation from baseline)
- Respiratory rate

## Semantic Interpretations Needed

### HRV Context
- Baseline: Personal 30-day rolling average
- High HRV: Better recovery, parasympathetic dominance
- Low HRV: Stress, fatigue, incomplete recovery
- Typical range: 20-100ms (highly individual)

### Sleep Score Components
- Total sleep (7-9 hours optimal)
- Efficiency (85%+ good)
- Restfulness (low movement)
- REM sleep (20-25% of total)
- Deep sleep (15-20% of total)
- Latency (<15 minutes ideal)
- Timing (consistency matters)

### Readiness Score Components
- Previous day's activity
- Sleep quality and duration
- Sleep balance (sleep debt)
- Body temperature
- HRV balance
- Resting heart rate
- Recovery index

### Temperature Deviation
- Baseline: Personal average
- Positive deviation: Possible illness, overtraining, stress
- Negative deviation: Less common, can indicate underrecovery
- Range: Typically ±1°C is significant

## Data Aggregation Needs

### Trends
- 7-day rolling averages
- 30-day baselines
- Week-over-week comparisons
- Month-over-month comparisons

### Anomaly Detection
- Values >1.5 standard deviations from baseline
- Consecutive days of decline
- Sudden changes (>20% shift)

### Correlations
- Activity impact on sleep
- Sleep impact on readiness
- HRV trends vs training load
- Temperature patterns

## Security Considerations
- Token storage: Environment variables or secure vault
- Scope limitation: Read-only access
- Data retention: Cache strategy
- Audit logging: Track what AI queries
- Rate limiting: Respect Oura API limits
