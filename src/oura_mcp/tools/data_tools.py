"""Data access tools for Oura MCP server."""

import json
from datetime import date, datetime, timedelta
from typing import Any, Dict

from ..api.client import OuraClient


class DataToolProvider:
    """Provides data access tools."""

    def __init__(self, oura_client: OuraClient):
        self.oura_client = oura_client

    async def get_sleep_sessions(self, days: int) -> str:
        """Get detailed sleep sessions with exact times and durations."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        # Get all sleep sessions (including naps, multiple periods)
        sessions = await self.oura_client.get_sleep(start_date, end_date)

        if not sessions:
            return f"No sleep sessions available for the last {days} days"

        result = f"# 🛏️ Detailed Sleep Sessions (Last {days} days)\n\n"
        result += f"**Retrieved {len(sessions)} sleep periods**\n\n"

        # Group sessions by day
        sessions_by_day = {}
        for session in sessions:
            day = session.get("day")
            if day not in sessions_by_day:
                sessions_by_day[day] = []
            sessions_by_day[day].append(session)

        # Format each day's sessions
        for day in sorted(sessions_by_day.keys(), reverse=True):
            day_sessions = sessions_by_day[day]
            result += f"## 📅 {day}\n\n"

            if len(day_sessions) > 1:
                result += f"*{len(day_sessions)} sleep periods recorded (biphasic/polyphasic)*\n\n"

            for idx, session in enumerate(day_sessions, 1):
                # Parse timestamps
                bedtime_start = session.get("bedtime_start")
                bedtime_end = session.get("bedtime_end")

                if bedtime_start:
                    start_dt = datetime.fromisoformat(bedtime_start.replace('Z', '+00:00'))
                    start_time = start_dt.strftime("%H:%M")
                else:
                    start_time = "N/A"

                if bedtime_end:
                    end_dt = datetime.fromisoformat(bedtime_end.replace('Z', '+00:00'))
                    end_time = end_dt.strftime("%H:%M")
                else:
                    end_time = "N/A"

                # Session header
                if len(day_sessions) > 1:
                    result += f"### Period {idx}: {start_time} → {end_time}\n\n"
                else:
                    result += f"### Sleep: {start_time} → {end_time}\n\n"

                # Duration breakdown
                total_sleep = session.get("total_sleep_duration", 0)
                deep_sleep = session.get("deep_sleep_duration", 0)
                rem_sleep = session.get("rem_sleep_duration", 0)
                light_sleep = session.get("light_sleep_duration", 0)
                awake_time = session.get("awake_time", 0)

                if total_sleep > 0:
                    hours = total_sleep // 3600
                    minutes = (total_sleep % 3600) // 60

                    result += f"**Total Sleep:** {hours}h {minutes}m\n\n"
                    result += f"- **Deep Sleep:** {deep_sleep // 60}m ({deep_sleep / total_sleep * 100:.1f}%)\n"
                    result += f"- **REM Sleep:** {rem_sleep // 60}m ({rem_sleep / total_sleep * 100:.1f}%)\n"
                    result += f"- **Light Sleep:** {light_sleep // 60}m ({light_sleep / total_sleep * 100:.1f}%)\n"
                    result += f"- **Awake Time:** {awake_time // 60}m\n\n"

                # Additional metrics
                if session.get("efficiency"):
                    result += f"**Efficiency:** {session['efficiency']}%\n"
                if session.get("latency"):
                    result += f"**Sleep Latency:** {session['latency'] // 60}m\n"

                result += "\n"

            result += "---\n\n"

        return result

    async def get_heart_rate_data(self, hours: int) -> str:
        """Get time-series heart rate data."""
        end_datetime = datetime.now()
        start_datetime = end_datetime - timedelta(hours=hours)

        # Get heart rate data
        hr_data = await self.oura_client.get_heart_rate(start_datetime, end_datetime)

        if not hr_data:
            return f"No heart rate data available for the last {hours} hours"

        result = f"# ❤️ Heart Rate Data (Last {hours} hours)\n\n"
        result += f"**Retrieved {len(hr_data)} data points**\n\n"

        # Calculate statistics
        hr_values = [point.get("bpm") for point in hr_data if point.get("bpm")]
        if hr_values:
            avg_hr = sum(hr_values) / len(hr_values)
            min_hr = min(hr_values)
            max_hr = max(hr_values)

            result += f"## Summary Statistics\n"
            result += f"- **Average HR:** {avg_hr:.0f} bpm\n"
            result += f"- **Min HR:** {min_hr} bpm\n"
            result += f"- **Max HR:** {max_hr} bpm\n"
            result += f"- **Range:** {max_hr - min_hr} bpm\n\n"

            # HR Zones (simple approximation: max HR = 220 - age, assuming age 30)
            max_hr_estimate = 190  # Can be made dynamic with personal_info
            zone1 = int(max_hr_estimate * 0.50)
            zone2 = int(max_hr_estimate * 0.60)
            zone3 = int(max_hr_estimate * 0.70)
            zone4 = int(max_hr_estimate * 0.80)
            zone5 = int(max_hr_estimate * 0.90)

            # Count time in zones
            zone_counts = {
                "Rest (<50%)": sum(1 for hr in hr_values if hr < zone1),
                "Zone 1 (50-60%)": sum(1 for hr in hr_values if zone1 <= hr < zone2),
                "Zone 2 (60-70%)": sum(1 for hr in hr_values if zone2 <= hr < zone3),
                "Zone 3 (70-80%)": sum(1 for hr in hr_values if zone3 <= hr < zone4),
                "Zone 4 (80-90%)": sum(1 for hr in hr_values if zone4 <= hr < zone5),
                "Zone 5 (90%+)": sum(1 for hr in hr_values if hr >= zone5),
            }

            result += f"## HR Zones Distribution\n"
            for zone, count in zone_counts.items():
                pct = (count / len(hr_values) * 100) if hr_values else 0
                result += f"- **{zone}:** {count} points ({pct:.1f}%)\n"
            result += "\n"

        # Group by source
        by_source = {}
        for point in hr_data:
            source = point.get("source", "unknown")
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(point.get("bpm"))

        if by_source:
            result += f"## By Activity Type\n"
            for source, values in by_source.items():
                if values:
                    avg = sum(values) / len(values)
                    result += f"- **{source.title()}:** {len(values)} points, avg {avg:.0f} bpm\n"

        return result

    async def get_workout_sessions(self, days: int) -> str:
        """Get detailed workout sessions."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        # Get workout sessions
        sessions = await self.oura_client.get_sessions(start_date, end_date)

        if not sessions:
            return f"No workout sessions available for the last {days} days"

        result = f"# 🏋️ Workout Sessions (Last {days} days)\n\n"
        result += f"**Retrieved {len(sessions)} sessions**\n\n"

        # Sort by date
        sessions_sorted = sorted(sessions, key=lambda s: s.get("day", ""), reverse=True)

        for session in sessions_sorted:
            day = session.get("day", "Unknown")
            start_time = session.get("start_datetime", "")
            if start_time:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                time_str = start_dt.strftime("%H:%M")
            else:
                time_str = "N/A"

            session_type = session.get("type", "Unknown")

            result += f"## 📅 {day} at {time_str}\n\n"
            result += f"**Type:** {session_type}\n\n"

            # Duration
            duration_seconds = session.get("total_duration", 0)
            if duration_seconds:
                hours = duration_seconds // 3600
                minutes = (duration_seconds % 3600) // 60
                if hours > 0:
                    result += f"**Duration:** {hours}h {minutes}m\n"
                else:
                    result += f"**Duration:** {minutes}m\n"

            # Heart rate metrics
            avg_hr = session.get("heart_rate", {}).get("average")
            max_hr = session.get("heart_rate", {}).get("maximum")
            if avg_hr:
                result += f"**Avg HR:** {avg_hr} bpm\n"
            if max_hr:
                result += f"**Max HR:** {max_hr} bpm\n"

            # Calories
            calories = session.get("calories", 0)
            if calories:
                result += f"**Calories:** {calories} kcal\n"

            # Distance (if available)
            distance = session.get("distance", 0)
            if distance:
                result += f"**Distance:** {distance / 1000:.2f} km\n"

            result += "\n---\n\n"

        return result

    async def get_daily_stress(self, days: int) -> str:
        """Get daily stress data."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        # Get stress data
        stress_data = await self.oura_client.get_daily_stress(start_date, end_date)

        if not stress_data:
            return f"⚠️ No stress data available for the last {days} days\n\n*Note: Stress tracking may not be available for your Oura ring generation or requires opt-in.*"

        result = f"# 😰 Daily Stress (Last {days} days)\n\n"
        result += f"**Retrieved {len(stress_data)} records**\n\n"

        # Calculate averages
        day_summaries = []
        for record in stress_data:
            day = record.get("day", "Unknown")
            day_summary = record.get("day_summary")

            # Check if day_summary is a dict and has the required fields
            if day_summary and isinstance(day_summary, dict):
                stress_high = day_summary.get("stress_high", 0)
                recovery_high = day_summary.get("recovery_high", 0)

                day_summaries.append({
                    "day": day,
                    "stress_high": stress_high,
                    "recovery_high": recovery_high
                })

        if day_summaries:
            avg_stress = sum(d["stress_high"] for d in day_summaries) / len(day_summaries)
            avg_recovery = sum(d["recovery_high"] for d in day_summaries) / len(day_summaries)

            result += f"## Average (Period)\n"
            result += f"- **Stress Time:** {avg_stress / 60:.1f} hours/day\n"
            result += f"- **Recovery Time:** {avg_recovery / 60:.1f} hours/day\n\n"

        result += f"## Daily Breakdown\n\n"
        for record in day_summaries:
            result += f"### {record['day']}\n"
            result += f"- **High Stress:** {record['stress_high'] // 60}h {record['stress_high'] % 60}m\n"
            result += f"- **High Recovery:** {record['recovery_high'] // 60}h {record['recovery_high'] % 60}m\n\n"

        return result

    async def get_spo2_data(self, days: int) -> str:
        """Get SpO2 (blood oxygen saturation) data."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        # Get SpO2 data
        spo2_data = await self.oura_client.get_daily_spo2(start_date, end_date)

        if not spo2_data:
            return f"⚠️ No SpO2 data available for the last {days} days\n\n*Note: SpO2 tracking requires Oura Ring Gen 3 and may need to be enabled in settings.*"

        result = f"# 🫁 Blood Oxygen (SpO2) Data (Last {days} days)\n\n"
        result += f"**Retrieved {len(spo2_data)} records**\n\n"

        # Calculate statistics
        spo2_values = [r.get("spo2_percentage", {}).get("average") for r in spo2_data if r.get("spo2_percentage", {}).get("average")]

        if spo2_values:
            avg_spo2 = sum(spo2_values) / len(spo2_values)
            min_spo2 = min(spo2_values)
            max_spo2 = max(spo2_values)

            result += f"## Summary\n"
            result += f"- **Average SpO2:** {avg_spo2:.1f}%\n"
            result += f"- **Range:** {min_spo2:.1f}% - {max_spo2:.1f}%\n\n"

            # Interpretation
            if avg_spo2 >= 95:
                status = "✅ Normal"
                note = "Your blood oxygen levels are within normal range."
            elif avg_spo2 >= 90:
                status = "⚠️ Borderline"
                note = "Slightly below normal. Monitor for patterns."
            else:
                status = "🔴 Low"
                note = "Consistently low SpO2. Consider consulting a healthcare provider."

            result += f"**Status:** {status}\n"
            result += f"*{note}*\n\n"

        result += f"## Daily Values\n\n"
        for record in spo2_data:
            day = record.get("day", "Unknown")
            spo2_avg = record.get("spo2_percentage", {}).get("average")
            if spo2_avg:
                result += f"- **{day}:** {spo2_avg:.1f}%\n"

        return result

    async def get_vo2_max(self, days: int) -> str:
        """Get VO2 Max data."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        # Get VO2 Max data
        try:
            vo2_data = await self.oura_client.get_vo2_max(start_date, end_date)
        except Exception as e:
            # API returns 404 if feature not available or no data yet
            if "404" in str(e):
                return f"⚠️ VO2 Max not available\n\n*Note: VO2 Max requires:\n- Oura Ring Gen 3\n- Regular cardio activity tracking\n- Several days of data to calculate initial estimate*"
            raise

        if not vo2_data:
            return f"⚠️ No VO2 Max data available for the last {days} days\n\n*Note: VO2 Max requires regular cardio activity tracking and may take several days to calculate.*"

        result = f"# 🏃 VO2 Max (Last {days} days)\n\n"
        result += f"**Retrieved {len(vo2_data)} estimates**\n\n"

        # Get latest estimate
        if vo2_data:
            latest = vo2_data[-1]
            vo2_value = latest.get("vo2_max")
            day = latest.get("day", "Unknown")

            if vo2_value:
                result += f"## Latest Estimate ({day})\n"
                result += f"**VO2 Max:** {vo2_value:.1f} ml/kg/min\n\n"

                # Fitness level interpretation (approximate, for age 30-40)
                if vo2_value >= 45:
                    level = "Excellent 🏆"
                elif vo2_value >= 38:
                    level = "Good 💪"
                elif vo2_value >= 32:
                    level = "Average 👍"
                elif vo2_value >= 25:
                    level = "Below Average 📉"
                else:
                    level = "Poor 🔴"

                result += f"**Fitness Level:** {level}\n\n"
                result += f"*Note: Fitness levels vary by age and sex. This is a general estimate.*\n\n"

        # Show trend
        result += f"## Historical Values\n\n"
        for record in vo2_data:
            day = record.get("day", "Unknown")
            vo2_value = record.get("vo2_max")
            if vo2_value:
                result += f"- **{day}:** {vo2_value:.1f} ml/kg/min\n"

        return result

    async def get_tags(self, days: int) -> str:
        """Get user-created tags."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        # Get tags
        tags = await self.oura_client.get_tags(start_date, end_date)

        if not tags:
            return f"No tags found for the last {days} days\n\n*Create tags in the Oura app to track activities, symptoms, or notes.*"

        result = f"# 🏷️ Tags & Notes (Last {days} days)\n\n"
        result += f"**Retrieved {len(tags)} tags**\n\n"

        # Group by day
        tags_by_day = {}
        for tag in tags:
            day = tag.get("day", "Unknown")
            if day not in tags_by_day:
                tags_by_day[day] = []
            tags_by_day[day].append(tag)

        # Display by day
        for day in sorted(tags_by_day.keys(), reverse=True):
            result += f"## 📅 {day}\n\n"
            for tag in tags_by_day[day]:
                tag_type = tag.get("tag_type_code", "unknown")
                text = tag.get("text", "")

                result += f"- **{tag_type}**"
                if text:
                    result += f": {text}"
                result += "\n"
            result += "\n"

        return result
