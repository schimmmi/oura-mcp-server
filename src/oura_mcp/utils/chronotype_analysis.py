"""
Chronotype Analysis

Analyzes sleep timing patterns and activity peaks to determine chronotype
(morning lark, night owl, intermediate) and optimal activity windows.

Based on:
- Average sleep/wake times over extended period
- Activity distribution throughout the day
- Sleep quality correlation with timing
"""

from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Tuple
from statistics import mean, stdev
from collections import defaultdict


class ChronotypeAnalyzer:
    """
    Analyzes chronotype based on sleep timing and activity patterns.

    Chronotypes:
    - Morning Lark: Sleep before 23:00, wake before 7:00
    - Night Owl: Sleep after 01:00, wake after 9:00
    - Intermediate: Between lark and owl patterns
    """

    # Chronotype definitions (hours in 24h format)
    LARK_BEDTIME_MAX = 23.0
    LARK_WAKETIME_MAX = 7.0
    OWL_BEDTIME_MIN = 1.0  # 01:00 (next day)
    OWL_WAKETIME_MIN = 9.0

    def __init__(self, min_days: int = 14):
        """
        Initialize chronotype analyzer.

        Args:
            min_days: Minimum days of data required for reliable analysis
        """
        self.min_days = min_days

    def analyze_chronotype(
        self,
        sleep_sessions: List[Dict],
        activity_data: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Comprehensive chronotype analysis.

        Args:
            sleep_sessions: Sleep session data from Oura API
            activity_data: Optional activity data for peak analysis

        Returns:
            Dictionary with chronotype classification and insights
        """
        if len(sleep_sessions) < self.min_days:
            return {
                'error': f'Insufficient data: {len(sleep_sessions)} days (minimum {self.min_days} required)',
                'chronotype': 'Unknown'
            }

        # Filter to main sleep sessions only (exclude short naps)
        main_sleep_sessions = self._extract_main_sleep_sessions(sleep_sessions)

        if len(main_sleep_sessions) < self.min_days:
            return {
                'error': f'Insufficient main sleep data: {len(main_sleep_sessions)} days (minimum {self.min_days} required)',
                'chronotype': 'Unknown'
            }

        # Extract sleep timing patterns from MAIN sleep only
        bedtimes = []
        waketimes = []
        sleep_midpoints = []
        weekday_data = []
        weekend_data = []

        for session in main_sleep_sessions:
            bedtime = self._parse_time(session.get('bedtime_start'))
            waketime = self._parse_time(session.get('bedtime_end'))

            if bedtime is not None:
                bedtimes.append(bedtime)
            if waketime is not None:
                waketimes.append(waketime)

            # Calculate midpoint of sleep (MSF - scientific standard)
            if bedtime is not None and waketime is not None:
                midpoint = self._calculate_sleep_midpoint(bedtime, waketime)
                sleep_midpoints.append(midpoint)

                # Separate weekday vs weekend
                day_str = session.get('day')
                if day_str:
                    try:
                        date_obj = datetime.fromisoformat(day_str)
                        weekday = date_obj.weekday()  # 0=Monday, 6=Sunday
                        if weekday >= 5:  # Saturday/Sunday
                            weekend_data.append({'bedtime': bedtime, 'waketime': waketime, 'midpoint': midpoint})
                        else:
                            weekday_data.append({'bedtime': bedtime, 'waketime': waketime, 'midpoint': midpoint})
                    except ValueError:
                        pass

        if not bedtimes or not waketimes:
            return {
                'error': 'No valid sleep timing data found',
                'chronotype': 'Unknown'
            }

        # Calculate averages and variability
        avg_bedtime = self._calculate_circular_mean(bedtimes)
        avg_waketime = self._calculate_circular_mean(waketimes)
        bedtime_consistency = self._calculate_consistency(bedtimes)
        waketime_consistency = self._calculate_consistency(waketimes)

        # Calculate midpoint of sleep on free days (MSFsc - scientific gold standard)
        msf = None
        if weekend_data:
            weekend_midpoints = [d['midpoint'] for d in weekend_data]
            msf = self._calculate_circular_mean(weekend_midpoints)

        # Determine chronotype using both traditional and MSF methods
        chronotype = self._classify_chronotype(avg_bedtime, avg_waketime, msf)

        # Analyze sleep quality by timing
        quality_by_timing = self._analyze_quality_by_timing(sleep_sessions)

        # Find optimal sleep window
        optimal_bedtime = self._find_optimal_bedtime(sleep_sessions)

        # Activity peak analysis (if available)
        activity_insights = None
        if activity_data:
            activity_insights = self._analyze_activity_peaks(activity_data)

        # Build report
        result = {
            'chronotype': chronotype,
            'classification': self._get_classification_details(chronotype),
            'sleep_timing': {
                'average_bedtime': self._format_time(avg_bedtime),
                'average_waketime': self._format_time(avg_waketime),
                'bedtime_consistency': f"{bedtime_consistency:.1%}",
                'waketime_consistency': f"{waketime_consistency:.1%}",
                'sleep_window_hours': self._calculate_sleep_window(avg_bedtime, avg_waketime)
            },
            'optimal_timing': {
                'recommended_bedtime': self._format_time(optimal_bedtime),
                'reason': 'Based on highest sleep quality correlation'
            },
            'quality_insights': quality_by_timing,
            'days_analyzed': len(main_sleep_sessions),
            'main_sleep_only': True
        }

        # Add MSF data if available
        if msf is not None:
            result['msf'] = {
                'midpoint_of_sleep': self._format_time(msf),
                'weekend_days': len(weekend_data),
                'classification_method': 'MSF (scientific standard)'
            }

        # Add weekday vs weekend comparison if data available
        if weekday_data and weekend_data:
            weekday_bedtime = self._calculate_circular_mean([d['bedtime'] for d in weekday_data])
            weekend_bedtime = self._calculate_circular_mean([d['bedtime'] for d in weekend_data])
            weekday_waketime = self._calculate_circular_mean([d['waketime'] for d in weekday_data])
            weekend_waketime = self._calculate_circular_mean([d['waketime'] for d in weekend_data])

            result['schedule_flexibility'] = {
                'weekday_bedtime': self._format_time(weekday_bedtime),
                'weekend_bedtime': self._format_time(weekend_bedtime),
                'weekday_waketime': self._format_time(weekday_waketime),
                'weekend_waketime': self._format_time(weekend_waketime),
                'social_jetlag_hours': abs(self._calculate_sleep_midpoint(weekend_bedtime, weekend_waketime) -
                                          self._calculate_sleep_midpoint(weekday_bedtime, weekday_waketime))
            }

        if activity_insights:
            result['activity_pattern'] = activity_insights

        return result

    def _extract_main_sleep_sessions(self, sleep_sessions: List[Dict]) -> List[Dict]:
        """
        Extract main sleep session per day, excluding short naps.

        Uses longest session per day OR sessions >2 hours if aggregated.

        Args:
            sleep_sessions: All sleep sessions (may include naps)

        Returns:
            List of main sleep sessions only
        """
        from collections import defaultdict

        # Group sessions by day
        sessions_by_day = defaultdict(list)
        for session in sleep_sessions:
            day = session.get('day')
            if day:
                sessions_by_day[day].append(session)

        main_sessions = []

        for day, sessions in sessions_by_day.items():
            # If already aggregated, check if it's valid main sleep
            if len(sessions) == 1:
                session = sessions[0]
                duration = session.get('total_sleep_duration', 0)
                # Only include if >2 hours (7200 seconds)
                if duration and duration >= 7200:
                    main_sessions.append(session)
            else:
                # Multiple sessions: pick longest one as main sleep
                longest = max(sessions, key=lambda s: s.get('total_sleep_duration', 0))
                duration = longest.get('total_sleep_duration', 0)
                if duration and duration >= 3600:  # At least 1 hour
                    main_sessions.append(longest)

        return main_sessions

    def _calculate_sleep_midpoint(self, bedtime: float, waketime: float) -> float:
        """
        Calculate midpoint of sleep (MSF).

        Args:
            bedtime: Bedtime in decimal hours
            waketime: Waketime in decimal hours

        Returns:
            Midpoint in decimal hours
        """
        # Normalize waketime if it's earlier than bedtime (next day)
        if waketime < bedtime:
            waketime += 24

        midpoint = (bedtime + waketime) / 2

        # Normalize to 0-24 range
        return midpoint % 24

    def _parse_time(self, timestamp_str: Optional[str]) -> Optional[float]:
        """
        Parse ISO timestamp to decimal hours (0-24).

        Args:
            timestamp_str: ISO format timestamp

        Returns:
            Hours as float (e.g., 22.5 for 22:30), or None if invalid
        """
        if not timestamp_str:
            return None

        try:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.hour + dt.minute / 60.0
        except (ValueError, AttributeError):
            return None

    def _calculate_circular_mean(self, times: List[float]) -> float:
        """
        Calculate mean of circular data (times that wrap around 24h).

        Handles times like 23:00, 00:30, 01:00 correctly.

        Args:
            times: List of times as decimal hours

        Returns:
            Mean time as decimal hours
        """
        import math

        # Convert to angles (hours -> radians)
        angles = [t * 2 * math.pi / 24 for t in times]

        # Calculate mean angle
        sin_sum = sum(math.sin(a) for a in angles)
        cos_sum = sum(math.cos(a) for a in angles)

        mean_angle = math.atan2(sin_sum, cos_sum)

        # Convert back to hours
        mean_time = (mean_angle * 24 / (2 * math.pi)) % 24

        return mean_time

    def _calculate_consistency(self, times: List[float]) -> float:
        """
        Calculate consistency score (inverse of variance).

        Args:
            times: List of times as decimal hours

        Returns:
            Consistency score 0-1 (1 = perfectly consistent)
        """
        if len(times) < 2:
            return 1.0

        # Calculate circular variance
        import math
        angles = [t * 2 * math.pi / 24 for t in times]

        sin_sum = sum(math.sin(a) for a in angles)
        cos_sum = sum(math.cos(a) for a in angles)

        r = math.sqrt(sin_sum**2 + cos_sum**2) / len(angles)

        # r is concentration parameter: 1 = perfect consistency, 0 = random
        return r

    def _classify_chronotype(self, avg_bedtime: float, avg_waketime: float, msf: Optional[float] = None) -> str:
        """
        Classify chronotype based on sleep/wake times and MSF (Midpoint of Sleep on Free days).

        Uses scientific MSF method as primary classifier when available.

        Args:
            avg_bedtime: Average bedtime in decimal hours
            avg_waketime: Average waketime in decimal hours
            msf: Midpoint of sleep on free days (weekend), if available

        Returns:
            Chronotype classification string
        """
        # Primary classification: Use MSF if available (scientific gold standard)
        if msf is not None:
            # MSF chronotype thresholds (Roenneberg et al.)
            # Early: MSF < 3:00
            # Intermediate: MSF 3:00-5:00
            # Late: MSF > 5:00
            if msf < 3.0:
                return "Morning Lark"
            elif msf > 5.0:
                return "Night Owl"
            elif msf > 4.5:
                return "Slight Evening Tendency"
            elif msf < 3.5:
                return "Slight Morning Tendency"
            else:
                return "Intermediate"

        # Fallback: Use bedtime/waketime (less accurate but still useful)
        # Normalize bedtime to 0-24 scale (handle times after midnight)
        bedtime_normalized = avg_bedtime if avg_bedtime > 12 else avg_bedtime + 24

        # Morning Lark criteria
        if bedtime_normalized <= self.LARK_BEDTIME_MAX + 24 and avg_waketime <= self.LARK_WAKETIME_MAX:
            return "Morning Lark"

        # Night Owl criteria (bedtime after 01:00 = 25:00 in normalized scale)
        if bedtime_normalized >= self.OWL_BEDTIME_MIN + 24 and avg_waketime >= self.OWL_WAKETIME_MIN:
            return "Night Owl"

        # Slight variations
        if bedtime_normalized <= 24.5 and avg_waketime <= 8.0:
            return "Slight Morning Tendency"

        if bedtime_normalized >= 24.5 and avg_waketime >= 8.0:
            return "Slight Evening Tendency"

        return "Intermediate"

    def _get_classification_details(self, chronotype: str) -> Dict:
        """
        Get detailed description of chronotype.

        Args:
            chronotype: Chronotype classification

        Returns:
            Dictionary with description and recommendations
        """
        details = {
            "Morning Lark": {
                "description": "Early sleeper, early riser. Peak performance in morning hours.",
                "optimal_work_hours": "6:00-14:00",
                "optimal_exercise": "Morning (7:00-9:00)",
                "traits": ["Early bedtime", "Natural morning person", "Evening fatigue"]
            },
            "Night Owl": {
                "description": "Late sleeper, late riser. Peak performance in evening hours.",
                "optimal_work_hours": "10:00-18:00 or later",
                "optimal_exercise": "Evening (17:00-20:00)",
                "traits": ["Late bedtime", "Morning grogginess", "Evening alertness"]
            },
            "Slight Morning Tendency": {
                "description": "Moderate morning preference. Flexible schedule works well.",
                "optimal_work_hours": "7:00-15:00",
                "optimal_exercise": "Morning or midday (8:00-12:00)",
                "traits": ["Slight morning preference", "Good adaptability"]
            },
            "Slight Evening Tendency": {
                "description": "Moderate evening preference. Flexible schedule works well.",
                "optimal_work_hours": "9:00-17:00",
                "optimal_exercise": "Afternoon or evening (15:00-19:00)",
                "traits": ["Slight evening preference", "Good adaptability"]
            },
            "Intermediate": {
                "description": "Balanced chronotype. No strong morning or evening preference.",
                "optimal_work_hours": "8:00-16:00 (standard schedule)",
                "optimal_exercise": "Midday (11:00-14:00)",
                "traits": ["Flexible schedule", "Balanced energy", "Good adaptation"]
            }
        }

        return details.get(chronotype, {
            "description": "Unknown chronotype pattern",
            "optimal_work_hours": "Individual variation",
            "optimal_exercise": "Based on personal preference",
            "traits": []
        })

    def _calculate_sleep_window(self, bedtime: float, waketime: float) -> float:
        """
        Calculate typical sleep window duration.

        Args:
            bedtime: Average bedtime in decimal hours
            waketime: Average waketime in decimal hours

        Returns:
            Sleep window in hours
        """
        if waketime < bedtime:
            waketime += 24

        return waketime - bedtime

    def _analyze_quality_by_timing(self, sleep_sessions: List[Dict]) -> Dict:
        """
        Analyze sleep quality correlation with bedtime timing.

        Args:
            sleep_sessions: Sleep session data

        Returns:
            Quality insights by timing windows
        """
        # Group by bedtime windows
        windows = {
            "Before 22:00": [],
            "22:00-23:00": [],
            "23:00-00:00": [],
            "00:00-01:00": [],
            "After 01:00": []
        }

        for session in sleep_sessions:
            bedtime = self._parse_time(session.get('bedtime_start'))

            # Try multiple score sources
            score = session.get('score')
            if score is None:
                # Check readiness score as fallback
                readiness = session.get('readiness', {})
                if isinstance(readiness, dict):
                    score = readiness.get('score')

            # Use efficiency as proxy if no score available
            if score is None:
                efficiency = session.get('efficiency')
                if efficiency is not None:
                    # Convert efficiency (0-100%) to score-like metric
                    score = min(100, efficiency * 1.2)  # Scale up slightly

            if bedtime is None or score is None:
                continue

            # Normalize for comparison
            bedtime_normalized = bedtime if bedtime > 12 else bedtime + 24

            if bedtime_normalized < 22:
                windows["Before 22:00"].append(score)
            elif bedtime_normalized < 23:
                windows["22:00-23:00"].append(score)
            elif bedtime_normalized < 24:
                windows["23:00-00:00"].append(score)
            elif bedtime_normalized < 25:
                windows["00:00-01:00"].append(score)
            else:
                windows["After 01:00"].append(score)

        # Calculate averages
        results = {}
        for window, scores in windows.items():
            if scores:
                results[window] = {
                    'average_score': round(mean(scores), 1),
                    'nights': len(scores)
                }

        # Find best window
        if results:
            best_window = max(results.items(), key=lambda x: x[1]['average_score'])
            results['best_window'] = {
                'time': best_window[0],
                'score': best_window[1]['average_score']
            }

        return results

    def _find_optimal_bedtime(self, sleep_sessions: List[Dict]) -> float:
        """
        Find optimal bedtime based on sleep quality.

        Args:
            sleep_sessions: Sleep session data

        Returns:
            Optimal bedtime in decimal hours
        """
        # Collect bedtime-score pairs
        data = []
        for session in sleep_sessions:
            bedtime = self._parse_time(session.get('bedtime_start'))
            score = session.get('score')

            if bedtime is not None and score is not None:
                data.append((bedtime, score))

        if not data:
            return 23.0  # Default fallback

        # Find time window with best average score
        # Group by 30-minute windows
        windows = defaultdict(list)
        for bedtime, score in data:
            # Round to nearest 30 minutes
            window = round(bedtime * 2) / 2
            windows[window].append(score)

        # Find best window
        best_window = max(windows.items(), key=lambda x: mean(x[1]))

        return best_window[0]

    def _analyze_activity_peaks(self, activity_data: List[Dict]) -> Dict:
        """
        Analyze when activity peaks occur during the day.

        Args:
            activity_data: Daily activity data from Oura API

        Returns:
            Activity pattern insights
        """
        # This would require intraday activity data which Oura doesn't provide
        # in daily summaries. For now, we can analyze high/low activity days.

        if not activity_data:
            return {'note': 'Detailed intraday activity data not available'}

        # Analyze weekly patterns instead
        daily_scores = defaultdict(list)

        for day_data in activity_data:
            day_str = day_data.get('day', '')
            if day_str:
                try:
                    date = datetime.fromisoformat(day_str)
                    weekday = date.strftime('%A')
                    score = day_data.get('score')
                    if score:
                        daily_scores[weekday].append(score)
                except ValueError:
                    continue

        # Calculate averages per weekday
        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        weekday_avg = {}

        for weekday in weekday_order:
            if weekday in daily_scores and daily_scores[weekday]:
                weekday_avg[weekday] = round(mean(daily_scores[weekday]), 1)

        if not weekday_avg:
            return {'note': 'Insufficient activity data for pattern analysis'}

        # Find peak days
        best_day = max(weekday_avg.items(), key=lambda x: x[1])
        worst_day = min(weekday_avg.items(), key=lambda x: x[1])

        return {
            'weekly_pattern': weekday_avg,
            'most_active_day': {
                'day': best_day[0],
                'average_score': best_day[1]
            },
            'least_active_day': {
                'day': worst_day[0],
                'average_score': worst_day[1]
            }
        }

    def _format_time(self, decimal_hours: float) -> str:
        """
        Format decimal hours to HH:MM string.

        Args:
            decimal_hours: Time as decimal (e.g., 22.5)

        Returns:
            Formatted time string (e.g., "22:30")
        """
        hours = int(decimal_hours) % 24
        minutes = int((decimal_hours % 1) * 60)
        return f"{hours:02d}:{minutes:02d}"

    def format_chronotype_report(self, analysis: Dict) -> str:
        """
        Format chronotype analysis as human-readable report.

        Args:
            analysis: Analysis dictionary from analyze_chronotype()

        Returns:
            Formatted report string
        """
        if 'error' in analysis:
            return f"⚠️ Chronotype Analysis Error\n\n{analysis['error']}"

        chronotype = analysis['chronotype']
        classification = analysis.get('classification', {})
        timing = analysis['sleep_timing']
        optimal = analysis['optimal_timing']
        quality = analysis['quality_insights']

        report = []

        # Header
        report.append(f"🦉 Chronotype Analysis\n")
        report.append(f"{'=' * 50}\n")

        # Chronotype
        report.append(f"**Chronotype:** {chronotype}\n")
        report.append(f"{classification.get('description', '')}\n")

        # Sleep timing
        report.append(f"\n📊 Your Sleep Pattern ({analysis['days_analyzed']} days analyzed - main sleep only)")
        report.append(f"- Average Bedtime: {timing['average_bedtime']}")
        report.append(f"- Average Wake Time: {timing['average_waketime']}")
        report.append(f"- Sleep Window: {timing['sleep_window_hours']:.1f} hours")
        report.append(f"- Bedtime Consistency: {timing['bedtime_consistency']}")
        report.append(f"- Wake Time Consistency: {timing['waketime_consistency']}")

        # MSF data if available
        if 'msf' in analysis:
            msf = analysis['msf']
            report.append(f"- Sleep Midpoint (MSF): {msf['midpoint_of_sleep']} (weekend average, {msf['weekend_days']} days)")
            report.append(f"- Classification Method: {msf['classification_method']}")

        report.append("")

        # Recommendations
        report.append(f"💡 Personalized Recommendations")
        report.append(f"- Optimal Work Hours: {classification.get('optimal_work_hours', 'N/A')}")
        report.append(f"- Best Exercise Time: {classification.get('optimal_exercise', 'N/A')}")
        report.append(f"- Recommended Bedtime: {optimal['recommended_bedtime']} ({optimal['reason']})\n")

        # Quality by timing
        if quality and 'best_window' in quality:
            best = quality['best_window']
            report.append(f"🌙 Sleep Quality by Bedtime")
            report.append(f"- Best Window: {best['time']} (Avg Score: {best['score']})")

            # Show all windows
            for window, data in sorted(quality.items()):
                if window != 'best_window':
                    marker = "⭐" if window == best['time'] else "  "
                    report.append(f"{marker} {window}: {data['average_score']}/100 ({data['nights']} nights)")
            report.append("")

        # Schedule flexibility (weekday vs weekend)
        if 'schedule_flexibility' in analysis:
            flex = analysis['schedule_flexibility']
            report.append(f"📅 Weekday vs Weekend Pattern")
            report.append(f"- Weekday Bedtime: {flex['weekday_bedtime']}")
            report.append(f"- Weekend Bedtime: {flex['weekend_bedtime']}")
            report.append(f"- Weekday Wake: {flex['weekday_waketime']}")
            report.append(f"- Weekend Wake: {flex['weekend_waketime']}")
            report.append(f"- Social Jetlag: {flex['social_jetlag_hours']:.1f} hours\n")

        # Activity pattern
        if 'activity_pattern' in analysis:
            activity = analysis['activity_pattern']
            if 'most_active_day' in activity:
                report.append(f"🏃 Activity Pattern")
                report.append(f"- Most Active: {activity['most_active_day']['day']} (Score: {activity['most_active_day']['average_score']})")
                report.append(f"- Least Active: {activity['least_active_day']['day']} (Score: {activity['least_active_day']['average_score']})\n")

        # Traits
        traits = classification.get('traits', [])
        if traits:
            report.append(f"🔍 Your Chronotype Traits")
            for trait in traits:
                report.append(f"- {trait}")

        return "\n".join(report)
