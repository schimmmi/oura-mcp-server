"""Debug and utility tools."""

import json
from datetime import date, timedelta
from typing import Any, Dict

from ..api.client import OuraClient
from ..utils.weekly_report import WeeklyReportGenerator


class DebugToolProvider:
    """Provides debug and utility tools."""

    def __init__(self, oura_client: OuraClient):
        self.oura_client = oura_client
        self.weekly_report_generator = WeeklyReportGenerator()

    async def generate_daily_brief(self) -> str:
        """Generate daily health brief."""
        today = date.today()
        yesterday = today - timedelta(days=1)

        # Gather all data
        # Sleep uses yesterday's date (Oura convention)
        all_sleep_periods = await self.oura_client.get_sleep(yesterday - timedelta(days=1), today)
        sleep_periods = [p for p in all_sleep_periods if p.get("day") == yesterday.isoformat()]

        sleep_summary = await self.oura_client.get_daily_sleep(today, today)
        readiness_data = await self.oura_client.get_daily_readiness(today, today)
        activity_data = await self.oura_client.get_daily_activity(today, today)

        brief = "# Daily Health Brief\n\n"
        brief += f"**Date:** {today.isoformat()}\n\n"

        # Sleep
        if sleep_periods:
            # Aggregate all sleep periods
            total_sleep = sum(p.get("total_sleep_duration", 0) for p in sleep_periods)
            deep_sleep = sum(p.get("deep_sleep_duration", 0) for p in sleep_periods)
            rem_sleep = sum(p.get("rem_sleep_duration", 0) for p in sleep_periods)

            score = sleep_summary[0].get("score", 0) if sleep_summary else 0

            brief += f"## Sleep (Score: {score})\n"
            brief += f"- Total: {total_sleep // 3600}h {(total_sleep % 3600) // 60}m\n"
            brief += f"- Deep: {deep_sleep // 60}m\n"
            brief += f"- REM: {rem_sleep // 60}m\n"
            if len(sleep_periods) > 1:
                brief += f"- Periods: {len(sleep_periods)} (biphasic/polyphasic)\n"
            brief += "\n"
        else:
            brief += f"## Sleep\n*No sleep data available*\n\n"

        # Readiness
        if readiness_data:
            readiness = readiness_data[-1]
            score = readiness.get("score")
            brief += f"## Readiness (Score: {score})\n"
            contributors = readiness.get("contributors", {})
            brief += f"- HRV Balance: {contributors.get('hrv_balance', 'N/A')}\n"
            brief += f"- Temperature: {contributors.get('body_temperature', 'N/A')}\n\n"

        # Activity
        if activity_data:
            activity = activity_data[-1]
            score = activity.get("score")
            brief += f"## Activity (Score: {score})\n"
            brief += f"- Steps: {activity.get('steps', 0):,}\n"
            brief += f"- Calories: {activity.get('total_calories', 0)}\n\n"

        return brief

    async def analyze_sleep_trend(self, days: int) -> str:
        """Analyze sleep trend."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        data = await self.oura_client.get_daily_sleep(start_date, end_date)

        if not data:
            return f"No sleep data available for the last {days} days"

        scores = [d.get("score") for d in data if d.get("score") is not None]

        if not scores:
            return "No sleep scores available"

        avg_score = sum(scores) / len(scores)
        trend = "improving" if scores[-1] > avg_score else "declining"

        analysis = f"# Sleep Trend Analysis ({days} days)\n\n"
        analysis += f"- **Average Score:** {avg_score:.1f}\n"
        analysis += f"- **Latest Score:** {scores[-1]}\n"
        analysis += f"- **Trend:** {trend}\n"
        analysis += f"- **Data Points:** {len(scores)}\n"

        return analysis

    async def get_raw_sleep_data(self, days: int) -> str:
        """Get raw sleep data from Oura API for debugging."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        data = await self.oura_client.get_daily_sleep(start_date, end_date)

        if not data:
            return f"No sleep data available for the last {days} days"

        result = f"# Raw Oura Sleep Data (Last {days} days)\n\n"
        result += f"**Retrieved {len(data)} records**\n\n"

        for record in data:
            result += f"## Date: {record.get('day')}\n"
            result += f"```json\n{json.dumps(record, indent=2)}\n```\n\n"

        return result

    async def generate_weekly_report(
        self,
        weeks_ago: int = 0,
        include_previous_week: bool = True
    ) -> str:
        """
        Generate comprehensive weekly health report.

        Args:
            weeks_ago: Number of weeks ago to report (0 = current week, 1 = last week, etc.)
            include_previous_week: Include week-over-week comparison

        Returns:
            Formatted weekly report
        """
        # Calculate date range
        today = date.today()
        days_since_monday = today.weekday()  # Monday = 0

        # Calculate start and end of target week
        week_start = today - timedelta(days=days_since_monday) - timedelta(weeks=weeks_ago)
        week_end = week_start + timedelta(days=6)

        # Get data for the week
        sleep_data = await self.oura_client.get_sleep(week_start, week_end)
        readiness_data = await self.oura_client.get_daily_readiness(week_start, week_end)
        activity_data = await self.oura_client.get_daily_activity(week_start, week_end)

        # Get previous week data if requested
        previous_week_data = None
        if include_previous_week:
            prev_week_start = week_start - timedelta(days=7)
            prev_week_end = prev_week_start + timedelta(days=6)

            prev_sleep = await self.oura_client.get_sleep(prev_week_start, prev_week_end)
            prev_readiness = await self.oura_client.get_daily_readiness(prev_week_start, prev_week_end)
            prev_activity = await self.oura_client.get_daily_activity(prev_week_start, prev_week_end)

            # Analyze previous week
            prev_sleep_metrics = self.weekly_report_generator._analyze_sleep_metrics(prev_sleep)
            prev_readiness_metrics = self.weekly_report_generator._analyze_readiness_metrics(prev_readiness)
            prev_activity_metrics = self.weekly_report_generator._analyze_activity_metrics(prev_activity)

            previous_week_data = {
                'sleep': prev_sleep_metrics,
                'readiness': prev_readiness_metrics,
                'activity': prev_activity_metrics
            }

        # Generate report
        report = self.weekly_report_generator.generate_weekly_report(
            sleep_data,
            readiness_data,
            activity_data,
            week_start,
            week_end,
            previous_week_data
        )

        return self.weekly_report_generator.format_weekly_report(report)
