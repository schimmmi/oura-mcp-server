# Phase 2 Quick Start Guide 🚀

**New Intelligence Features** - Get the most out of your Oura MCP Server

---

## 🎯 What's New in Phase 2?

Phase 2 adds **health intelligence** to your Oura data:
- Understands your personal baselines
- Detects concerning patterns
- Provides training recommendations
- Finds hidden correlations
- Gives context-aware interpretations

---

## 🏃 Quick Test

Run the test suite to see all features in action:

```bash
python3 test_advanced_features.py
```

This will demonstrate:
- ✅ HRV analysis with baselines
- ✅ Recovery status assessment
- ✅ Training readiness for different sports
- ✅ Metric correlations
- ✅ Anomaly detection

---

## 📊 New Resources

### HRV Resources

**Get latest HRV with baseline:**
```
Resource: oura://hrv/latest
```

**Get 7-day HRV trend:**
```
Resource: oura://hrv/trend/7_days
```

**Get 30-day HRV trend:**
```
Resource: oura://hrv/trend/30_days
```

Example output shows:
- Current HRV balance score
- 30-day baseline average
- Deviation from baseline (%)
- Status: Balanced, Moderate, Low, Very Low
- Autonomic nervous system interpretation
- Consecutive decline warnings

---

## 🛠️ New Tools

### 1. Recovery Status Detection

**Tool:** `detect_recovery_status`

**What it does:**
Combines multiple signals to assess your overall recovery state:
- HRV Balance (35% weight)
- Readiness Score (30%)
- Sleep Quality (20%)
- Resting HR (10%)
- Body Temperature (5%)

**Ask Claude:**
- "Am I recovered?"
- "What's my recovery status?"
- "Should I rest today?"

**Output includes:**
- Recovery score (0-100)
- Overall state (Fully Recovered → Not Recovered)
- Contributing signals breakdown
- HRV analysis
- Training recommendations

---

### 2. Training Readiness Assessment

**Tool:** `assess_training_readiness`

**Parameters:**
- `training_type`: general | endurance | strength | high_intensity

**What it does:**
Provides sport-specific GO/NO-GO recommendations based on your recovery state.

**Ask Claude:**
- "Can I do my long run today?"
- "Am I ready for strength training?"
- "Assess my readiness for HIIT workout"

**Output includes:**
- GO/NO-GO/CAUTION recommendation
- Confidence level
- Intensity modifications (70-85%, 50-60%, etc.)
- Duration adjustments
- Limiting factors

**Training Type Thresholds:**

| Type | Optimal | Acceptable | Minimum |
|------|---------|------------|---------|
| General | 70 | 55 | 45 |
| Endurance | 70 | 60 | 50 |
| Strength | 75 | 65 | 55 |
| High Intensity | 80 | 70 | 60 |

---

### 3. Metric Correlation Analysis

**Tool:** `correlate_metrics`

**Parameters:**
- `metric1`: First metric (e.g., "sleep_score")
- `metric2`: Second metric (e.g., "readiness_score")
- `days`: Analysis period (default: 30)

**What it does:**
Calculates Pearson correlation to find relationships between metrics.

**Ask Claude:**
- "Is there a correlation between my sleep and activity?"
- "How does my HRV affect my readiness?"
- "Does activity impact my sleep quality?"
- "Correlate my deep_sleep with sleep_score over 30 days"
- "Is there a relationship between rem_sleep and readiness?"
- "How does efficiency correlate with my HRV?"

**Supported Metrics:**

**Sleep Metrics:**
- `sleep_score` - Overall sleep score (0-100)
- `deep_sleep` - Deep sleep contributor score
- `rem_sleep` - REM sleep contributor score
- `light_sleep` - Light sleep contributor score
- `total_sleep` - Total sleep duration contributor score
- `efficiency` - Sleep efficiency contributor score
- `restfulness` - Restfulness contributor score
- `latency` - Sleep latency contributor score
- `timing` - Sleep timing contributor score

**Readiness Metrics:**
- `readiness_score` - Overall readiness score
- `hrv_balance` - HRV balance contributor score
- `resting_heart_rate` - Resting heart rate contributor score
- `body_temperature` - Body temperature contributor score
- `activity_balance` - Activity balance contributor score
- `previous_day_activity` - Previous day activity contributor score
- `previous_night` - Previous night contributor score
- `recovery_index` - Recovery index contributor score
- `sleep_balance` - Sleep balance contributor score
- `sleep_regularity` - Sleep regularity contributor score

