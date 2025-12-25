"""Baseline calculation and management for Oura metrics."""

from datetime import date, timedelta
from typing import Dict, List, Optional, Any
import statistics


class BaselineManager:
    """
    Manages rolling baselines for Oura metrics.
    
    Calculates 30-day rolling averages, standard deviations,
    and provides context for current values.
    """
    
    def __init__(self):
        """Initialize baseline manager."""
        self._cache: Dict[str, Any] = {}
    
    def calculate_baseline(
        self,
        values: List[float],
        metric_name: str
    ) -> Dict[str, float]:
        """
        Calculate baseline statistics for a metric.
        
        Args:
            values: List of metric values
            metric_name: Name of the metric
            
        Returns:
            Dictionary with baseline statistics
        """
        if not values:
            return {
                "mean": 0,
                "std_dev": 0,
                "min": 0,
                "max": 0,
                "count": 0
            }
        
        return {
            "mean": statistics.mean(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
            "min": min(values),
            "max": max(values),
            "count": len(values)
        }
    
    def calculate_sleep_baselines(
        self,
        sleep_data: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate baselines for all sleep metrics.
        
        Args:
            sleep_data: List of sleep records from API
            
        Returns:
            Dictionary of baselines by metric name
        """
        baselines = {}
        
        # Extract scores from contributors
        scores_by_metric: Dict[str, List[float]] = {
            "sleep_score": [],
            "total_sleep": [],
            "deep_sleep": [],
            "rem_sleep": [],
            "efficiency": [],
            "restfulness": [],
            "latency": [],
            "timing": []
        }
        
        for record in sleep_data:
            # Overall score
            if record.get("score"):
                scores_by_metric["sleep_score"].append(record["score"])
            
            # Contributors
            contributors = record.get("contributors", {})
            for metric, values in scores_by_metric.items():
                if metric != "sleep_score" and metric in contributors:
                    values.append(contributors[metric])
        
        # Calculate baselines for each metric
        for metric, values in scores_by_metric.items():
            if values:
                baselines[metric] = self.calculate_baseline(values, metric)
        
        return baselines
    
    def calculate_readiness_baselines(
        self,
        readiness_data: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, float]]:
        """Calculate baselines for readiness metrics."""
        baselines = {}
        
        scores_by_metric: Dict[str, List[float]] = {
            "readiness_score": [],
            "activity_balance": [],
            "body_temperature": [],
            "hrv_balance": [],
            "previous_day_activity": [],
            "previous_night": [],
            "recovery_index": [],
            "resting_heart_rate": [],
            "sleep_balance": [],
            "sleep_regularity": []
        }
        
        for record in readiness_data:
            # Overall score
            if record.get("score"):
                scores_by_metric["readiness_score"].append(record["score"])
            
            # Contributors
            contributors = record.get("contributors", {})
            for metric, values in scores_by_metric.items():
                if metric != "readiness_score" and metric in contributors:
                    value = contributors[metric]
                    # Skip None values
                    if value is not None:
                        values.append(value)
        
        # Calculate baselines
        for metric, values in scores_by_metric.items():
            if values:
                baselines[metric] = self.calculate_baseline(values, metric)
        
        return baselines
    
    def calculate_activity_baselines(
        self,
        activity_data: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, float]]:
        """Calculate baselines for activity metrics."""
        baselines = {}
        
        scores_by_metric: Dict[str, List[float]] = {
            "activity_score": [],
            "steps": [],
            "total_calories": [],
            "active_calories": []
        }
        
        for record in activity_data:
            if record.get("score"):
                scores_by_metric["activity_score"].append(record["score"])
            if record.get("steps"):
                scores_by_metric["steps"].append(record["steps"])
            if record.get("total_calories"):
                scores_by_metric["total_calories"].append(record["total_calories"])
            if record.get("active_calories"):
                scores_by_metric["active_calories"].append(record["active_calories"])
        
        for metric, values in scores_by_metric.items():
            if values:
                baselines[metric] = self.calculate_baseline(values, metric)
        
        return baselines
    
    def interpret_deviation(
        self,
        current_value: float,
        baseline: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Interpret how a current value deviates from baseline.
        
        Args:
            current_value: Current metric value
            baseline: Baseline statistics
            
        Returns:
            Interpretation dictionary
        """
        if not baseline or baseline["count"] == 0:
            return {
                "deviation_absolute": 0,
                "deviation_percentage": 0,
                "deviation_std": 0,
                "interpretation": "No baseline data available",
                "status": "unknown"
            }
        
        mean = baseline["mean"]
        std_dev = baseline["std_dev"]
        
        deviation_abs = current_value - mean
        deviation_pct = (deviation_abs / mean * 100) if mean != 0 else 0
        deviation_std = (deviation_abs / std_dev) if std_dev != 0 else 0
        
        # Determine status
        if abs(deviation_std) < 0.5:
            status = "normal"
            interpretation = "within normal range"
        elif abs(deviation_std) < 1.0:
            status = "slightly_abnormal"
            interpretation = "slightly " + ("above" if deviation_abs > 0 else "below") + " normal"
        elif abs(deviation_std) < 1.5:
            status = "moderately_abnormal"
            interpretation = "moderately " + ("elevated" if deviation_abs > 0 else "decreased")
        else:
            status = "highly_abnormal"
            interpretation = "significantly " + ("elevated" if deviation_abs > 0 else "decreased")
        
        return {
            "deviation_absolute": round(deviation_abs, 1),
            "deviation_percentage": round(deviation_pct, 1),
            "deviation_std": round(deviation_std, 2),
            "interpretation": interpretation,
            "status": status,
            "baseline_mean": round(mean, 1),
            "baseline_range": f"{round(baseline['min'], 1)}-{round(baseline['max'], 1)}"
        }
    
    def format_baseline_summary(
        self,
        metric_name: str,
        current_value: float,
        baseline: Dict[str, float]
    ) -> str:
        """
        Format a human-readable baseline summary.
        
        Args:
            metric_name: Name of metric
            current_value: Current value
            baseline: Baseline statistics
            
        Returns:
            Formatted string
        """
        interp = self.interpret_deviation(current_value, baseline)
        
        result = f"**{metric_name}:** {current_value:.1f}\n"
        result += f"- 30-day average: {interp['baseline_mean']:.1f}\n"
        result += f"- Deviation: {interp['deviation_absolute']:+.1f} ({interp['deviation_percentage']:+.1f}%)\n"
        result += f"- Status: {interp['interpretation']}\n"
        
        return result
