"""
Optimal Bedtime Calculator

Analyzes sleep patterns to recommend optimal bedtime based on historical data
of best sleep nights.
"""

from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Tuple
from statistics import mean, stdev, median


class BedtimeCalculator:
    """Calculates optimal bedtime based on historical sleep quality data."""

    def __init__(self, target_wake_time: Optional[time] = None):
        """
        Initialize the bedtime calculator.

        Args:
            target_wake_time: Desired wake time (default: inferred from data)
        """
        self.target_wake_time = target_wake_time

    def analyze_best_nights(
        self,
        sleep_data: List[Dict],
        top_percentile: float = 0.25
    ) -> Dict:
        """
        Analyze sleep data to identify patterns from best nights.

        Args:
            sleep_data: List of sleep session data
            top_percentile: Top fraction of nights to analyze (default: top 25%)

        Returns:
            Dictionary with optimal bedtime recommendations
        """
        if not sleep_data:
            return self._empty_result("No sleep data available")

        # Extract and score sleep sessions
        scored_nights = []
        for session in sleep_data:
            if not isinstance(session, dict):
                continue

            score = self._calculate_sleep_quality_score(session)
            if score is None:
                continue

            # Parse bedtime
            bedtime_str = session.get("bedtime_start")
            if not bedtime_str:
                continue

            try:
                bedtime_dt = datetime.fromisoformat(bedtime_str.replace('Z', '+00:00'))

                scored_nights.append({
                    'score': score,
                    'bedtime': bedtime_dt,
                    'duration': session.get('total_sleep_duration', 0) / 3600,  # hours
                    'efficiency': session.get('efficiency', 0),
                    'deep_sleep': session.get('deep_sleep_duration', 0) / 3600,
                    'rem_sleep': session.get('rem_sleep_duration', 0) / 3600,
                    'latency': session.get('latency', 0) / 60,  # minutes
                    'restlessness': session.get('restlessness', 0),
                    'wake_time': bedtime_dt + timedelta(seconds=session.get('total_sleep_duration', 0))
                })
            except (ValueError, TypeError):
                continue

        if not scored_nights:
            return self._empty_result("No valid sleep sessions found")

        # Sort by score and take top percentile
        scored_nights.sort(key=lambda x: x['score'], reverse=True)
        top_count = max(1, int(len(scored_nights) * top_percentile))
        best_nights = scored_nights[:top_count]
        all_nights = scored_nights

        # Analyze patterns
        optimal_bedtime = self._calculate_optimal_bedtime(best_nights)
        bedtime_window = self._calculate_bedtime_window(best_nights)
        optimal_duration = mean([n['duration'] for n in best_nights])

        # Calculate consistency metrics
        bedtime_consistency = self._calculate_consistency(
            [n['bedtime'] for n in best_nights]
        )

        # Day-of-week patterns
        weekday_patterns = self._analyze_weekday_patterns(best_nights, all_nights)

        # Calculate recommended wake time
        if self.target_wake_time:
            recommended_wake_time = self.target_wake_time
        else:
            recommended_wake_time = self._calculate_optimal_wake_time(best_nights)

        # Generate sleep window recommendation
        sleep_window = self._calculate_sleep_window(
            optimal_bedtime,
            optimal_duration
        )

        return {
            'optimal_bedtime': optimal_bedtime,
            'bedtime_window': bedtime_window,
            'optimal_duration': optimal_duration,
            'recommended_wake_time': recommended_wake_time,
            'sleep_window': sleep_window,
            'bedtime_consistency': bedtime_consistency,
            'weekday_patterns': weekday_patterns,
            'best_nights_analyzed': len(best_nights),
            'total_nights_analyzed': len(all_nights),
            'average_score': mean([n['score'] for n in best_nights]),
            'quality_metrics': self._extract_quality_metrics(best_nights),
            'comparison_to_average': self._compare_to_average(best_nights, all_nights)
        }

    def _calculate_sleep_quality_score(self, session: Dict) -> Optional[float]:
        """
        Calculate composite sleep quality score (0-100).

        Weights:
        - Efficiency: 25%
        - Duration (relative to 8h optimal): 20%
        - Deep sleep percentage: 20%
        - REM sleep percentage: 20%
        - Low latency: 10%
        - Low restlessness: 5%
        """
        try:
            efficiency = session.get('efficiency', 0)
            duration = session.get('total_sleep_duration', 0) / 3600
            deep_sleep = session.get('deep_sleep_duration', 0)
            rem_sleep = session.get('rem_sleep_duration', 0)
            total_duration = session.get('total_sleep_duration', 1)
            latency = session.get('latency', 0) / 60  # minutes
            restlessness = session.get('restlessness', 0)

            if total_duration == 0:
                return None

            # Calculate component scores
            efficiency_score = efficiency  # Already 0-100

            # Duration score (optimal = 8h)
            duration_score = 100 * (1 - abs(duration - 8) / 8)
            duration_score = max(0, min(100, duration_score))

            # Deep sleep score (optimal = 15-20% of total)
            deep_pct = (deep_sleep / total_duration) * 100
            if 15 <= deep_pct <= 20:
                deep_score = 100
            else:
                deep_score = 100 - abs(deep_pct - 17.5) * 3
            deep_score = max(0, min(100, deep_score))

            # REM sleep score (optimal = 20-25% of total)
            rem_pct = (rem_sleep / total_duration) * 100
            if 20 <= rem_pct <= 25:
                rem_score = 100
            else:
                rem_score = 100 - abs(rem_pct - 22.5) * 3
            rem_score = max(0, min(100, rem_score))

            # Latency score (optimal = 10-20 min)
            if 10 <= latency <= 20:
                latency_score = 100
            elif latency < 10:
                latency_score = 100 - (10 - latency) * 5
            else:
                latency_score = 100 - (latency - 20) * 2
            latency_score = max(0, min(100, latency_score))

            # Restlessness score (lower is better)
            restlessness_score = max(0, 100 - restlessness * 2)

            # Weighted composite
            score = (
                efficiency_score * 0.25 +
                duration_score * 0.20 +
                deep_score * 0.20 +
                rem_score * 0.20 +
                latency_score * 0.10 +
                restlessness_score * 0.05
            )

            return score

        except (KeyError, TypeError, ZeroDivisionError):
            return None

    def _calculate_optimal_bedtime(self, nights: List[Dict]) -> time:
        """Calculate average bedtime from best nights."""
        # Convert to minutes since midnight for averaging
        minutes_list = []
        for night in nights:
            bt = night['bedtime']
            minutes = bt.hour * 60 + bt.minute
            # Handle bedtimes after midnight (e.g., 1 AM = 1440 + 60)
            if minutes < 12 * 60:  # Before noon likely means after midnight
                minutes += 24 * 60
            minutes_list.append(minutes)

        avg_minutes = int(mean(minutes_list))

        # Convert back to time
        hours = (avg_minutes // 60) % 24
        minutes = avg_minutes % 60

        return time(hours, minutes)

    def _calculate_bedtime_window(self, nights: List[Dict]) -> Tuple[time, time]:
        """Calculate recommended bedtime window (±1 stdev)."""
        minutes_list = []
        for night in nights:
            bt = night['bedtime']
            minutes = bt.hour * 60 + bt.minute
            if minutes < 12 * 60:
                minutes += 24 * 60
            minutes_list.append(minutes)

        avg_minutes = mean(minutes_list)
        std_minutes = stdev(minutes_list) if len(minutes_list) > 1 else 30

        early = int(avg_minutes - std_minutes)
        late = int(avg_minutes + std_minutes)

        early_time = time((early // 60) % 24, early % 60)
        late_time = time((late // 60) % 24, late % 60)

        return (early_time, late_time)

    def _calculate_consistency(self, bedtimes: List[datetime]) -> float:
        """Calculate bedtime consistency score (0-100)."""
        if len(bedtimes) < 2:
            return 100.0

        minutes_list = []
        for bt in bedtimes:
            minutes = bt.hour * 60 + bt.minute
            if minutes < 12 * 60:
                minutes += 24 * 60
            minutes_list.append(minutes)

        std = stdev(minutes_list)

        # Convert stdev to consistency score
        # 30 min stdev = 100, 120 min stdev = 0
        consistency = max(0, 100 - (std - 30) * (100 / 90))

        return consistency

    def _analyze_weekday_patterns(
        self,
        best_nights: List[Dict],
        all_nights: List[Dict]
    ) -> Dict:
        """Analyze if certain days of week produce better sleep."""
        weekday_scores = {i: [] for i in range(7)}

        for night in all_nights:
            weekday = night['bedtime'].weekday()
            weekday_scores[weekday].append(night['score'])

        patterns = {}
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        for day_idx, scores in weekday_scores.items():
            if scores:
                patterns[day_names[day_idx]] = {
                    'avg_score': mean(scores),
                    'count': len(scores)
                }

        return patterns

    def _calculate_optimal_wake_time(self, nights: List[Dict]) -> time:
        """Calculate average wake time from best nights."""
        wake_minutes = []
        for night in nights:
            wt = night['wake_time']
            minutes = wt.hour * 60 + wt.minute
            wake_minutes.append(minutes)

        avg_minutes = int(mean(wake_minutes))
        hours = (avg_minutes // 60) % 24
        minutes = avg_minutes % 60

        return time(hours, minutes)

    def _calculate_sleep_window(
        self,
        bedtime: time,
        duration: float
    ) -> Tuple[time, time]:
        """Calculate sleep window from bedtime and duration."""
        bt_minutes = bedtime.hour * 60 + bedtime.minute
        wake_minutes = bt_minutes + int(duration * 60)

        wake_time = time((wake_minutes // 60) % 24, wake_minutes % 60)

        return (bedtime, wake_time)

    def _extract_quality_metrics(self, nights: List[Dict]) -> Dict:
        """Extract average quality metrics from best nights."""
        return {
            'avg_efficiency': mean([n['efficiency'] for n in nights]),
            'avg_duration': mean([n['duration'] for n in nights]),
            'avg_deep_sleep': mean([n['deep_sleep'] for n in nights]),
            'avg_rem_sleep': mean([n['rem_sleep'] for n in nights]),
            'avg_latency': mean([n['latency'] for n in nights]),
            'avg_restlessness': mean([n['restlessness'] for n in nights])
        }

    def _compare_to_average(
        self,
        best_nights: List[Dict],
        all_nights: List[Dict]
    ) -> Dict:
        """Compare best nights to overall average."""
        if not all_nights:
            return {}

        best_avg_score = mean([n['score'] for n in best_nights])
        overall_avg_score = mean([n['score'] for n in all_nights])

        best_avg_duration = mean([n['duration'] for n in best_nights])
        overall_avg_duration = mean([n['duration'] for n in all_nights])

        return {
            'score_improvement': best_avg_score - overall_avg_score,
            'duration_difference': best_avg_duration - overall_avg_duration,
            'score_percentile': (best_avg_score / overall_avg_score - 1) * 100
        }

    def _empty_result(self, reason: str) -> Dict:
        """Return empty result with reason."""
        return {
            'error': reason,
            'optimal_bedtime': None,
            'bedtime_window': None,
            'optimal_duration': None,
            'recommended_wake_time': None
        }

    def generate_recommendation_report(self, analysis: Dict) -> str:
        """Generate human-readable bedtime recommendation report."""
        if 'error' in analysis:
            return f"❌ Unable to calculate optimal bedtime: {analysis['error']}"

        report_lines = [
            "# 🌙 Optimal Bedtime Recommendation",
            "",
            f"*Based on analysis of your top {analysis['best_nights_analyzed']} nights (out of {analysis['total_nights_analyzed']} total)*",
            "",
            "## ⏰ Recommended Sleep Schedule",
            "",
            f"**Optimal Bedtime:** {analysis['optimal_bedtime'].strftime('%I:%M %p')}",
            f"**Bedtime Window:** {analysis['bedtime_window'][0].strftime('%I:%M %p')} - {analysis['bedtime_window'][1].strftime('%I:%M %p')}",
            f"**Optimal Sleep Duration:** {analysis['optimal_duration']:.1f} hours",
            f"**Recommended Wake Time:** {analysis['recommended_wake_time'].strftime('%I:%M %p')}",
            "",
            f"**Consistency Score:** {analysis['bedtime_consistency']:.0f}/100",
            "",
        ]

        # Quality metrics from best nights
        qm = analysis['quality_metrics']
        report_lines.extend([
            "## 🎯 What Makes Your Best Nights Great",
            "",
            f"- **Sleep Efficiency:** {qm['avg_efficiency']:.1f}%",
            f"- **Sleep Duration:** {qm['avg_duration']:.1f} hours",
            f"- **Deep Sleep:** {qm['avg_deep_sleep']:.1f} hours ({(qm['avg_deep_sleep']/qm['avg_duration']*100):.0f}%)",
            f"- **REM Sleep:** {qm['avg_rem_sleep']:.1f} hours ({(qm['avg_rem_sleep']/qm['avg_duration']*100):.0f}%)",
            f"- **Sleep Latency:** {qm['avg_latency']:.0f} minutes",
            f"- **Restlessness:** {qm['avg_restlessness']:.1f}%",
            "",
        ])

        # Comparison to average
        comp = analysis['comparison_to_average']
        if comp:
            report_lines.extend([
                "## 📊 Improvement Potential",
                "",
                f"Your best nights score **{comp['score_percentile']:.0f}%** higher than your average night!",
                "",
            ])

            if abs(comp['duration_difference']) > 0.5:
                if comp['duration_difference'] > 0:
                    report_lines.append(f"- You sleep **{comp['duration_difference']:.1f} hours longer** on your best nights")
                else:
                    report_lines.append(f"- You sleep **{abs(comp['duration_difference']):.1f} hours less** on your best nights")
                report_lines.append("")

        # Day of week patterns
        if analysis['weekday_patterns']:
            report_lines.extend([
                "## 📅 Day-of-Week Patterns",
                "",
            ])

            # Sort by score
            sorted_days = sorted(
                analysis['weekday_patterns'].items(),
                key=lambda x: x[1]['avg_score'],
                reverse=True
            )

            best_day = sorted_days[0]
            worst_day = sorted_days[-1]

            report_lines.extend([
                f"**Best sleep nights:** {best_day[0]} (avg score: {best_day[1]['avg_score']:.1f})",
                f"**Most challenging:** {worst_day[0]} (avg score: {worst_day[1]['avg_score']:.1f})",
                "",
            ])

        # Recommendations
        report_lines.extend([
            "## 💡 Personalized Recommendations",
            "",
            f"1. **Target bedtime:** Aim to be in bed by **{analysis['bedtime_window'][0].strftime('%I:%M %p')}**",
            f"2. **Flexibility window:** You can go to bed anytime between {analysis['bedtime_window'][0].strftime('%I:%M %p')} and {analysis['bedtime_window'][1].strftime('%I:%M %p')}",
            f"3. **Sleep duration:** Allow for **{analysis['optimal_duration']:.1f} hours** of sleep",
            f"4. **Wake time:** Set alarm for **{analysis['recommended_wake_time'].strftime('%I:%M %p')}**",
            "",
        ])

        # Consistency recommendations
        consistency = analysis['bedtime_consistency']
        if consistency < 70:
            report_lines.extend([
                "### ⚠️ Improve Consistency",
                "",
                "Your bedtime varies significantly. For better sleep quality:",
                "- Try to go to bed within a 30-minute window each night",
                "- Set a bedtime alarm 30 minutes before target bedtime",
                "- Maintain consistent schedule even on weekends",
                "",
            ])
        elif consistency > 85:
            report_lines.extend([
                "### ✅ Great Consistency!",
                "",
                "You maintain excellent bedtime consistency - keep it up!",
                "",
            ])

        # Optimal sleep environment
        report_lines.extend([
            "## 🛏️ Optimize Your Sleep Environment",
            "",
            "Based on your best nights, maintain these conditions:",
            "- **Temperature:** Cool (65-68°F / 18-20°C)",
            "- **Darkness:** Complete darkness or sleep mask",
            "- **Quiet:** Minimize noise or use white noise",
            "- **Pre-sleep routine:** Start winding down 30-60 min before bedtime",
            "",
        ])

        return "\n".join(report_lines)
