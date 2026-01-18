"""Prediction and forecasting tools for health data."""

import statistics
from datetime import date, timedelta
from typing import Any, Dict, List, Tuple, Optional

from ..api.client import OuraClient
from ..utils.calorie_forecast import CalorieForecaster


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

    async def predict_calorie_needs(
        self,
        days_ahead: int = 7,
        nutrition_style: str = 'balanced',
        max_carbs_g: Optional[int] = None
    ) -> str:
        """
        Predict daily calorie needs for upcoming days based on activity patterns.

        Args:
            days_ahead: Number of days to predict (default: 7)
            nutrition_style: Nutrition approach for macro recommendations (default: 'balanced')
                Options: balanced, keto, low_carb, carnivore, paleo, high_protein,
                        athlete, mediterranean, zone
            max_carbs_g: Maximum carbs in grams per day (overrides nutrition_style if provided)

        Returns:
            Formatted calorie needs prediction report
        """
        # Gather historical activity data (last 30 days)
        end_date = date.today()
        start_date = end_date - timedelta(days=30)

        activity_data = await self.oura_client.get_daily_activity(start_date, end_date)

        if not activity_data or len(activity_data) < 7:
            return "⚠️ Insufficient activity data for prediction (need at least 7 days)"

        # Get personal information
        try:
            personal_info_response = await self.oura_client.get_personal_info()
            personal_info = {
                'weight': personal_info_response.get('weight', 70),
                'height': personal_info_response.get('height', 170),
                'age': personal_info_response.get('age', 30),
                'biological_sex': personal_info_response.get('biological_sex', 'male')
            }
        except Exception:
            # Use defaults if personal info not available
            personal_info = {
                'weight': 70,
                'height': 170,
                'age': 30,
                'biological_sex': 'male'
            }

        # Validate nutrition style
        if max_carbs_g is None and nutrition_style not in CalorieForecaster.NUTRITION_STYLES:
            available_styles = ', '.join(CalorieForecaster.NUTRITION_STYLES.keys())
            return f"⚠️ Invalid nutrition style '{nutrition_style}'. Available options: {available_styles}"

        result = f"# 🍽️ Calorie Needs Prediction ({days_ahead} days)\n\n"
        result += f"**Based on:** Last {len(activity_data)} days of activity data\n"
        result += f"**Prediction Date:** {date.today().isoformat()}\n"

        if max_carbs_g is not None:
            result += f"**Macro Strategy:** Custom (Max {max_carbs_g}g carbs/day)\n\n"
        else:
            style_info = CalorieForecaster.NUTRITION_STYLES[nutrition_style]
            result += f"**Nutrition Style:** {style_info['name']} - {style_info['description']}\n\n"

        # Calculate trends
        trends = CalorieForecaster.analyze_calorie_trends(activity_data, personal_info)

        result += "## 📊 Your Baseline Metrics\n\n"
        result += f"**Basal Metabolic Rate (BMR):** {trends.get('bmr', 0):,} cal/day\n"
        result += f"**Average TDEE (last 30 days):** {trends.get('average_tdee', 0):,} cal/day\n"
        result += f"**Range:** {trends.get('min_tdee', 0):,} - {trends.get('max_tdee', 0):,} cal/day\n"
        result += f"**Variability:** ±{trends.get('variability', 0):,.0f} calories\n\n"

        # Trend analysis
        trend_direction = trends.get('trend_direction', 'stable')
        if trend_direction == 'increasing':
            result += f"📈 **Trend:** Your calorie expenditure is increasing (+{trends.get('trend_change', 0):,.0f} cal/day)\n\n"
        elif trend_direction == 'decreasing':
            result += f"📉 **Trend:** Your calorie expenditure is decreasing (-{trends.get('trend_change', 0):,.0f} cal/day)\n\n"
        else:
            result += "➡️ **Trend:** Your calorie expenditure is stable\n\n"

        # Generate forecasts
        forecasts = CalorieForecaster.forecast_calorie_needs(
            activity_data,
            personal_info,
            days_ahead
        )

        if not forecasts:
            return result + "\n⚠️ Unable to generate forecasts"

        result += "## 🔮 Daily Calorie Needs Forecast\n\n"

        weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        for forecast in forecasts:
            forecast_date = date.fromisoformat(forecast['date'])
            weekday = weekday_names[forecast_date.weekday()]

            result += f"### {weekday}, {forecast_date.strftime('%B %d')}\n"
            result += f"**Predicted TDEE:** {forecast['predicted_calories']:,} calories {self._get_calorie_emoji(forecast['predicted_calories'])}\n"
            result += f"**Activity Level:** {forecast['activity_level'].replace('_', ' ').title()}\n"
            result += f"**Confidence:** {self._get_confidence_emoji(forecast['confidence'])} {forecast['confidence'].title()}\n"

            # Nutrition recommendations
            result += self._get_nutrition_recommendation(forecast['predicted_calories'], nutrition_style, max_carbs_g)
            result += "\n"

        # Add insights
        result += self._generate_calorie_insights(forecasts, trends)

        return result

    def _get_calorie_emoji(self, calories: int) -> str:
        """Get emoji for calorie level."""
        if calories >= 3000:
            return "🔥"
        elif calories >= 2500:
            return "💪"
        elif calories >= 2000:
            return "✅"
        else:
            return "🟢"

    def _get_confidence_emoji(self, confidence: str) -> str:
        """Get emoji for confidence level."""
        if confidence == 'high':
            return "🟢"
        elif confidence == 'medium':
            return "🟡"
        else:
            return "🔴"

    def _get_nutrition_recommendation(
        self,
        calories: int,
        nutrition_style: str,
        max_carbs_g: Optional[int] = None
    ) -> str:
        """Get nutrition recommendations based on calorie needs and nutrition style."""
        result = "**Macro Targets:**\n"

        # Use max_carbs if provided, otherwise use nutrition style
        if max_carbs_g is not None:
            macros = CalorieForecaster.calculate_macros_with_max_carbs(calories, max_carbs_g)
            protein_g = macros['protein_g']
            protein_pct = macros['protein_pct']
            carb_g = macros['carb_g']
            carb_pct = macros['carb_pct']
            fat_g = macros['fat_g']
            fat_pct = macros['fat_pct']

            result += f"  - Protein: {protein_g}g ({protein_pct}%)\n"
            result += f"  - Carbs: {carb_g}g ({carb_pct}%)"
            if macros['carb_limited']:
                result += " ⚠️ at limit\n"
            else:
                result += "\n"
            result += f"  - Fat: {fat_g}g ({fat_pct}%)\n"
        else:
            # Get macro percentages from nutrition style
            style = CalorieForecaster.NUTRITION_STYLES.get(nutrition_style, CalorieForecaster.NUTRITION_STYLES['balanced'])
            protein_pct = style['protein_pct']
            carb_pct = style['carb_pct']
            fat_pct = style['fat_pct']

            protein_cal = int(calories * protein_pct / 100)
            carb_cal = int(calories * carb_pct / 100)
            fat_cal = int(calories * fat_pct / 100)

            protein_g = int(protein_cal / 4)  # 4 cal/g
            carb_g = int(carb_cal / 4)  # 4 cal/g
            fat_g = int(fat_cal / 9)  # 9 cal/g

            result += f"  - Protein: {protein_g}g ({protein_pct}%)\n"

            if carb_pct > 0:
                result += f"  - Carbs: {carb_g}g ({carb_pct}%)\n"
            else:
                result += f"  - Carbs: <10g (minimal/trace)\n"

            result += f"  - Fat: {fat_g}g ({fat_pct}%)\n"

        return result

    def _generate_calorie_insights(
        self,
        forecasts: List[Dict[str, Any]],
        trends: Dict[str, Any]
    ) -> str:
        """Generate insights from calorie predictions."""
        result = "## 💡 Insights & Recommendations\n\n"

        # Calculate average predicted calories
        avg_predicted = statistics.mean([f['predicted_calories'] for f in forecasts])
        current_avg = trends.get('average_tdee', 0)

        if avg_predicted > current_avg + 100:
            result += "### 📈 Increased Energy Needs Expected\n"
            result += f"Your calorie needs are predicted to increase by ~{int(avg_predicted - current_avg)} cal/day.\n"
            result += "**Action:** Consider increasing food intake to support higher activity levels.\n\n"
        elif avg_predicted < current_avg - 100:
            result += "### 📉 Decreased Energy Needs Expected\n"
            result += f"Your calorie needs may decrease by ~{int(current_avg - avg_predicted)} cal/day.\n"
            result += "**Action:** Adjust portions to avoid excess calorie intake.\n\n"
        else:
            result += "### ➡️ Stable Energy Needs\n"
            result += "Your calorie needs are expected to remain consistent.\n"
            result += "**Action:** Maintain your current nutrition plan.\n\n"

        # Variability insights
        predicted_calories = [f['predicted_calories'] for f in forecasts]
        variability = max(predicted_calories) - min(predicted_calories)

        if variability > 300:
            result += "### ⚠️ High Day-to-Day Variation\n"
            result += f"Your calorie needs vary by up to {variability} cal/day.\n"
            result += "**Tip:** Adjust your intake based on daily activity levels, or maintain a consistent average.\n\n"

        # Weekly pattern insight
        weekday_cals = [f['predicted_calories'] for f in forecasts[:5]] if len(forecasts) >= 5 else []
        weekend_cals = [f['predicted_calories'] for f in forecasts[5:7]] if len(forecasts) >= 7 else []

        if weekday_cals and weekend_cals:
            weekday_avg = statistics.mean(weekday_cals)
            weekend_avg = statistics.mean(weekend_cals)

            if weekend_avg > weekday_avg + 150:
                result += f"### 🏃 More Active Weekends\n"
                result += f"You burn ~{int(weekend_avg - weekday_avg)} more calories on weekends.\n"
                result += "**Tip:** Fuel your weekend activities with adequate nutrition.\n\n"
            elif weekday_avg > weekend_avg + 150:
                result += f"### 💼 More Active Weekdays\n"
                result += f"You burn ~{int(weekday_avg - weekend_avg)} more calories during the week.\n"
                result += "**Tip:** Consider lighter meals on weekends to match lower activity.\n\n"

        return result
