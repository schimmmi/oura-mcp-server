"""Semantic formatters for Oura health data."""

from typing import Any, Dict, List

from ..utils.baselines import BaselineManager
from ..utils.interpretation import InterpretationEngine


class HealthDataFormatter:
    """Formats Oura health data into human-readable semantic reports."""

    def __init__(self, baseline_manager: BaselineManager, interpreter: InterpretationEngine):
        """
        Initialize formatter with intelligence components.

        Args:
            baseline_manager: Baseline calculation manager
            interpreter: Data interpretation engine
        """
        self.baseline_manager = baseline_manager
        self.interpreter = interpreter

    def format_sleep_semantic_detailed(
        self,
        day: str,
        score: int,
        contributors: Dict[str, int],
        total_sleep: int,
        deep_sleep: int,
        rem_sleep: int,
        light_sleep: int,
        awake_time: int,
        periods_count: int
    ) -> str:
        """Format detailed sleep data semantically."""
        result = f"# Sleep Report\n\n"
        result += f"**Date:** {day}\n"
        result += f"**Score:** {score}/100\n\n"

        # Check if we have actual data
        if total_sleep == 0:
            result += "*Note: Sleep data not yet fully synchronized*\n\n"
            return result

        # Duration breakdown
        hours = total_sleep // 3600
        minutes = (total_sleep % 3600) // 60
        result += f"## Total Sleep: {hours}h {minutes}m\n\n"

        if periods_count > 1:
            result += f"*Recorded across {periods_count} sleep periods (biphasic/polyphasic)*\n\n"

        # Sleep stages
        result += f"## Sleep Stages\n\n"

        if total_sleep > 0:
            deep_pct = (deep_sleep / total_sleep * 100) if deep_sleep > 0 else 0
            rem_pct = (rem_sleep / total_sleep * 100) if rem_sleep > 0 else 0
            light_pct = (light_sleep / total_sleep * 100) if light_sleep > 0 else 0
            awake_pct = (awake_time / total_sleep * 100) if awake_time > 0 else 0

            result += f"- **Deep Sleep:** {deep_sleep // 60}m ({deep_pct:.1f}%)\n"
            result += f"- **REM Sleep:** {rem_sleep // 60}m ({rem_pct:.1f}%)\n"
            result += f"- **Light Sleep:** {light_sleep // 60}m ({light_pct:.1f}%)\n"
            result += f"- **Awake Time:** {awake_time // 60}m ({awake_pct:.1f}%)\n\n"

        # Contributors (scores)
        if contributors:
            result += f"## Sleep Quality Scores\n\n"
            contributor_names = {
                "total_sleep": "Total Sleep Duration",
                "deep_sleep": "Deep Sleep Quality",
                "rem_sleep": "REM Sleep Quality",
                "efficiency": "Sleep Efficiency",
                "restfulness": "Restfulness",
                "latency": "Sleep Latency",
                "timing": "Sleep Timing"
            }

            for key, name in contributor_names.items():
                if key in contributors:
                    value = contributors[key]
                    result += f"- **{name}:** {value}/100\n"

        return result

    def format_sleep_semantic(self, data: Dict[str, Any]) -> str:
        """Format sleep data semantically."""
        score = data.get("score", 0)
        total_sleep = data.get("total_sleep_duration", 0)
        deep_sleep = data.get("deep_sleep_duration", 0)
        rem_sleep = data.get("rem_sleep_duration", 0)

        result = f"# Sleep Report\n\n"
        result += f"**Date:** {data.get('day')}\n"
        result += f"**Score:** {score}/100\n\n"
        result += f"## Duration\n"
        result += f"- Total: {total_sleep // 3600}h {(total_sleep % 3600) // 60}m\n"

        # Only show percentages if total_sleep > 0
        if total_sleep > 0:
            result += f"- Deep: {deep_sleep // 60}m ({deep_sleep / total_sleep * 100:.1f}%)\n"
            result += f"- REM: {rem_sleep // 60}m ({rem_sleep / total_sleep * 100:.1f}%)\n"
        else:
            result += f"- Deep: {deep_sleep // 60}m\n"
            result += f"- REM: {rem_sleep // 60}m\n"
            result += "\n*Note: Sleep data not yet fully synchronized*\n"

        return result

    def format_readiness_semantic(self, data: Dict[str, Any]) -> str:
        """Format readiness data semantically."""
        score = data.get("score", 0)

        result = f"# Readiness Report\n\n"
        result += f"**Date:** {data.get('day')}\n"
        result += f"**Score:** {score}/100\n\n"

        contributors = data.get("contributors", {})
        if contributors:
            result += "## Contributing Factors\n"
            for key, value in contributors.items():
                result += f"- {key.replace('_', ' ').title()}: {value}\n"

        return result

    def format_activity_semantic(self, data: Dict[str, Any]) -> str:
        """Format activity data semantically."""
        score = data.get("score", 0)

        result = f"# Activity Report\n\n"
        result += f"**Date:** {data.get('day')}\n"
        result += f"**Score:** {score}/100\n\n"
        result += f"- Steps: {data.get('steps', 0):,}\n"
        result += f"- Calories: {data.get('total_calories', 0)}\n"

        return result

    def format_hrv_latest(
        self,
        readiness_data: Dict[str, Any],
        baseline_data: List[Dict[str, Any]]
    ) -> str:
        """Format latest HRV data with baseline comparison."""
        contributors = readiness_data.get("contributors", {})
        hrv_balance = contributors.get("hrv_balance")

        if hrv_balance is None:
            return "No HRV data available for today"

        # Calculate baseline
        baselines = self.baseline_manager.calculate_readiness_baselines(baseline_data)
        hrv_baseline = baselines.get("hrv_balance", {})

        # Interpret HRV
        hrv_interp = self.interpreter.interpret_hrv_balance(
            hrv_balance,
            hrv_baseline.get("mean")
        )

        result = f"# 💚 HRV Report\n\n"
        result += f"**Date:** {readiness_data.get('day')}\n"
        result += f"**HRV Balance:** {hrv_balance}/100\n"
        result += f"**Status:** {hrv_interp['emoji']} {hrv_interp['status']}\n\n"

        result += f"## Interpretation\n"
        result += f"- {hrv_interp['description']}\n"
        result += f"- **Meaning:** {hrv_interp['meaning']}\n"
        result += f"- **Implications:** {hrv_interp['implications']}\n\n"

        if 'baseline_status' in hrv_interp:
            result += f"## Baseline Comparison\n"
            result += f"- **30-day Average:** {hrv_baseline.get('mean', 0):.1f}\n"
            result += f"- **Status:** {hrv_interp['baseline_status']}\n"
            if 'deviation_pct' in hrv_interp:
                result += f"- **Deviation:** {hrv_interp['deviation_pct']:+.1f}%\n"
            result += f"- **Range:** {hrv_baseline.get('min', 0):.0f} - {hrv_baseline.get('max', 0):.0f}\n\n"

        # Add resting HR if available
        resting_hr = contributors.get("resting_heart_rate")
        if resting_hr:
            rhr_baseline = baselines.get("resting_heart_rate", {})
            result += f"## Resting Heart Rate\n"
            result += f"- **Current:** {resting_hr}/100 (contributor score)\n"
            if rhr_baseline.get("mean"):
                result += f"- **30-day Average:** {rhr_baseline['mean']:.1f}\n"
            result += "\n"

        return result

    def format_hrv_trend(
        self,
        readiness_data: List[Dict[str, Any]],
        days: int
    ) -> str:
        """Format HRV trend over period."""
        hrv_values = []
        dates = []

        for record in readiness_data:
            contributors = record.get("contributors", {})
            hrv = contributors.get("hrv_balance")
            if hrv is not None:
                hrv_values.append(hrv)
                dates.append(record.get("day"))

        if not hrv_values:
            return f"No HRV data available for the last {days} days"

        # Calculate trend statistics
        import statistics
        avg_hrv = statistics.mean(hrv_values)
        std_hrv = statistics.stdev(hrv_values) if len(hrv_values) > 1 else 0
        min_hrv = min(hrv_values)
        max_hrv = max(hrv_values)

        # Determine trend direction
        if len(hrv_values) >= 3:
            recent_avg = statistics.mean(hrv_values[-3:])
            older_avg = statistics.mean(hrv_values[:len(hrv_values)//2])
            if recent_avg > older_avg + 5:
                trend = "Improving 📈"
            elif recent_avg < older_avg - 5:
                trend = "Declining 📉"
            else:
                trend = "Stable ↔️"
        else:
            trend = "Insufficient data"

        result = f"# 📈 HRV Trend Analysis ({days} days)\n\n"
        result += f"**Data Points:** {len(hrv_values)}\n"
        result += f"**Date Range:** {dates[0]} to {dates[-1]}\n\n"

        result += f"## Statistics\n"
        result += f"- **Average:** {avg_hrv:.1f}\n"
        result += f"- **Latest:** {hrv_values[-1]}\n"
        result += f"- **Range:** {min_hrv:.0f} - {max_hrv:.0f}\n"
        result += f"- **Std Dev:** {std_hrv:.1f}\n"
        result += f"- **Trend:** {trend}\n\n"

        # Interpret current state
        latest_hrv = hrv_values[-1]
        hrv_interp = self.interpreter.interpret_hrv_balance(latest_hrv, avg_hrv)

        result += f"## Current Status\n"
        result += f"{hrv_interp['emoji']} **{hrv_interp['status']}**\n"
        result += f"- {hrv_interp['description']}\n"
        result += f"- {hrv_interp['implications']}\n\n"

        # Check for consecutive patterns
        if len(hrv_values) >= 3:
            # Check for consecutive decline
            consecutive_decline = all(
                hrv_values[i] < hrv_values[i + 1]
                for i in range(min(3, len(hrv_values) - 1))
            )
            if consecutive_decline:
                result += f"## ⚠️ Pattern Detected\n"
                result += f"HRV has declined for {min(3, len(hrv_values))} consecutive days.\n"
                result += f"- **Recommendation:** Consider rest or reduced training load\n"
                result += f"- **Monitor for:** Overtraining, illness, stress accumulation\n\n"

        return result