**Activity Metrics:**
- `activity_score` - Overall activity score
- `steps` - Daily step count
- `total_calories` - Total calories burned
- `active_calories` - Active calories burned

**Correlation Strength:**
- Strong: |r| > 0.7
- Moderate: |r| > 0.5
- Weak: |r| > 0.3
- Very Weak: |r| ≤ 0.3

**Example Results from Real Data:**
- HRV ↔ Readiness: **+0.706** (Strong positive) 🔴
- Sleep ↔ Readiness: +0.564 (Moderate positive) 🟡
- Activity ↔ Sleep: -0.165 (Weak negative) 🟢

---

### 4. Anomaly Detection

**Tool:** `detect_anomalies`

**Parameters:**
- `metric_type`: sleep | readiness | activity
- `days`: Analysis window (default: 7)

**What it does:**
Detects statistically significant anomalies using:
- Z-score analysis (>1.5 std dev)
- Domain-specific thresholds
- Pattern recognition

**Ask Claude:**
- "Are there any anomalies in my sleep?"
- "Detect concerning patterns in my data"
- "What's unusual about my metrics this week?"

**Detects:**

**Sleep Anomalies:**
- Deep sleep drops (>30% below baseline) 🔴
- Restfulness issues (>20% below baseline) 🟡
- Overall score deviations

**Readiness Anomalies:**
- Low HRV (<50) 🔴
- Temperature deviations (<85) 🟡

**Output includes:**
- Severity (High 🔴, Medium 🟡, Low 🟢)
- Current vs baseline values
- Deviation (absolute & percentage)
- Possible causes
- Recommendations

---

## 💡 Real-World Use Cases

### Use Case 1: Training Day Decision

**Scenario:** You have a hard workout planned, but not sure if you're recovered.

**Ask Claude:**
```
"Assess my readiness for high-intensity training today"
```

**Claude will:**
1. Check your recovery status
2. Evaluate HRV, sleep, readiness
3. Compare to high-intensity thresholds
4. Give GO/NO-GO/CAUTION recommendation
5. Suggest modifications if needed

---

### Use Case 2: Understanding a Bad Night

**Scenario:** You had terrible sleep and want to know why.

**Ask Claude:**
```
"Detect anomalies in my sleep data. What's wrong?"
```

**Claude will:**
1. Compare to your 30-day baseline
2. Identify specific issues (e.g., deep sleep 49% below normal)
3. List possible causes
4. Suggest monitoring steps

---

### Use Case 3: Finding Patterns

**Scenario:** You suspect high activity days affect your sleep.

**Ask Claude:**
```
"Is there a correlation between my activity_score and sleep_score over the last 30 days?"
```

**Claude will:**
1. Calculate Pearson correlation
2. Show strength and direction
3. Provide statistical summary
4. Interpret the relationship

---

### Use Case 4: HRV Trend Analysis

**Scenario:** Your readiness has been low lately.

**Ask Claude:**
```
"Show me my HRV trend over the last week. What's happening?"
```

**Claude will:**
1. Show 7-day HRV trend
2. Compare to baseline
3. Detect decline patterns
4. Explain autonomic stress signals
5. Suggest recovery actions

---

## 🎓 Understanding the Intelligence

### Recovery Score Calculation

```
Recovery Score =
    HRV Balance × 0.35 +
    Readiness × 0.30 +
    Sleep Score × 0.20 +
    (100 - |RHR Deviation| × 10) × 0.10 +
    Temperature × 0.05
```

**Why these weights?**
- **HRV (35%)**: Best indicator of autonomic nervous system recovery
- **Readiness (30%)**: Oura's holistic assessment
- **Sleep (20%)**: Foundation of recovery
- **RHR (10%)**: Cardiovascular stress indicator
- **Temperature (5%)**: Early illness/overtraining signal

---

### HRV Interpretation

| Score | Status | Meaning | Implications |
|-------|--------|---------|--------------|
| 75-100 | Balanced 💚 | ANS well-balanced | Ready for stress |
| 50-74 | Moderate 🟡 | Some stress response | Functioning but not optimal |
| 30-49 | Low 🟠 | Elevated sympathetic activity | Under stress or recovering |
| 0-29 | Very Low 🔴 | ANS strained | High stress/illness/overtraining |

**ANS = Autonomic Nervous System**

