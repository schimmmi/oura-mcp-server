"""Prediction and forecasting tools for health data."""

import statistics
from datetime import date, timedelta
from typing import Any, Dict, List, Tuple, Optional

from ..api.client import OuraClient


class PredictionToolProvider:
    """Provides prediction and forecasting tools."""

    def __init__(self, oura_client: OuraClient):
        self.oura_client = oura_client

    async def predict_sleep_quality(self, days_ahead: int = 3) -> str:
        """
        Predict sleep quality for upcoming days based on historical patterns.

        Args:
            days_ahead: Number of days to predict (default: 3)

        Returns:
            Formatted prediction report
        """
        # Gather historical data (last 30 days)
        end_date = date.today()
        start_date = end_date - timedelta(days=30)

        sleep_data = await self.oura_client.get_daily_sleep(start_date, end_date)
        readiness_data = await self.oura_client.get_daily_readiness(start_date, end_date)

        if not sleep_data or len(sleep_data) < 7:
            return "⚠️ Insufficient data for prediction (need at least 7 days)"

        result = f"# 🔮 Sleep Quality Prediction ({days_ahead} days)\n\n"
        result += f"**Based on:** Last {len(sleep_data)} days of data\n"
        result += f"**Prediction Date:** {date.today().isoformat()}\n\n"

        # Extract time series
        sleep_scores = [d.get("score") for d in sleep_data if d.get("score") is not None]

        # Predict using multiple methods
        result += "## 📊 Prediction Methods\n\n"

        # Method 1: Trend-based prediction
        trend_predictions = self._predict_with_trend(sleep_scores, days_ahead)
        result += "### 1. Trend-Based Forecast\n"
        result += "*Extrapolates current trend into the future*\n\n"
        for i, pred in enumerate(trend_predictions, 1):
            future_date = date.today() + timedelta(days=i)
            result += f"- **{future_date.strftime('%A, %b %d')}:** {pred:.0f} points "
            result += self._get_score_emoji(pred) + "\n"
        result += "\n"

        # Method 2: Moving average prediction
        ma_predictions = self._predict_with_moving_average(sleep_scores, days_ahead)
        result += "### 2. Moving Average (7-day)\n"
        result += "*Smooths recent trends for stable forecast*\n\n"
        for i, pred in enumerate(ma_predictions, 1):
            future_date = date.today() + timedelta(days=i)
            result += f"- **{future_date.strftime('%A, %b %d')}:** {pred:.0f} points "
            result += self._get_score_emoji(pred) + "\n"
        result += "\n"

        # Method 3: Weekly pattern prediction
        weekly_predictions = await self._predict_with_weekly_pattern(sleep_data, days_ahead)
        result += "### 3. Weekly Pattern Recognition\n"
        result += "*Based on your typical day-of-week performance*\n\n"
        for i, pred in enumerate(weekly_predictions, 1):
            future_date = date.today() + timedelta(days=i)
            result += f"- **{future_date.strftime('%A, %b %d')}:** {pred:.0f} points "
            result += self._get_score_emoji(pred) + "\n"
        result += "\n"

        # Ensemble prediction (average of methods)
        result += "## 🎯 Recommended Forecast (Ensemble)\n"
        result += "*Combines all methods for best accuracy*\n\n"

        ensemble_predictions = []
        for i in range(days_ahead):
            avg = (trend_predictions[i] + ma_predictions[i] + weekly_predictions[i]) / 3
            ensemble_predictions.append(avg)
            future_date = date.today() + timedelta(days=i + 1)

            result += f"### {future_date.strftime('%A, %B %d')}\n"
            result += f"**Predicted Score:** {avg:.0f} points {self._get_score_emoji(avg)}\n"

            # Confidence assessment
            variance = statistics.stdev([trend_predictions[i], ma_predictions[i], weekly_predictions[i]])
            confidence = self._calculate_confidence(variance)
            result += f"**Confidence:** {confidence}\n"

            # Recommendation
            result += f"**Recommendation:** {self._get_recommendation(avg)}\n\n"

        # Add insights
        result += await self._generate_prediction_insights(
            sleep_data,
            readiness_data,
            ensemble_predictions
        )

        return result

    async def predict_readiness(self, days_ahead: int = 3) -> str:
        """
        Predict readiness scores for upcoming days.

        Args:
            days_ahead: Number of days to predict (default: 3)

        Returns:
            Formatted prediction report
        """
        # Gather historical data
        end_date = date.today()
        start_date = end_date - timedelta(days=30)

        readiness_data = await self.oura_client.get_daily_readiness(start_date, end_date)

        if not readiness_data or len(readiness_data) < 7:
            return "⚠️ Insufficient data for prediction (need at least 7 days)"

        result = f"# 🎯 Readiness Prediction ({days_ahead} days)\n\n"
        result += f"**Based on:** Last {len(readiness_data)} days of data\n"
        result += f"**Prediction Date:** {date.today().isoformat()}\n\n"

        # Extract time series
        readiness_scores = [d.get("score") for d in readiness_data if d.get("score") is not None]
        hrv_values = [
            d.get("contributors", {}).get("hrv_balance")
            for d in readiness_data
            if d.get("contributors", {}).get("hrv_balance") is not None
        ]

        # Predict readiness
        trend_predictions = self._predict_with_trend(readiness_scores, days_ahead)
        ma_predictions = self._predict_with_moving_average(readiness_scores, days_ahead)
        weekly_predictions = await self._predict_with_weekly_pattern(readiness_data, days_ahead)

        result += "## 🎯 Forecast\n\n"

        for i in range(days_ahead):
            avg = (trend_predictions[i] + ma_predictions[i] + weekly_predictions[i]) / 3
            future_date = date.today() + timedelta(days=i + 1)

            result += f"### {future_date.strftime('%A, %B %d')}\n"
            result += f"**Predicted Readiness:** {avg:.0f} points {self._get_readiness_emoji(avg)}\n"

            # Training recommendation
            result += f"**Training Recommendation:** {self._get_training_recommendation(avg)}\n\n"

        # HRV prediction if available
        if hrv_values:
            result += "## 💚 HRV Forecast\n\n"
            hrv_trend = self._predict_with_trend(hrv_values, days_ahead)

            for i in range(days_ahead):
                future_date = date.today() + timedelta(days=i + 1)
                result += f"- **{future_date.strftime('%A')}:** HRV Balance ~{hrv_trend[i]:.0f}\n"

        return result

    def _predict_with_trend(self, values: List[float], days_ahead: int) -> List[float]:
        """Linear trend extrapolation."""
        if len(values) < 2:
            return [statistics.mean(values)] * days_ahead

        # Simple linear regression
        n = len(values)
        x = list(range(n))
        y = values

        x_mean = statistics.mean(x)
        y_mean = statistics.mean(y)

        # Calculate slope
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return [y_mean] * days_ahead

        slope = numerator / denominator
        intercept = y_mean - slope * x_mean

        # Predict future values
        predictions = []
        for i in range(days_ahead):
            future_x = n + i
            pred = intercept + slope * future_x
            # Clamp to valid range
            pred = max(0, min(100, pred))
            predictions.append(pred)

        return predictions

    def _predict_with_moving_average(self, values: List[float], days_ahead: int, window: int = 7) -> List[float]:
        """Moving average prediction."""
        if len(values) < window:
            window = len(values)

        # Calculate moving average of last window
        recent = values[-window:]
        avg = statistics.mean(recent)

        # Apply damping factor for stability
        predictions = []
        for i in range(days_ahead):
            # Slight regression to mean over time
            overall_mean = statistics.mean(values)
            damped = avg * (1 - i * 0.05) + overall_mean * (i * 0.05)
            damped = max(0, min(100, damped))
            predictions.append(damped)

        return predictions

    async def _predict_with_weekly_pattern(self, data: List[Dict[str, Any]], days_ahead: int) -> List[float]:
        """Predict based on day-of-week patterns."""
        from datetime import datetime

        # Group by day of week
        day_groups = {i: [] for i in range(7)}  # 0=Monday, 6=Sunday

        for record in data:
            day_str = record.get("day")
            score = record.get("score")
            if day_str and score:
                day_date = datetime.fromisoformat(day_str)
                weekday = day_date.weekday()
                day_groups[weekday].append(score)

        # Calculate average for each day
        day_averages = {}
        overall_mean = statistics.mean([score for scores in day_groups.values() for score in scores if scores])

        for day, scores in day_groups.items():
            if scores:
                day_averages[day] = statistics.mean(scores)
            else:
                day_averages[day] = overall_mean

        # Predict based on upcoming days
        predictions = []
        today_weekday = date.today().weekday()

        for i in range(days_ahead):
            future_weekday = (today_weekday + i + 1) % 7
            predictions.append(day_averages[future_weekday])

        return predictions

    async def _generate_prediction_insights(
        self,
        sleep_data: List[Dict[str, Any]],
        readiness_data: Optional[List[Dict[str, Any]]],
        predictions: List[float]
    ) -> str:
        """Generate insights from predictions."""
        result = "## 💡 Insights & Recommendations\n\n"

        # Recent trend
        recent_scores = [d.get("score") for d in sleep_data[-7:] if d.get("score")]
        current_avg = statistics.mean(recent_scores)
        predicted_avg = statistics.mean(predictions)

        if predicted_avg > current_avg + 3:
            result += "### 📈 Improving Trend\n"
            result += f"Your sleep quality is predicted to improve by {predicted_avg - current_avg:.0f} points!\n"
            result += "**Action:** Maintain your current habits - they're working.\n\n"
        elif predicted_avg < current_avg - 3:
            result += "### 📉 Declining Trend\n"
            result += f"Sleep quality may decline by {current_avg - predicted_avg:.0f} points.\n"
            result += "**Action:** Consider adjusting bedtime routine or stress management.\n\n"
        else:
            result += "### ➡️ Stable Trend\n"
            result += "Sleep quality expected to remain consistent.\n"
            result += "**Action:** Continue current routine for stability.\n\n"

        # Variability warning
        std_dev = statistics.stdev(predictions) if len(predictions) > 1 else 0
        if std_dev > 5:
            result += "### ⚠️ High Variability Expected\n"
            result += "Predictions show significant day-to-day fluctuation.\n"
            result += "**Tip:** Focus on consistency in sleep schedule.\n\n"

        return result

    def _calculate_confidence(self, variance: float) -> str:
        """Calculate prediction confidence based on method agreement."""
        if variance < 3:
            return "🟢 High (methods agree)"
        elif variance < 7:
            return "🟡 Medium (some variation)"
        else:
            return "🔴 Low (high uncertainty)"

    def _get_score_emoji(self, score: float) -> str:
        """Get emoji for sleep score."""
        if score >= 85:
            return "🌟"
        elif score >= 70:
            return "✅"
        elif score >= 60:
            return "🟡"
        else:
            return "🔴"

    def _get_readiness_emoji(self, score: float) -> str:
        """Get emoji for readiness score."""
        if score >= 85:
            return "🚀"
        elif score >= 70:
            return "✅"
        elif score >= 60:
            return "⚠️"
        else:
            return "🔴"

    def _get_recommendation(self, score: float) -> str:
        """Get sleep recommendation based on predicted score."""
        if score >= 85:
            return "Excellent sleep expected - maintain routine"
        elif score >= 70:
            return "Good sleep predicted - continue current habits"
        elif score >= 60:
            return "Moderate sleep - consider earlier bedtime"
        else:
            return "Poor sleep risk - prioritize sleep hygiene"

    def _get_training_recommendation(self, score: float) -> str:
        """Get training recommendation based on predicted readiness."""
        if score >= 85:
            return "🚀 Excellent for intense training"
        elif score >= 70:
            return "✅ Good for moderate to hard sessions"
        elif score >= 60:
            return "⚠️ Light training recommended"
        else:
            return "🔴 Focus on recovery, avoid intense training"
