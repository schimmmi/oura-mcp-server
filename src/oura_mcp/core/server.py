"""MCP Server implementation for Oura Ring data."""

import os
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from ..api.client import OuraClient
from ..utils.config import Config, get_config
from ..utils.logging import get_logger, setup_logging
from ..utils.baselines import BaselineManager
from ..utils.anomalies import AnomalyDetector
from ..utils.interpretation import InterpretationEngine


logger = get_logger(__name__)


class OuraMCPServer:
    """
    MCP Server for Oura Ring data.
    
    Provides resources and tools for AI assistants to access
    and analyze health metrics.
    """
    
    def __init__(self, config: Config):
        """
        Initialize MCP server.

        Args:
            config: Server configuration
        """
        self.config = config
        self.server = Server(config.mcp.server.name)
        self.oura_client: OuraClient = None

        # Initialize intelligence components
        self.baseline_manager = BaselineManager()
        self.anomaly_detector = AnomalyDetector(self.baseline_manager)
        self.interpreter = InterpretationEngine()

        # Register handlers
        self._register_resources()
        self._register_tools()

        logger.info(f"Initialized {config.mcp.server.name} v{config.mcp.server.version}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        # Initialize Oura client
        self.oura_client = OuraClient(self.config.oura.api)
        await self.oura_client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.oura_client:
            await self.oura_client.__aexit__(exc_type, exc_val, exc_tb)
    
    def _register_resources(self):
        """Register MCP resources."""
        
        @self.server.list_resources()
        async def list_resources():
            """List available resources."""
            resources = []
            
            if "sleep" in self.config.mcp.resources.enabled:
                resources.extend([
                    {
                        "uri": "oura://sleep/today",
                        "name": "Today's Sleep",
                        "mimeType": "application/json",
                        "description": "Sleep data for last night"
                    },
                    {
                        "uri": "oura://sleep/yesterday",
                        "name": "Yesterday's Sleep",
                        "mimeType": "application/json",
                        "description": "Sleep data from the night before"
                    },
                ])
            
            if "readiness" in self.config.mcp.resources.enabled:
                resources.append({
                    "uri": "oura://readiness/today",
                    "name": "Today's Readiness",
                    "mimeType": "application/json",
                    "description": "Readiness score and contributing factors"
                })
            
            if "activity" in self.config.mcp.resources.enabled:
                resources.append({
                    "uri": "oura://activity/today",
                    "name": "Today's Activity",
                    "mimeType": "application/json",
                    "description": "Activity data for today"
                })

            if "hrv" in self.config.mcp.resources.enabled:
                resources.extend([
                    {
                        "uri": "oura://hrv/latest",
                        "name": "Latest HRV",
                        "mimeType": "application/json",
                        "description": "Most recent HRV data with baseline comparison"
                    },
                    {
                        "uri": "oura://hrv/trend/7_days",
                        "name": "HRV Trend (7 days)",
                        "mimeType": "application/json",
                        "description": "HRV trend over last 7 days"
                    },
                    {
                        "uri": "oura://hrv/trend/30_days",
                        "name": "HRV Trend (30 days)",
                        "mimeType": "application/json",
                        "description": "HRV trend over last 30 days"
                    }
                ])

            # Add personal info resource
            resources.append({
                "uri": "oura://personal_info",
                "name": "Personal Information",
                "mimeType": "application/json",
                "description": "User profile (age, weight, height, biological sex)"
            })

            # Add stress resource
            resources.append({
                "uri": "oura://stress/today",
                "name": "Today's Stress",
                "mimeType": "application/json",
                "description": "Daytime stress levels and recovery time"
            })

            # Add SpO2 resource
            resources.append({
                "uri": "oura://spo2/latest",
                "name": "Latest SpO2",
                "mimeType": "application/json",
                "description": "Blood oxygen saturation during sleep"
            })

            return resources
        
        @self.server.read_resource()
        async def read_resource(uri: str):
            """Read a specific resource."""
            logger.info(f"Reading resource: {uri}")
            
            try:
                # Parse URI
                if uri.startswith("oura://sleep/"):
                    period = uri.split("/")[-1]
                    return await self._get_sleep_resource(period)
                
                elif uri.startswith("oura://readiness/"):
                    period = uri.split("/")[-1]
                    return await self._get_readiness_resource(period)
                
                elif uri.startswith("oura://activity/"):
                    period = uri.split("/")[-1]
                    return await self._get_activity_resource(period)

                elif uri.startswith("oura://hrv/"):
                    # Parse: oura://hrv/latest or oura://hrv/trend/7_days
                    parts = uri.replace("oura://hrv/", "").split("/")
                    if parts[0] == "latest":
                        return await self._get_hrv_resource("latest")
                    elif parts[0] == "trend":
                        period = parts[1] if len(parts) > 1 else "7_days"
                        return await self._get_hrv_resource(f"trend_{period}")
                    else:
                        raise ValueError(f"Unknown HRV resource: {uri}")

                elif uri == "oura://personal_info":
                    return await self._get_personal_info_resource()

                elif uri.startswith("oura://stress/"):
                    period = uri.split("/")[-1]
                    return await self._get_stress_resource(period)

                elif uri.startswith("oura://spo2/"):
                    period = uri.split("/")[-1]
                    return await self._get_spo2_resource(period)

                else:
                    raise ValueError(f"Unknown resource URI: {uri}")
            
            except Exception as e:
                logger.error(f"Error reading resource {uri}: {e}")
                raise
    
    def _register_tools(self):
        """Register MCP tools."""
        
        @self.server.list_tools()
        async def list_tools():
            """List available tools."""
            tools = []

            if "generate_daily_brief" in self.config.mcp.tools.enabled:
                tools.append(types.Tool(
                    name="generate_daily_brief",
                    description="Generate comprehensive daily health brief",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    }
                ))

            if "analyze_sleep_trend" in self.config.mcp.tools.enabled:
                tools.append(types.Tool(
                    name="analyze_sleep_trend",
                    description="Analyze sleep patterns over specified period",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "days": {
                                "type": "integer",
                                "description": "Number of days to analyze",
                                "default": 7
                            }
                        }
                    }
                ))

            if "detect_recovery_status" in self.config.mcp.tools.enabled:
                tools.append(types.Tool(
                    name="detect_recovery_status",
                    description="Assess current recovery state based on multiple physiological signals",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    }
                ))

            if "assess_training_readiness" in self.config.mcp.tools.enabled:
                tools.append(types.Tool(
                    name="assess_training_readiness",
                    description="Assess readiness for specific types of training",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "training_type": {
                                "type": "string",
                                "description": "Type of training: general, endurance, strength, high_intensity",
                                "enum": ["general", "endurance", "strength", "high_intensity"],
                                "default": "general"
                            }
                        }
                    }
                ))

            if "correlate_metrics" in self.config.mcp.tools.enabled:
                tools.append(types.Tool(
                    name="correlate_metrics",
                    description="Find correlations between two metrics over specified period",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "metric1": {
                                "type": "string",
                                "description": "First metric (e.g., 'activity_score', 'sleep_score', 'hrv_balance')"
                            },
                            "metric2": {
                                "type": "string",
                                "description": "Second metric (e.g., 'readiness_score', 'resting_heart_rate')"
                            },
                            "days": {
                                "type": "integer",
                                "description": "Number of days to analyze",
                                "default": 30
                            }
                        },
                        "required": ["metric1", "metric2"]
                    }
                ))

            if "detect_anomalies" in self.config.mcp.tools.enabled:
                tools.append(types.Tool(
                    name="detect_anomalies",
                    description="Detect statistical anomalies in metrics over recent period",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "metric_type": {
                                "type": "string",
                                "description": "Type of metric to analyze: sleep, readiness, activity",
                                "enum": ["sleep", "readiness", "activity"],
                                "default": "sleep"
                            },
                            "days": {
                                "type": "integer",
                                "description": "Number of days to analyze",
                                "default": 7
                            }
                        }
                    }
                ))

            # Add debug tool to see raw data
            tools.append(types.Tool(
                name="get_raw_sleep_data",
                description="Get raw sleep data from Oura API for debugging (shows last N days)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "days": {
                            "type": "integer",
                            "description": "Number of days to retrieve",
                            "default": 3
                        }
                    }
                }
            ))

            # Add detailed sleep sessions tool
            tools.append(types.Tool(
                name="get_sleep_sessions",
                description="Get detailed sleep sessions with exact times and durations (includes all sleep periods like naps, couch sleep, etc.)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "days": {
                            "type": "integer",
                            "description": "Number of days to retrieve",
                            "default": 3
                        }
                    }
                }
            ))

            # Add heart rate tool
            tools.append(types.Tool(
                name="get_heart_rate_data",
                description="Get time-series heart rate data with HR zones and patterns",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "hours": {
                            "type": "integer",
                            "description": "Number of hours to retrieve",
                            "default": 24
                        }
                    }
                }
            ))

            # Add workout sessions tool
            tools.append(types.Tool(
                name="get_workout_sessions",
                description="Get detailed workout/activity sessions with HR data and metrics",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "days": {
                            "type": "integer",
                            "description": "Number of days to retrieve",
                            "default": 7
                        }
                    }
                }
            ))

            # Add daily stress tool
            tools.append(types.Tool(
                name="get_daily_stress",
                description="Get daily stress levels, stress load, and recovery time",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "days": {
                            "type": "integer",
                            "description": "Number of days to retrieve",
                            "default": 7
                        }
                    }
                }
            ))

            # Add SpO2 tool
            tools.append(types.Tool(
                name="get_spo2_data",
                description="Get blood oxygen saturation (SpO2) data during sleep",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "days": {
                            "type": "integer",
                            "description": "Number of days to retrieve",
                            "default": 7
                        }
                    }
                }
            ))

            # Add VO2 Max tool
            tools.append(types.Tool(
                name="get_vo2_max",
                description="Get VO2 Max (cardiorespiratory fitness) estimates",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "days": {
                            "type": "integer",
                            "description": "Number of days to retrieve",
                            "default": 30
                        }
                    }
                }
            ))

            # Add tags tool
            tools.append(types.Tool(
                name="get_tags",
                description="Get user-created tags and notes",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "days": {
                            "type": "integer",
                            "description": "Number of days to retrieve",
                            "default": 7
                        }
                    }
                }
            ))

            return tools
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]):
            """Execute a tool."""
            logger.info(f"Calling tool: {name} with args: {arguments}")

            try:
                if name == "generate_daily_brief":
                    result = await self._tool_generate_daily_brief()
                    return [types.TextContent(type="text", text=result)]

                elif name == "analyze_sleep_trend":
                    days = arguments.get("days", 7)
                    result = await self._tool_analyze_sleep_trend(days)
                    return [types.TextContent(type="text", text=result)]

                elif name == "get_raw_sleep_data":
                    days = arguments.get("days", 3)
                    result = await self._tool_get_raw_sleep_data(days)
                    return [types.TextContent(type="text", text=result)]

                elif name == "detect_recovery_status":
                    result = await self._tool_detect_recovery_status()
                    return [types.TextContent(type="text", text=result)]

                elif name == "assess_training_readiness":
                    training_type = arguments.get("training_type", "general")
                    result = await self._tool_assess_training_readiness(training_type)
                    return [types.TextContent(type="text", text=result)]

                elif name == "correlate_metrics":
                    metric1 = arguments.get("metric1")
                    metric2 = arguments.get("metric2")
                    days = arguments.get("days", 30)
                    result = await self._tool_correlate_metrics(metric1, metric2, days)
                    return [types.TextContent(type="text", text=result)]

                elif name == "detect_anomalies":
                    metric_type = arguments.get("metric_type", "sleep")
                    days = arguments.get("days", 7)
                    result = await self._tool_detect_anomalies(metric_type, days)
                    return [types.TextContent(type="text", text=result)]

                elif name == "get_sleep_sessions":
                    days = arguments.get("days", 3)
                    result = await self._tool_get_sleep_sessions(days)
                    return [types.TextContent(type="text", text=result)]

                elif name == "get_heart_rate_data":
                    hours = arguments.get("hours", 24)
                    result = await self._tool_get_heart_rate_data(hours)
                    return [types.TextContent(type="text", text=result)]

                elif name == "get_workout_sessions":
                    days = arguments.get("days", 7)
                    result = await self._tool_get_workout_sessions(days)
                    return [types.TextContent(type="text", text=result)]

                elif name == "get_daily_stress":
                    days = arguments.get("days", 7)
                    result = await self._tool_get_daily_stress(days)
                    return [types.TextContent(type="text", text=result)]

                elif name == "get_spo2_data":
                    days = arguments.get("days", 7)
                    result = await self._tool_get_spo2_data(days)
                    return [types.TextContent(type="text", text=result)]

                elif name == "get_vo2_max":
                    days = arguments.get("days", 30)
                    result = await self._tool_get_vo2_max(days)
                    return [types.TextContent(type="text", text=result)]

                elif name == "get_tags":
                    days = arguments.get("days", 7)
                    result = await self._tool_get_tags(days)
                    return [types.TextContent(type="text", text=result)]

                else:
                    raise ValueError(f"Unknown tool: {name}")

            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}")
                raise
    
    # === Resource Implementations ===
    
    async def _get_sleep_resource(self, period: str) -> str:
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
        return self._format_sleep_semantic_detailed(
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
    
    async def _get_readiness_resource(self, period: str) -> str:
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
        return self._format_readiness_semantic(readiness_data)
    
    async def _get_activity_resource(self, period: str) -> str:
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
        return self._format_activity_semantic(activity_data)

    async def _get_hrv_resource(self, period: str) -> str:
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

            return self._format_hrv_latest(readiness_data[-1], baseline_data)

        elif period.startswith("trend_"):
            days_str = period.replace("trend_", "").replace("_days", "")
            days = int(days_str)

            start_date = today - timedelta(days=days)
            readiness_data = await self.oura_client.get_daily_readiness(start_date, today)

            if not readiness_data:
                return f"No HRV data available for the last {days} days"

            return self._format_hrv_trend(readiness_data, days)

        else:
            raise ValueError(f"Unknown HRV period: {period}")

    async def _get_personal_info_resource(self) -> str:
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

    async def _get_stress_resource(self, period: str) -> str:
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

    async def _get_spo2_resource(self, period: str) -> str:
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

    # === Tool Implementations ===
    
    async def _tool_generate_daily_brief(self) -> str:
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
    
    async def _tool_analyze_sleep_trend(self, days: int) -> str:
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

    async def _tool_get_raw_sleep_data(self, days: int) -> str:
        """Get raw sleep data from Oura API for debugging."""
        import json

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

    async def _tool_get_sleep_sessions(self, days: int) -> str:
        """Get detailed sleep sessions with exact times and durations."""
        from datetime import datetime

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

    async def _tool_get_heart_rate_data(self, hours: int) -> str:
        """Get time-series heart rate data."""
        from datetime import datetime

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

    async def _tool_get_workout_sessions(self, days: int) -> str:
        """Get detailed workout sessions."""
        from datetime import datetime

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

    async def _tool_get_daily_stress(self, days: int) -> str:
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

            if day_summary:
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

    async def _tool_get_spo2_data(self, days: int) -> str:
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

    async def _tool_get_vo2_max(self, days: int) -> str:
        """Get VO2 Max data."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        # Get VO2 Max data
        vo2_data = await self.oura_client.get_vo2_max(start_date, end_date)

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

    async def _tool_get_tags(self, days: int) -> str:
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

    async def _tool_detect_recovery_status(self) -> str:
        """Detect current recovery status based on multiple signals."""
        import json
        today = date.today()

        # Gather all relevant data
        readiness_data = await self.oura_client.get_daily_readiness(today, today)
        sleep_data = await self.oura_client.get_daily_sleep(today, today)

        if not readiness_data:
            return "⚠️ No readiness data available for today"

        readiness = readiness_data[-1]
        contributors = readiness.get("contributors", {})

        # Extract key metrics
        readiness_score = readiness.get("score", 0)
        hrv_balance = contributors.get("hrv_balance", 50)
        resting_hr = contributors.get("resting_heart_rate", 50)
        temp_score = contributors.get("body_temperature", 100)

        sleep_score = sleep_data[-1].get("score", 70) if sleep_data else 70

        # Get baselines for context
        baseline_start = today - timedelta(days=30)
        baseline_readiness = await self.oura_client.get_daily_readiness(baseline_start, today)
        baselines = self.baseline_manager.calculate_readiness_baselines(baseline_readiness)

        # Interpret recovery state
        recovery_state = self.interpreter.interpret_recovery_state(
            readiness=readiness_score,
            hrv_balance=hrv_balance,
            resting_hr_deviation=0,  # We'd need to calculate this from baseline
            sleep_score=sleep_score,
            temperature_score=temp_score
        )

        # Format output
        result = "# 🏥 Recovery Status Assessment\n\n"
        result += f"**Overall State:** {recovery_state['emoji']} {recovery_state['state']}\n"
        result += f"**Recovery Score:** {recovery_state['recovery_score']}/100\n"
        result += f"**Confidence:** {recovery_state['confidence']*100:.0f}%\n\n"

        result += f"## Description\n{recovery_state['description']}\n\n"

        result += f"## Training Recommendation\n{recovery_state['training_recommendation']}\n\n"

        result += "## Contributing Signals\n\n"
        for signal_name, signal_data in recovery_state['signals'].items():
            name_display = signal_name.replace("_", " ").title()
            if 'value' in signal_data:
                result += f"- **{name_display}:** {signal_data['value']} (weight: {signal_data['weight']}, impact: {signal_data['impact']})\n"
            else:
                result += f"- **{name_display}:** {signal_data.get('deviation', 'N/A')} bpm deviation (weight: {signal_data['weight']})\n"

        result += "\n"

        # Add HRV interpretation
        hrv_interp = self.interpreter.interpret_hrv_balance(
            hrv_balance,
            baselines.get("hrv_balance", {}).get("mean")
        )
        result += f"## HRV Analysis\n"
        result += f"{hrv_interp['emoji']} **Status:** {hrv_interp['status']}\n"
        result += f"- {hrv_interp['description']}\n"
        result += f"- {hrv_interp['meaning']}\n"
        result += f"- **Implications:** {hrv_interp['implications']}\n"

        if 'baseline_status' in hrv_interp:
            result += f"- **Baseline:** {hrv_interp['baseline_status']}\n"

        return result

    async def _tool_assess_training_readiness(self, training_type: str) -> str:
        """Assess readiness for specific training type."""
        today = date.today()

        # Get recovery state first
        readiness_data = await self.oura_client.get_daily_readiness(today, today)
        sleep_data = await self.oura_client.get_daily_sleep(today, today)

        if not readiness_data:
            return "⚠️ No readiness data available for today"

        readiness = readiness_data[-1]
        contributors = readiness.get("contributors", {})
        readiness_score = readiness.get("score", 0)

        # Build recovery state
        recovery_state = self.interpreter.interpret_recovery_state(
            readiness=readiness_score,
            hrv_balance=contributors.get("hrv_balance", 50),
            resting_hr_deviation=0,
            sleep_score=sleep_data[-1].get("score", 70) if sleep_data else 70,
            temperature_score=contributors.get("body_temperature", 100)
        )

        # Get training-specific assessment
        assessment = self.interpreter.assess_training_readiness(
            readiness=readiness_score,
            recovery_state=recovery_state,
            training_type=training_type
        )

        # Format output
        result = f"# 🏋️ Training Readiness Assessment\n\n"
        result += f"**Training Type:** {assessment['training_type']}\n"
        result += f"**Recommendation:** {assessment['emoji']} {assessment['go_nogo']}\n"
        result += f"**Confidence:** {assessment['confidence']}\n\n"

        result += f"## Readiness Scores\n"
        result += f"- **Readiness Score:** {assessment['readiness_score']}/100\n"
        result += f"- **Recovery Score:** {assessment['recovery_score']}/100\n\n"

        result += f"## Recommendations\n"
        result += f"- **Intensity:** {assessment['intensity']}\n"
        result += f"- **Duration:** {assessment['duration']}\n\n"

        if assessment['modifications']:
            result += f"## Suggested Modifications\n"
            for mod in assessment['modifications']:
                result += f"- {mod}\n"
            result += "\n"

        result += f"## Limiting Factors\n"
        for factor in assessment['key_factors']:
            result += f"- {factor}\n"

        return result

    async def _tool_correlate_metrics(self, metric1: str, metric2: str, days: int) -> str:
        """Find correlations between two metrics."""
        import statistics

        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        # Gather data
        sleep_data = await self.oura_client.get_daily_sleep(start_date, end_date)
        readiness_data = await self.oura_client.get_daily_readiness(start_date, end_date)
        activity_data = await self.oura_client.get_daily_activity(start_date, end_date)

        # Extract metric values
        def extract_metric(records, metric_name):
            values = []

            # List of contributor metrics (appear in contributors dict)
            sleep_contributors = ["deep_sleep", "rem_sleep", "light_sleep", "total_sleep",
                                 "efficiency", "restfulness", "latency", "timing"]
            readiness_contributors = ["hrv_balance", "resting_heart_rate", "body_temperature",
                                     "activity_balance", "previous_day_activity", "previous_night",
                                     "recovery_index", "sleep_balance", "sleep_regularity"]
            activity_contributors = ["meet_daily_targets", "move_every_hour", "recovery_time",
                                    "stay_active", "training_frequency", "training_volume"]

            for record in records:
                val = None

                # Check for score fields
                if metric_name == "sleep_score":
                    val = record.get("score")
                elif metric_name == "readiness_score":
                    val = record.get("score")
                elif metric_name == "activity_score":
                    val = record.get("score")
                # Check contributors
                elif metric_name in sleep_contributors or metric_name in readiness_contributors or metric_name in activity_contributors:
                    val = record.get("contributors", {}).get(metric_name)
                # Check direct fields (like steps, calories)
                else:
                    val = record.get(metric_name)

                if val is not None:
                    values.append(float(val))
            return values

        # Determine which dataset to use for each metric
        def get_data_for_metric(metric):
            if "sleep" in metric:
                return sleep_data
            elif "readiness" in metric or "hrv" in metric or "heart_rate" in metric or "temperature" in metric:
                return readiness_data
            elif "activity" in metric or "steps" in metric:
                return activity_data
            else:
                return readiness_data  # Default

        data1 = get_data_for_metric(metric1)
        data2 = get_data_for_metric(metric2)

        values1 = extract_metric(data1, metric1)
        values2 = extract_metric(data2, metric2)

        if not values1 or not values2:
            return f"⚠️ Insufficient data for correlation analysis\n- {metric1}: {len(values1)} values\n- {metric2}: {len(values2)} values"

        # Align datasets (use minimum length)
        min_len = min(len(values1), len(values2))
        values1 = values1[-min_len:]
        values2 = values2[-min_len:]

        # Calculate correlation (Pearson)
        if min_len < 2:
            return "⚠️ Not enough data points for correlation analysis (need at least 2)"

        mean1 = statistics.mean(values1)
        mean2 = statistics.mean(values2)

        covariance = sum((x - mean1) * (y - mean2) for x, y in zip(values1, values2)) / min_len
        std1 = statistics.stdev(values1) if len(values1) > 1 else 0
        std2 = statistics.stdev(values2) if len(values2) > 1 else 0

        if std1 == 0 or std2 == 0:
            correlation = 0
        else:
            correlation = covariance / (std1 * std2)

        # Interpret correlation
        if abs(correlation) > 0.7:
            strength = "Strong"
            emoji = "🔴"
        elif abs(correlation) > 0.5:
            strength = "Moderate"
            emoji = "🟡"
        elif abs(correlation) > 0.3:
            strength = "Weak"
            emoji = "🟢"
        else:
            strength = "Very Weak/None"
            emoji = "⚪"

        direction = "positive" if correlation > 0 else "negative"

        # Format output
        result = f"# 📊 Correlation Analysis ({days} days)\n\n"
        result += f"**Metrics:**\n"
        result += f"- {metric1.replace('_', ' ').title()}\n"
        result += f"- {metric2.replace('_', ' ').title()}\n\n"

        result += f"## Results\n"
        result += f"{emoji} **Correlation:** {correlation:+.3f}\n"
        result += f"**Strength:** {strength}\n"
        result += f"**Direction:** {direction}\n"
        result += f"**Data Points:** {min_len}\n\n"

        result += f"## Interpretation\n"
        if abs(correlation) > 0.5:
            result += f"These metrics show a {strength.lower()} {direction} relationship.\n"
            if correlation > 0:
                result += f"When {metric1} increases, {metric2} tends to increase as well.\n"
            else:
                result += f"When {metric1} increases, {metric2} tends to decrease.\n"
        else:
            result += f"These metrics show little to no clear relationship.\n"

        result += f"\n## Statistics\n"
        result += f"**{metric1.replace('_', ' ').title()}:**\n"
        result += f"- Mean: {mean1:.1f}\n"
        result += f"- Std Dev: {std1:.1f}\n"
        result += f"- Range: {min(values1):.1f} - {max(values1):.1f}\n\n"

        result += f"**{metric2.replace('_', ' ').title()}:**\n"
        result += f"- Mean: {mean2:.1f}\n"
        result += f"- Std Dev: {std2:.1f}\n"
        result += f"- Range: {min(values2):.1f} - {max(values2):.1f}\n"

        return result

    async def _tool_detect_anomalies(self, metric_type: str, days: int) -> str:
        """Detect anomalies in specified metric type."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        if metric_type == "sleep":
            current_data = await self.oura_client.get_daily_sleep(end_date, end_date)
            recent_data = await self.oura_client.get_daily_sleep(start_date, end_date)

            if not current_data or not recent_data:
                return "⚠️ Insufficient sleep data for anomaly detection"

            anomalies = self.anomaly_detector.detect_sleep_anomalies(
                current_data[-1],
                recent_data
            )

        elif metric_type == "readiness":
            current_data = await self.oura_client.get_daily_readiness(end_date, end_date)
            recent_data = await self.oura_client.get_daily_readiness(start_date, end_date)

            if not current_data or not recent_data:
                return "⚠️ Insufficient readiness data for anomaly detection"

            anomalies = self.anomaly_detector.detect_readiness_anomalies(
                current_data[-1],
                recent_data
            )

        else:
            return f"⚠️ Anomaly detection not yet implemented for {metric_type}"

        # Format output
        result = f"# 🔍 Anomaly Detection Report\n\n"
        result += f"**Period:** Last {days} days\n"
        result += f"**Metric Type:** {metric_type.title()}\n"
        result += f"**Date:** {end_date.isoformat()}\n\n"

        result += self.anomaly_detector.format_anomalies_report(anomalies)

        return result

    # === Semantic Formatters ===

    def _format_sleep_semantic_detailed(
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

    def _format_sleep_semantic(self, data: Dict[str, Any]) -> str:
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
    
    def _format_readiness_semantic(self, data: Dict[str, Any]) -> str:
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
    
    def _format_activity_semantic(self, data: Dict[str, Any]) -> str:
        """Format activity data semantically."""
        score = data.get("score", 0)

        result = f"# Activity Report\n\n"
        result += f"**Date:** {data.get('day')}\n"
        result += f"**Score:** {score}/100\n\n"
        result += f"- Steps: {data.get('steps', 0):,}\n"
        result += f"- Calories: {data.get('total_calories', 0)}\n"

        return result

    def _format_hrv_latest(
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

    def _format_hrv_trend(
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
    
    async def run(self):
        """Run the MCP server."""
        logger.info(f"Starting {self.config.mcp.server.name}...")
        
        async with self:
            if self.config.mcp.server.transport == "stdio":
                async with stdio_server() as (read_stream, write_stream):
                    await self.server.run(
                        read_stream,
                        write_stream,
                        self.server.create_initialization_options()
                    )
            else:
                raise NotImplementedError("Only stdio transport is currently supported")


async def start_server(config_path: Optional[str] = None):
    """
    Start the Oura MCP server.
    
    Args:
        config_path: Optional path to config file
    """
    # Load config
    if config_path:
        os.environ["OURA_MCP_CONFIG"] = config_path
    
    config = get_config()
    
    # Setup logging
    setup_logging(config.logging)
    
    # Create and run server
    server = OuraMCPServer(config)
    await server.run()