---

### Anomaly Detection Logic

**Statistical Anomalies:**
- Deviation > 1.5 standard deviations
- Z-score calculation
- Baseline comparison

**Domain-Specific Thresholds:**
- Deep sleep drop > 30%
- HRV < 50 (absolute)
- Temperature < 85
- Restfulness drop > 20%

**Severity Classification:**
- **High 🔴**: Immediate attention needed
- **Medium 🟡**: Monitor closely
- **Low 🟢**: Informational

---

## 🔧 Configuration

All features are enabled by default in `config/config.yaml`:

```yaml
mcp:
  tools:
    enabled:
      - "analyze_sleep_trend"
      - "detect_recovery_status"      # ⭐ NEW
      - "generate_daily_brief"
      - "assess_training_readiness"   # ⭐ NEW
      - "correlate_metrics"            # ⭐ NEW
      - "detect_anomalies"             # ⭐ NEW
```

To disable a tool, remove it from the list.

---

## 📈 What to Expect

### Baseline Period (First 7-14 days)

The system needs data to establish your personal baselines:
- HRV baseline: 7+ days
- Sleep baseline: 14+ days for accuracy
- Activity baseline: 7+ days

**During this period:**
- Baselines will be calculated but may not be fully representative
- Anomaly detection will be less accurate
- Correlations need minimum 2 data points

**After baseline period:**
- Highly accurate personal baselines
- Reliable anomaly detection
- Meaningful correlation analysis

---

## 🚨 Interpreting Warnings

### 🔴 High Severity
Action needed. Consider:
- Rest day
- Medical consultation if persistent
- Stress management
- Sleep prioritization

### 🟡 Medium Severity
Monitor closely. Consider:
- Reduced training intensity
- Extra recovery day
- Lifestyle adjustments
- Re-assess in 24-48h

### 🟢 Low Severity / ✅ Normal
Continue as planned. Optional:
- Note any lifestyle factors
- Track for patterns
- Maintain good habits

---

## 💪 Best Practices

1. **Check Recovery Status Morning:**
   - Ask Claude: "What's my recovery status?"
   - Use before planning training day

2. **Use Training-Specific Assessments:**
   - Different thresholds for different sports
   - High-intensity needs better recovery than general

3. **Monitor HRV Trends Weekly:**
   - Ask: "Show my HRV trend"
   - Catch overtraining early

4. **Investigate Anomalies:**
   - Don't ignore high-severity warnings
   - Use possible causes to adjust lifestyle

5. **Discover Your Patterns:**
   - Run correlations monthly
   - Learn what affects your metrics
   - Optimize lifestyle based on data

---

## 🆘 Troubleshooting

**Q: Baseline shows "No data available"**
A: Need minimum 2-3 days of data. Keep wearing your ring.

**Q: Recovery score seems wrong**
A: Check if all metrics are synced. Recovery uses multiple signals.

**Q: Correlation shows "Insufficient data"**
A: Need at least 2 matching data points. Ensure both metrics are tracked.

**Q: No anomalies detected but I feel terrible**
A: Statistical anomalies ≠ subjective feeling. Trust your body. The tool detects deviations from *your* baseline, not absolute values.

---

## 🎯 Next Steps

1. **Run the test:** `python3 test_advanced_features.py`
2. **Connect to Claude Desktop** (see main README)
3. **Ask Claude about your recovery**
4. **Explore correlations in your data**
5. **Use training assessments before workouts**
6. **Monitor HRV trends weekly**

---

## 📚 Additional Resources

- **Full Implementation Details:** [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- **API Design:** [MCP_DESIGN.md](MCP_DESIGN.md)
- **Oura API Info:** [OURA_API_RESEARCH.md](OURA_API_RESEARCH.md)
- **Test Results:** [TEST_RESULTS.md](TEST_RESULTS.md)
- **Release Notes:** [RELEASE_NOTES.md](RELEASE_NOTES.md)
- **Bug Fixes:** [BUGFIXES.md](BUGFIXES.md)

---

## 🎉 You're Ready!

You now have an **intelligent health assistant** that:
- ✅ Understands your personal normal
- ✅ Detects concerning patterns
- ✅ Gives training recommendations
- ✅ Finds hidden correlations
- ✅ Provides context-aware insights

**Start asking Claude smart health questions!** 🧠💪

---

*Phase 2: Intelligence Layer - Fully Operational ✅*
