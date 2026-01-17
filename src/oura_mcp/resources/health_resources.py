"""Health-related MCP resources (sleep, readiness, activity, HRV)."""

from datetime import date, timedelta
from typing import Dict, List, Any

from ..api.client import OuraClient
from .formatters import HealthDataFormatter


class HealthResourceProvider:
    """Provides health-related MCP resources."""

    def __init__(self, oura_client: OuraClient, formatter: HealthDataFormatter):
        """
        Initialize health resource provider.

        Args:
            oura_client: Oura API client
            formatter: Health data formatter
        """
        self.oura_client = oura_client
        self.formatter = formatter

    async def get_sleep_resource(self, period: str) -> str:
        """Get sleep resource data."""
        today = date.today()

        if period == "today":
            # Sleep from last night - Oura uses the *previous* day for the night's sleep
            target_date = today - timedelta(days=1)
            display_date = today
        elif period == "yesterday":
            target_date = today - timedelta(days=2)
            display_date = today - timedelta(days=1)
        else:
            raise ValueError(f"Unknown sleep period: {period}")

        # Get detailed sleep data (all periods for the day)
        # Need to search a bit wider to catch all periods
        sleep_periods = await self.oura_client.get_sleep(
            target_date - timedelta(days=1),
            target_date + timedelta(days=1)
        )

        # Filter to only periods with the target day
        sleep_periods = [p for p in sleep_periods if p.get("day") == target_date.isoformat()]

        # Get daily summary (for score) - this uses the display date
        daily_summary = await self.oura_client.get_daily_sleep(display_date, display_date)

        if not sleep_periods:
            return f"No sleep data available for {display_date.isoformat()}"

        # Aggregate all sleep periods for this day
        total_sleep = sum(p.get("total_sleep_duration", 0) for p in sleep_periods)
        deep_sleep = sum(p.get("deep_sleep_duration", 0) for p in sleep_periods)
        rem_sleep = sum(p.get("rem_sleep_duration", 0) for p in sleep_periods)
        light_sleep = sum(p.get("light_sleep_duration", 0) for p in sleep_periods)
        awake_time = sum(p.get("awake_time", 0) for p in sleep_periods)

        # Get score from daily summary
        score = daily_summary[0].get("score", 0) if daily_summary else 0
        contributors = daily_summary[0].get("contributors", {}) if daily_summary else {}

        # Format semantic response
        return self.formatter.format_sleep_semantic_detailed(
            day=display_date.isoformat(),
            score=score,
            contributors=contributors,
            total_sleep=total_sleep,
            deep_sleep=deep_sleep,
            rem_sleep=rem_sleep,
            light_sleep=light_sleep,
            awake_time=awake_time,
            periods_count=len(sleep_periods)
        )

    async def get_readiness_resource(self, period: str) -> str:
        """Get readiness resource data."""
        today = date.today()

        if period == "today":
            start_date = today
            end_date = today
        else:
            raise ValueError(f"Unknown readiness period: {period}")

        data = await self.oura_client.get_daily_readiness(start_date, end_date)

        if not data:
            return "No readiness data available for this period"

        readiness_data = data[-1]
        return self.formatter.format_readiness_semantic(readiness_data)

    async def get_activity_resource(self, period: str) -> str:
        """Get activity resource data."""
        today = date.today()

        if period == "today":
            start_date = today
            end_date = today
        else:
            raise ValueError(f"Unknown activity period: {period}")

        data = await self.oura_client.get_daily_activity(start_date, end_date)

        if not data:
            return "No activity data available for this period"

        activity_data = data[-1]
        return self.formatter.format_activity_semantic(activity_data)

    async def get_hrv_resource(self, period: str) -> str:
        """Get HRV resource data with baseline comparison."""
        today = date.today()

        if period == "latest":
            # Get today's readiness (contains HRV)
            readiness_data = await self.oura_client.get_daily_readiness(today, today)
            if not readiness_data:
                return "No HRV data available for today"

            # Get 30 days for baseline
            baseline_start = today - timedelta(days=30)
            baseline_data = await self.oura_client.get_daily_readiness(baseline_start, today)

            return self.formatter.format_hrv_latest(readiness_data[-1], baseline_data)

        elif period.startswith("trend_"):
            days_str = period.replace("trend_", "").replace("_days", "")
            days = int(days_str)

            start_date = today - timedelta(days=days)
            readiness_data = await self.oura_client.get_daily_readiness(start_date, today)

            if not readiness_data:
                return f"No HRV data available for the last {days} days"

            return self.formatter.format_hrv_trend(readiness_data, days)

        else:
            raise ValueError(f"Unknown HRV period: {period}")
