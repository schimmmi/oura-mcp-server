"""Sleep debt calculation and tracking utilities."""

import statistics
from datetime import date, timedelta
from typing import Any, Dict, List, Tuple, Optional


class SleepDebtTracker:
    """Tracks and calculates accumulated sleep debt over time."""

    # Sleep duration targets (in seconds)
    OPTIMAL_SLEEP = {
        "default": 8 * 3600,  # 8 hours
        "teenager": 9 * 3600,  # 9 hours
        "adult": 8 * 3600,     # 8 hours
        "senior": 7 * 3600,    # 7 hours
    }

    def __init__(self, optimal_sleep_hours: float = 8.0):
        """
        Initialize sleep debt tracker.

        Args:
            optimal_sleep_hours: Target sleep duration in hours (default: 8)
        """
        self.optimal_sleep = optimal_sleep_hours * 3600  # Convert to seconds

    def calculate_sleep_debt(
        self,
        sleep_data: List[Dict[str, Any]],
        lookback_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Calculate accumulated sleep debt over time.

        Args:
            sleep_data: List of daily sleep records from Oura API
            lookback_days: Number of days to analyze (None = all data)

        Returns:
            Dictionary with sleep debt analysis
        """
        if not sleep_data:
            return {
                "total_debt": 0,
                "avg_daily_deficit": 0,
                "days_analyzed": 0,
                "status": "no_data"
            }

        # Filter data if lookback specified
        if lookback_days:
            sleep_data = sleep_data[-lookback_days:]

        # Calculate daily deficits
        daily_deficits = []
        debt_over_time = []
        accumulated_debt = 0

        for record in sleep_data:
            day = record.get("day")
            total_sleep = record.get("total_sleep_duration", 0)

            # Calculate deficit (negative = debt, positive = surplus)
            deficit = total_sleep - self.optimal_sleep
            daily_deficits.append(deficit)

            # Accumulate debt (only count negative values)
            if deficit < 0:
                accumulated_debt += abs(deficit)
            else:
                # Surplus can pay back some debt, but not create "credit"
                accumulated_debt = max(0, accumulated_debt - deficit * 0.5)  # 50% payback rate

            debt_over_time.append({
                "day": day,
                "sleep_duration": total_sleep / 3600,  # Convert to hours
                "deficit": deficit / 3600,
                "accumulated_debt": accumulated_debt / 3600
            })

        # Calculate statistics
        total_debt = accumulated_debt / 3600  # Convert to hours
        avg_daily_deficit = statistics.mean(daily_deficits) / 3600 if daily_deficits else 0
        days_in_debt = sum(1 for d in daily_deficits if d < 0)
        days_surplus = sum(1 for d in daily_deficits if d >= 0)

        # Determine severity
        severity = self._assess_debt_severity(total_debt, avg_daily_deficit)

        # Calculate recovery time
        recovery_days = self._estimate_recovery_time(total_debt, avg_daily_deficit)

        return {
            "total_debt_hours": round(total_debt, 2),
            "avg_daily_deficit_hours": round(avg_daily_deficit, 2),
            "days_analyzed": len(sleep_data),
            "days_in_debt": days_in_debt,
            "days_surplus": days_surplus,
            "severity": severity,
            "recovery_days_estimate": recovery_days,
            "debt_over_time": debt_over_time,
            "status": "calculated"
        }

    def _assess_debt_severity(self, total_debt: float, avg_deficit: float) -> Dict[str, str]:
        """
        Assess the severity of sleep debt.

        Args:
            total_debt: Total accumulated debt in hours
            avg_deficit: Average daily deficit in hours

        Returns:
            Dictionary with severity assessment
        """
        if total_debt < 2:
            level = "minimal"
            emoji = "🟢"
            description = "Minimal sleep debt - you're well rested"
            impact = "Little to no impact on performance"
        elif total_debt < 5:
            level = "mild"
            emoji = "🟡"
            description = "Mild sleep debt - slight fatigue possible"
            impact = "Minor impact on cognitive function and mood"
        elif total_debt < 10:
            level = "moderate"
            emoji = "🟠"
            description = "Moderate sleep debt - noticeable fatigue"
            impact = "Reduced cognitive performance, increased stress"
        elif total_debt < 20:
            level = "severe"
            emoji = "🔴"
            description = "Severe sleep debt - significant impairment"
            impact = "Major cognitive deficits, health risks increasing"
        else:
            level = "critical"
            emoji = "💀"
            description = "Critical sleep debt - immediate action needed"
            impact = "Serious health risks, severely impaired function"

        return {
            "level": level,
            "emoji": emoji,
            "description": description,
            "impact": impact
        }

    def _estimate_recovery_time(self, total_debt: float, avg_deficit: float) -> int:
        """
        Estimate days needed to recover from sleep debt.

        Args:
            total_debt: Total accumulated debt in hours
            avg_deficit: Average daily deficit in hours

        Returns:
            Estimated days for full recovery
        """
        if total_debt <= 0:
            return 0

        # Recovery rate: can pay back ~1 hour per night with good sleep
        # (getting optimal + 1 hour extra)
        recovery_rate = 1.0  # hours per day

        # If consistently under-sleeping, recovery is harder
        if avg_deficit < -0.5:
            recovery_rate = 0.5  # Slower recovery if pattern continues

        days = int(total_debt / recovery_rate)

        # Cap at reasonable maximum
        return min(days, 30)

    def generate_debt_report(
        self,
        sleep_data: List[Dict[str, Any]],
        lookback_days: int = 30
    ) -> str:
        """
        Generate formatted sleep debt report.

        Args:
            sleep_data: List of daily sleep records
            lookback_days: Number of days to analyze

        Returns:
            Formatted markdown report
        """
        debt_analysis = self.calculate_sleep_debt(sleep_data, lookback_days)

        if debt_analysis["status"] == "no_data":
            return "⚠️ No sleep data available for debt analysis"

        result = f"# 💤 Sleep Debt Analysis ({lookback_days} days)\n\n"

        # Summary
        severity = debt_analysis["severity"]
        result += f"## {severity['emoji']} Status: {severity['level'].upper()}\n\n"
        result += f"**{severity['description']}**\n\n"

        # Key Metrics
        result += f"## 📊 Key Metrics\n\n"
        result += f"- **Total Sleep Debt:** {debt_analysis['total_debt_hours']:.1f} hours\n"
        result += f"- **Average Daily Deficit:** {debt_analysis['avg_daily_deficit_hours']:.1f} hours\n"
        result += f"- **Days in Debt:** {debt_analysis['days_in_debt']}/{debt_analysis['days_analyzed']}\n"
        result += f"- **Days with Surplus:** {debt_analysis['days_surplus']}/{debt_analysis['days_analyzed']}\n"
        result += f"- **Optimal Sleep Target:** {self.optimal_sleep / 3600:.1f} hours/night\n\n"

        # Impact Assessment
        result += f"## 🎯 Impact on Performance\n\n"
        result += f"**{severity['impact']}**\n\n"

        if severity['level'] in ['moderate', 'severe', 'critical']:
            result += "### Potential Effects:\n"
            result += "- 🧠 Reduced cognitive performance and reaction time\n"
            result += "- 😰 Increased stress and emotional reactivity\n"
            result += "- 💪 Decreased physical performance and recovery\n"
            result += "- 🏥 Weakened immune system\n"
            result += "- ⚖️ Impaired metabolism and weight regulation\n\n"

        # Recovery Plan
        result += f"## 🔄 Recovery Plan\n\n"

        recovery_days = debt_analysis['recovery_days_estimate']
        if recovery_days == 0:
            result += "✅ **No recovery needed** - you're well rested!\n\n"
        else:
            result += f"**Estimated Recovery Time:** {recovery_days} days\n\n"

            result += "### Recommended Actions:\n"

            if severity['level'] == 'minimal' or severity['level'] == 'mild':
                result += "1. **Maintain Schedule:** Keep consistent sleep/wake times\n"
                result += "2. **Add 30 minutes:** Go to bed 30 minutes earlier tonight\n"
                result += "3. **Weekend Catch-up:** Allow 1 extra hour on weekend nights\n\n"
            elif severity['level'] == 'moderate':
                result += "1. **Priority Recovery:** Make sleep your #1 priority\n"
                result += "2. **Add 1-2 hours:** Go to bed significantly earlier\n"
                result += "3. **Weekend Extension:** Add 2 extra hours on weekends\n"
                result += "4. **Reduce Stress:** Cut non-essential activities\n"
                result += "5. **Naps OK:** 20-30 minute power naps can help\n\n"
            else:  # severe or critical
                result += "1. **⚠️ IMMEDIATE ACTION:** Clear your schedule for sleep\n"
                result += "2. **Add 2-3 hours:** Go to bed much earlier every night\n"
                result += "3. **Weekend Recovery:** Sleep in as much as possible\n"
                result += "4. **Professional Help:** Consider consulting a sleep specialist\n"
                result += "5. **Reduce All Stress:** Cancel non-critical commitments\n"
                result += "6. **Strategic Naps:** 60-90 minute naps if needed\n\n"

        # Trend Visualization
        result += self._format_debt_timeline(debt_analysis['debt_over_time'][-14:])

        # Tips
        result += f"## 💡 Sleep Optimization Tips\n\n"
        result += "1. **Consistency:** Same bedtime/wake time every day (±30 min)\n"
        result += "2. **Environment:** Dark, cool (65-68°F), quiet bedroom\n"
        result += "3. **Pre-sleep Routine:** 30-60 min wind-down period\n"
        result += "4. **Avoid:**\n"
        result += "   - Caffeine after 2 PM\n"
        result += "   - Screens 1 hour before bed\n"
        result += "   - Heavy meals within 3 hours of sleep\n"
        result += "   - Alcohol (disrupts deep sleep)\n"
        result += "5. **Exercise:** Regular activity, but not within 3 hours of bed\n\n"

        return result

    def _format_debt_timeline(self, recent_data: List[Dict[str, Any]]) -> str:
        """Format recent sleep debt timeline."""
        result = "## 📈 Recent Debt Timeline (Last 14 Days)\n\n"

        result += "```\n"
        result += "Day         Sleep   Deficit   Accumulated Debt\n"
        result += "-----------------------------------------------\n"

        for entry in recent_data:
            day = entry['day'][-5:]  # Last 5 chars (MM-DD)
            sleep = entry['sleep_duration']
            deficit = entry['deficit']
            debt = entry['accumulated_debt']

            # Visual bar for debt
            bar_length = min(int(debt / 0.5), 20)  # Each character = 0.5 hours
            bar = "█" * bar_length

            deficit_str = f"{deficit:+.1f}h"
            result += f"{day:10}  {sleep:4.1f}h  {deficit_str:8}  {debt:4.1f}h {bar}\n"

        result += "```\n\n"

        return result

    def calculate_optimal_sleep_for_age(self, age: int) -> float:
        """
        Calculate optimal sleep duration based on age.

        Args:
            age: Age in years

        Returns:
            Optimal sleep duration in hours
        """
        if age < 18:
            return 9.0  # Teenagers
        elif age < 65:
            return 8.0  # Adults
        else:
            return 7.5  # Seniors

    def calculate_sleep_efficiency_debt(
        self,
        sleep_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate debt based on sleep efficiency (quality vs quantity).

        Args:
            sleep_data: List of daily sleep records

        Returns:
            Efficiency-based debt analysis
        """
        if not sleep_data:
            return {"status": "no_data"}

        efficiency_scores = []
        quality_debt = 0

        for record in sleep_data:
            efficiency = record.get("contributors", {}).get("efficiency")
            if efficiency is not None:
                efficiency_scores.append(efficiency)

                # Efficiency below 85 counts as quality debt
                if efficiency < 85:
                    deficit = (85 - efficiency) / 10  # Convert to "hours equivalent"
                    quality_debt += deficit

        if not efficiency_scores:
            return {"status": "no_efficiency_data"}

        avg_efficiency = statistics.mean(efficiency_scores)

        return {
            "avg_efficiency": round(avg_efficiency, 1),
            "quality_debt_hours_equivalent": round(quality_debt, 1),
            "nights_poor_efficiency": sum(1 for e in efficiency_scores if e < 85),
            "status": "calculated"
        }
