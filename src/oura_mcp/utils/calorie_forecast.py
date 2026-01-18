"""Calorie needs forecasting utilities."""

import statistics
from datetime import date, timedelta
from typing import Dict, List, Tuple, Optional, Any


class CalorieForecaster:
    """Forecaster for daily calorie needs based on activity patterns."""

    # Standard calorie formulas (Mifflin-St Jeor equation)
    # BMR = Base Metabolic Rate

    # Nutrition style macro distributions
    NUTRITION_STYLES = {
        'balanced': {
            'name': 'Balanced',
            'description': 'Balanced macro distribution',
            'protein_pct': 30,
            'carb_pct': 40,
            'fat_pct': 30
        },
        'keto': {
            'name': 'Ketogenic',
            'description': 'Very low carb, high fat',
            'protein_pct': 25,
            'carb_pct': 5,
            'fat_pct': 70
        },
        'low_carb': {
            'name': 'Low Carb',
            'description': 'Reduced carbohydrates',
            'protein_pct': 30,
            'carb_pct': 20,
            'fat_pct': 50
        },
        'carnivore': {
            'name': 'Carnivore/Animal-Based',
            'description': 'Primarily animal products, minimal to no carbs',
            'protein_pct': 35,
            'carb_pct': 0,
            'fat_pct': 65
        },
        'paleo': {
            'name': 'Paleo',
            'description': 'Whole foods, moderate carbs',
            'protein_pct': 30,
            'carb_pct': 30,
            'fat_pct': 40
        },
        'high_protein': {
            'name': 'High Protein',
            'description': 'Elevated protein for muscle building',
            'protein_pct': 40,
            'carb_pct': 35,
            'fat_pct': 25
        },
        'athlete': {
            'name': 'Athlete/High Carb',
            'description': 'High carb for endurance/performance',
            'protein_pct': 25,
            'carb_pct': 50,
            'fat_pct': 25
        },
        'mediterranean': {
            'name': 'Mediterranean',
            'description': 'Moderate fat, whole grains',
            'protein_pct': 20,
            'carb_pct': 45,
            'fat_pct': 35
        },
        'zone': {
            'name': 'Zone Diet',
            'description': '40/30/30 distribution',
            'protein_pct': 30,
            'carb_pct': 40,
            'fat_pct': 30
        }
    }

    @staticmethod
    def calculate_macros_with_max_carbs(
        calories: int,
        max_carbs_g: int,
        protein_target_pct: float = 30
    ) -> Dict[str, Any]:
        """
        Calculate macro distribution with a maximum carb limit.

        Args:
            calories: Total daily calories
            max_carbs_g: Maximum carbs in grams
            protein_target_pct: Target protein percentage (default: 30%)

        Returns:
            Dictionary with protein, carb, and fat amounts in grams and percentages
        """
        # Calculate protein
        protein_cal = int(calories * protein_target_pct / 100)
        protein_g = int(protein_cal / 4)  # 4 cal/g

        # Calculate carbs (limited by max)
        carb_g = min(max_carbs_g, int(calories * 0.4 / 4))  # Don't exceed 40% even if max_carbs allows
        carb_cal = carb_g * 4

        # Remaining calories go to fat
        remaining_cal = calories - protein_cal - carb_cal
        fat_g = int(remaining_cal / 9)  # 9 cal/g

        # Calculate actual percentages
        protein_pct = int((protein_cal / calories) * 100)
        carb_pct = int((carb_cal / calories) * 100)
        fat_pct = int((fat_g * 9 / calories) * 100)

        return {
            'protein_g': protein_g,
            'protein_pct': protein_pct,
            'carb_g': carb_g,
            'carb_pct': carb_pct,
            'fat_g': fat_g,
            'fat_pct': fat_pct,
            'carb_limited': carb_g == max_carbs_g
        }

    @staticmethod
    def calculate_bmr(
        weight_kg: float,
        height_cm: float,
        age_years: int,
        sex: str
    ) -> float:
        """
        Calculate Basal Metabolic Rate using Mifflin-St Jeor equation.

        Args:
            weight_kg: Body weight in kg
            height_cm: Height in cm
            age_years: Age in years
            sex: Biological sex ('male' or 'female')

        Returns:
            BMR in calories/day
        """
        # Mifflin-St Jeor equation
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age_years

        if sex.lower() == 'male':
            bmr += 5
        else:  # female
            bmr -= 161

        return bmr

    @staticmethod
    def calculate_tdee(bmr: float, activity_level: str) -> float:
        """
        Calculate Total Daily Energy Expenditure.

        Args:
            bmr: Basal Metabolic Rate
            activity_level: Activity level category

        Returns:
            TDEE in calories/day
        """
        activity_multipliers = {
            'sedentary': 1.2,      # Little to no exercise
            'light': 1.375,        # Light exercise 1-3 days/week
            'moderate': 1.55,      # Moderate exercise 3-5 days/week
            'active': 1.725,       # Hard exercise 6-7 days/week
            'very_active': 1.9     # Very hard exercise & physical job
        }

        multiplier = activity_multipliers.get(activity_level, 1.55)
        return bmr * multiplier

    @staticmethod
    def get_activity_level_from_score(activity_score: float) -> str:
        """
        Determine activity level category from Oura activity score.

        Args:
            activity_score: Oura activity score (0-100)

        Returns:
            Activity level category
        """
        if activity_score >= 85:
            return 'very_active'
        elif activity_score >= 70:
            return 'active'
        elif activity_score >= 55:
            return 'moderate'
        elif activity_score >= 40:
            return 'light'
        else:
            return 'sedentary'

    @classmethod
    def calculate_oura_based_tdee(
        cls,
        activity_data: Dict[str, Any],
        personal_info: Dict[str, Any]
    ) -> Tuple[float, float, str]:
        """
        Calculate TDEE using Oura activity data and personal info.

        Args:
            activity_data: Daily activity data from Oura
            personal_info: Personal information (weight, height, age, sex)

        Returns:
            Tuple of (BMR, TDEE, activity_level)
        """
        # Extract personal info
        weight_kg = personal_info.get('weight', 70)  # Default 70kg
        height_cm = personal_info.get('height', 170)  # Default 170cm
        age_years = personal_info.get('age', 30)  # Default 30 years
        sex = personal_info.get('biological_sex', 'male')

        # Calculate BMR
        bmr = cls.calculate_bmr(weight_kg, height_cm, age_years, sex)

        # Get activity level from Oura score
        activity_score = activity_data.get('score', 50)
        activity_level = cls.get_activity_level_from_score(activity_score)

        # Calculate TDEE
        tdee = cls.calculate_tdee(bmr, activity_level)

        return bmr, tdee, activity_level

    @classmethod
    def calculate_precise_tdee(
        cls,
        activity_data: Dict[str, Any],
        personal_info: Dict[str, Any]
    ) -> float:
        """
        Calculate more precise TDEE using actual activity calories from Oura.

        Args:
            activity_data: Daily activity data from Oura
            personal_info: Personal information

        Returns:
            Estimated TDEE in calories
        """
        # Extract personal info for BMR
        weight_kg = personal_info.get('weight', 70)
        height_cm = personal_info.get('height', 170)
        age_years = personal_info.get('age', 30)
        sex = personal_info.get('biological_sex', 'male')

        # Calculate BMR
        bmr = cls.calculate_bmr(weight_kg, height_cm, age_years, sex)

        # Get actual calories from Oura
        # Oura provides total_calories and active_calories
        total_calories = activity_data.get('total_calories', 0)
        active_calories = activity_data.get('active_calories', 0)

        if total_calories > 0:
            # Oura's total_calories is already a good estimate of TDEE
            return float(total_calories)
        else:
            # Fallback to BMR + active calories
            return bmr + active_calories

    @classmethod
    def forecast_calorie_needs(
        cls,
        activity_history: List[Dict[str, Any]],
        personal_info: Dict[str, Any],
        days_ahead: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Forecast daily calorie needs for upcoming days.

        Args:
            activity_history: Historical activity data
            personal_info: Personal information
            days_ahead: Number of days to forecast

        Returns:
            List of forecasts with date, predicted calories, and activity level
        """
        if not activity_history:
            return []

        # Calculate historical TDEEs
        historical_tdees = []
        historical_scores = []

        for activity_day in activity_history:
            tdee = cls.calculate_precise_tdee(activity_day, personal_info)
            score = activity_day.get('score', 50)

            if tdee > 0:
                historical_tdees.append(tdee)
                historical_scores.append(score)

        if not historical_tdees:
            return []

        # Calculate average TDEE and trend
        avg_tdee = statistics.mean(historical_tdees)

        # Calculate weekly pattern (day-of-week averages)
        weekly_pattern = cls._calculate_weekly_pattern(activity_history, personal_info)

        # Generate forecasts
        forecasts = []
        today = date.today()

        for i in range(days_ahead):
            future_date = today + timedelta(days=i + 1)
            weekday = future_date.weekday()

            # Use weekly pattern if available, otherwise use average
            if weekday in weekly_pattern:
                predicted_tdee = weekly_pattern[weekday]
            else:
                predicted_tdee = avg_tdee

            # Determine activity level
            predicted_score = statistics.mean(historical_scores[-7:]) if len(historical_scores) >= 7 else statistics.mean(historical_scores)
            activity_level = cls.get_activity_level_from_score(predicted_score)

            forecasts.append({
                'date': future_date.isoformat(),
                'predicted_calories': round(predicted_tdee),
                'activity_level': activity_level,
                'confidence': 'high' if len(historical_tdees) >= 14 else 'medium' if len(historical_tdees) >= 7 else 'low'
            })

        return forecasts

    @classmethod
    def _calculate_weekly_pattern(
        cls,
        activity_history: List[Dict[str, Any]],
        personal_info: Dict[str, Any]
    ) -> Dict[int, float]:
        """
        Calculate average TDEE for each day of the week.

        Args:
            activity_history: Historical activity data
            personal_info: Personal information

        Returns:
            Dictionary mapping weekday (0=Monday) to average TDEE
        """
        from datetime import datetime

        # Group by day of week
        weekly_groups = {i: [] for i in range(7)}

        for activity_day in activity_history:
            day_str = activity_day.get('day')
            if not day_str:
                continue

            tdee = cls.calculate_precise_tdee(activity_day, personal_info)
            if tdee > 0:
                day_date = datetime.fromisoformat(day_str)
                weekday = day_date.weekday()
                weekly_groups[weekday].append(tdee)

        # Calculate averages
        weekly_pattern = {}
        for weekday, tdees in weekly_groups.items():
            if tdees:
                weekly_pattern[weekday] = statistics.mean(tdees)

        return weekly_pattern

    @classmethod
    def analyze_calorie_trends(
        cls,
        activity_history: List[Dict[str, Any]],
        personal_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze calorie expenditure trends.

        Args:
            activity_history: Historical activity data
            personal_info: Personal information

        Returns:
            Analysis results with trends and insights
        """
        if not activity_history:
            return {'error': 'No activity data available'}

        # Calculate BMR
        weight_kg = personal_info.get('weight', 70)
        height_cm = personal_info.get('height', 170)
        age_years = personal_info.get('age', 30)
        sex = personal_info.get('biological_sex', 'male')

        bmr = cls.calculate_bmr(weight_kg, height_cm, age_years, sex)

        # Calculate historical TDEEs
        tdees = []
        dates = []

        for activity_day in activity_history:
            tdee = cls.calculate_precise_tdee(activity_day, personal_info)
            day_str = activity_day.get('day')

            if tdee > 0 and day_str:
                tdees.append(tdee)
                dates.append(day_str)

        if not tdees:
            return {'error': 'No valid TDEE data'}

        # Calculate statistics
        avg_tdee = statistics.mean(tdees)
        min_tdee = min(tdees)
        max_tdee = max(tdees)
        std_dev = statistics.stdev(tdees) if len(tdees) > 1 else 0

        # Calculate trend (simple linear)
        if len(tdees) >= 7:
            recent_avg = statistics.mean(tdees[-7:])
            older_avg = statistics.mean(tdees[:7])
            trend_direction = 'increasing' if recent_avg > older_avg else 'decreasing' if recent_avg < older_avg else 'stable'
            trend_change = abs(recent_avg - older_avg)
        else:
            trend_direction = 'insufficient_data'
            trend_change = 0

        return {
            'bmr': round(bmr),
            'average_tdee': round(avg_tdee),
            'min_tdee': round(min_tdee),
            'max_tdee': round(max_tdee),
            'variability': round(std_dev),
            'trend_direction': trend_direction,
            'trend_change': round(trend_change),
            'data_points': len(tdees),
            'date_range': {
                'start': dates[0],
                'end': dates[-1]
            }
        }
