"""Anomaly detection for Oura metrics."""

from datetime import date, timedelta
from typing import Dict, List, Optional, Any
from .baselines import BaselineManager


class AnomalyDetector:
    """
    Detects anomalies and unusual patterns in Oura data.
    
    Uses statistical analysis and domain knowledge to identify
    concerning deviations from personal baselines.
    """
    
    def __init__(self, baseline_manager: BaselineManager):
        """
        Initialize anomaly detector.
        
        Args:
            baseline_manager: Baseline manager for statistical context
        """
        self.baseline_manager = baseline_manager
    
    def detect_sleep_anomalies(
        self,
        current_sleep: Dict[str, Any],
        recent_sleep: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies in sleep data.
        
        Args:
            current_sleep: Most recent sleep record
            recent_sleep: Recent sleep records (for baseline)
            
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        # Calculate baselines
        baselines = self.baseline_manager.calculate_sleep_baselines(recent_sleep)
        
        # Check overall score
        current_score = current_sleep.get("score", 0)
        if "sleep_score" in baselines:
            score_interp = self.baseline_manager.interpret_deviation(
                current_score,
                baselines["sleep_score"]
            )
            
            if score_interp["status"] in ["moderately_abnormal", "highly_abnormal"]:
                severity = "high" if score_interp["status"] == "highly_abnormal" else "medium"
                anomalies.append({
                    "metric": "sleep_score",
                    "type": "significant_deviation",
                    "severity": severity,
                    "current_value": current_score,
                    "baseline_mean": score_interp["baseline_mean"],
                    "deviation": score_interp["deviation_absolute"],
                    "deviation_pct": score_interp["deviation_percentage"],
                    "message": f"Sleep score {current_score} is {abs(score_interp['deviation_percentage']):.0f}% {'below' if score_interp['deviation_percentage'] < 0 else 'above'} your 30-day average"
                })
        
        # Check contributors
        contributors = current_sleep.get("contributors", {})
        
        # Deep sleep is critical
        if "deep_sleep" in contributors and "deep_sleep" in baselines:
            deep_sleep = contributors["deep_sleep"]
            deep_interp = self.baseline_manager.interpret_deviation(
                deep_sleep,
                baselines["deep_sleep"]
            )
            
            if deep_interp["deviation_percentage"] < -30:  # >30% drop
                anomalies.append({
                    "metric": "deep_sleep",
                    "type": "significant_drop",
                    "severity": "high",
                    "current_value": deep_sleep,
                    "baseline_mean": deep_interp["baseline_mean"],
                    "deviation": deep_interp["deviation_absolute"],
                    "deviation_pct": deep_interp["deviation_percentage"],
                    "message": f"⚠️ Deep sleep score {deep_sleep} is {abs(deep_interp['deviation_percentage']):.0f}% below normal",
                    "possible_causes": [
                        "Stress or anxiety",
                        "Alcohol consumption",
                        "Late meals or caffeine",
                        "Environmental factors (noise, temperature)",
                        "Sleep apnea or breathing issues",
                        "Illness or inflammation"
                    ]
                })
        
        # Restfulness check
        if "restfulness" in contributors and "restfulness" in baselines:
            restfulness = contributors["restfulness"]
            rest_interp = self.baseline_manager.interpret_deviation(
                restfulness,
                baselines["restfulness"]
            )
            
            if rest_interp["deviation_percentage"] < -20:
                anomalies.append({
                    "metric": "restfulness",
                    "type": "increased_movement",
                    "severity": "medium",
                    "current_value": restfulness,
                    "baseline_mean": rest_interp["baseline_mean"],
                    "deviation": rest_interp["deviation_absolute"],
                    "deviation_pct": rest_interp["deviation_percentage"],
                    "message": f"Restfulness {restfulness} indicates more movement than usual",
                    "possible_causes": [
                        "Stress or worry",
                        "Uncomfortable sleeping environment",
                        "Sleep apnea events",
                        "Pain or discomfort",
                        "Caffeine or stimulants"
                    ]
                })
        
        return anomalies
    
    def detect_readiness_anomalies(
        self,
        current_readiness: Dict[str, Any],
        recent_readiness: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in readiness data."""
        anomalies = []
        
        baselines = self.baseline_manager.calculate_readiness_baselines(recent_readiness)
        
        # Check HRV balance
        contributors = current_readiness.get("contributors", {})
        
        if "hrv_balance" in contributors and "hrv_balance" in baselines:
            hrv = contributors["hrv_balance"]
            hrv_interp = self.baseline_manager.interpret_deviation(
                hrv,
                baselines["hrv_balance"]
            )
            
            if hrv < 50:  # Below 50 indicates poor HRV
                severity = "high" if hrv < 30 else "medium"
                anomalies.append({
                    "metric": "hrv_balance",
                    "type": "low_hrv",
                    "severity": severity,
                    "current_value": hrv,
                    "baseline_mean": hrv_interp["baseline_mean"],
                    "deviation": hrv_interp["deviation_absolute"],
                    "message": f"⚠️ HRV Balance {hrv} indicates incomplete recovery",
                    "possible_causes": [
                        "Accumulated fatigue",
                        "Stress (physical or mental)",
                        "Illness onset",
                        "Overtraining",
                        "Poor sleep quality",
                        "Dehydration"
                    ]
                })
        
        # Check body temperature
        if "body_temperature" in contributors:
            temp = contributors["body_temperature"]
            if temp is not None and temp < 85:  # Below 85 can indicate issues
                anomalies.append({
                    "metric": "body_temperature",
                    "type": "temperature_deviation",
                    "severity": "medium",
                    "current_value": temp,
                    "message": f"Body temperature score {temp} is lower than optimal",
                    "possible_causes": [
                        "Insufficient recovery",
                        "Hormonal changes",
                        "Possible illness",
                        "Overtraining"
                    ]
                })
        
        return anomalies
    
    def detect_consecutive_decline(
        self,
        metric_values: List[float],
        days: int = 3
    ) -> Optional[Dict[str, Any]]:
        """
        Detect if a metric has been declining for N consecutive days.
        
        Args:
            metric_values: List of recent values (newest first)
            days: Number of days to check
            
        Returns:
            Anomaly dict if pattern detected, None otherwise
        """
        if len(metric_values) < days:
            return None
        
        # Check if each day is worse than the previous
        declining = all(
            metric_values[i] < metric_values[i + 1]
            for i in range(days - 1)
        )
        
        if declining:
            total_drop = metric_values[0] - metric_values[days - 1]
            return {
                "type": "consecutive_decline",
                "severity": "high" if days >= 4 else "medium",
                "days": days,
                "total_drop": total_drop,
                "message": f"⚠️ Metric has declined for {days} consecutive days (total: {total_drop:.1f})"
            }
        
        return None
    
    def format_anomalies_report(
        self,
        anomalies: List[Dict[str, Any]]
    ) -> str:
        """
        Format anomalies into a human-readable report.
        
        Args:
            anomalies: List of detected anomalies
            
        Returns:
            Formatted report string
        """
        if not anomalies:
            return "✅ No significant anomalies detected"
        
        # Sort by severity
        severity_order = {"high": 0, "medium": 1, "low": 2}
        sorted_anomalies = sorted(
            anomalies,
            key=lambda x: severity_order.get(x.get("severity", "low"), 3)
        )
        
        report = f"## ⚠️ Anomalies Detected ({len(anomalies)})\n\n"
        
        for anom in sorted_anomalies:
            severity_emoji = {
                "high": "🔴",
                "medium": "🟡",
                "low": "🟢"
            }.get(anom.get("severity", "low"), "⚪")
            
            report += f"### {severity_emoji} {anom['metric'].replace('_', ' ').title()}\n\n"
            report += f"{anom['message']}\n\n"
            
            if "current_value" in anom and "baseline_mean" in anom:
                report += f"- **Current:** {anom['current_value']:.1f}\n"
                report += f"- **Baseline:** {anom['baseline_mean']:.1f}\n"
                report += f"- **Change:** {anom['deviation']:+.1f} ({anom.get('deviation_pct', 0):+.1f}%)\n\n"
            
            if "possible_causes" in anom:
                report += "**Possible causes:**\n"
                for cause in anom["possible_causes"]:
                    report += f"- {cause}\n"
                report += "\n"
        
        return report
