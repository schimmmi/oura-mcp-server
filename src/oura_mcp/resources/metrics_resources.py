"""Metrics-related MCP resources (stress, SpO2, personal info)."""

from datetime import date
from typing import Any

from ..api.client import OuraClient


class MetricsResourceProvider:
    """Provides metrics-related MCP resources."""

    def __init__(self, oura_client: OuraClient):
        self.oura_client = oura_client

    async def get_personal_info_resource(self) -> str:
        """Get personal information resource."""
        personal_info = await self.oura_client.get_personal_info()

        result = f"# 👤 Personal Information\n\n"

        age = personal_info.get("age")
        weight = personal_info.get("weight")
        height = personal_info.get("height")
        biological_sex = personal_info.get("biological_sex")
        email = personal_info.get("email")

        if age:
            result += f"- **Age:** {age} years\n"
        if weight:
            result += f"- **Weight:** {weight} kg\n"
        if height:
            result += f"- **Height:** {height / 100:.2f} m\n"
        if biological_sex:
            result += f"- **Biological Sex:** {biological_sex}\n"
        if email:
            result += f"- **Email:** {email}\n"

        return result

    async def get_stress_resource(self, period: str) -> str:
        """Get stress resource data."""
        today = date.today()

        if period == "today":
            start_date = today
            end_date = today
        else:
            raise ValueError(f"Unknown stress period: {period}")

        data = await self.oura_client.get_daily_stress(start_date, end_date)

        if not data:
            return "⚠️ No stress data available for today\n\n*Note: Stress tracking may not be available for your ring generation.*"

        stress_data = data[-1]
        day_summary = stress_data.get("day_summary", {})

        result = f"# 😰 Stress Report\n\n"
        result += f"**Date:** {stress_data.get('day')}\n\n"

        # Ensure day_summary is a dict
        if not isinstance(day_summary, dict):
            return "⚠️ Stress data format invalid\n\n*Note: Stress tracking may not be available for your ring generation.*"

        stress_high = day_summary.get("stress_high", 0)
        recovery_high = day_summary.get("recovery_high", 0)

        result += f"## Daytime Balance\n"
        result += f"- **High Stress Time:** {stress_high // 60}h {stress_high % 60}m\n"
        result += f"- **High Recovery Time:** {recovery_high // 60}h {recovery_high % 60}m\n\n"

        # Calculate ratio
        total_time = stress_high + recovery_high
        if total_time > 0:
            stress_pct = (stress_high / total_time * 100)
            recovery_pct = (recovery_high / total_time * 100)

            result += f"## Distribution\n"
            result += f"- **Stress:** {stress_pct:.1f}%\n"
            result += f"- **Recovery:** {recovery_pct:.1f}%\n\n"

            if stress_pct > 60:
                status = "🔴 High Stress Day"
                recommendation = "Consider relaxation techniques, reduce workload if possible"
            elif stress_pct > 40:
                status = "🟡 Moderate Stress"
                recommendation = "Balanced day, maintain healthy habits"
            else:
                status = "✅ Low Stress"
                recommendation = "Good balance, recovery time is adequate"

            result += f"**Status:** {status}\n"
            result += f"**Recommendation:** {recommendation}\n"

        return result

    async def get_spo2_resource(self, period: str) -> str:
        """Get SpO2 resource data."""
        today = date.today()

        if period == "latest":
            start_date = today
            end_date = today
        else:
            raise ValueError(f"Unknown SpO2 period: {period}")

        data = await self.oura_client.get_daily_spo2(start_date, end_date)

        if not data:
            return "⚠️ No SpO2 data available\n\n*Note: SpO2 tracking requires Oura Ring Gen 3.*"

        spo2_data = data[-1]

        result = f"# 🫁 Blood Oxygen (SpO2)\n\n"
        result += f"**Date:** {spo2_data.get('day')}\n\n"

        spo2_percentage = spo2_data.get("spo2_percentage", {})
        avg_spo2 = spo2_percentage.get("average")

        if avg_spo2:
            result += f"**Average SpO2:** {avg_spo2:.1f}%\n\n"

            if avg_spo2 >= 95:
                status = "✅ Normal"
                note = "Your blood oxygen levels are within normal range."
            elif avg_spo2 >= 90:
                status = "⚠️ Borderline"
                note = "Slightly below normal. Monitor for patterns and consider consulting a healthcare provider if persistent."
            else:
                status = "🔴 Low"
                note = "Consistently low SpO2. Consult a healthcare provider."

            result += f"**Status:** {status}\n"
            result += f"*{note}*\n"

        return result
