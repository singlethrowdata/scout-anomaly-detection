#!/usr/bin/env python3
"""
SCOUT Root Cause Correlation Engine
Correlates detected anomalies with external factors to identify likely causes
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class EventType(Enum):
    """Types of external events that can cause anomalies"""
    GOOGLE_ALGO = "google_algorithm_update"
    GOOGLE_ADS = "google_ads_change"
    GA4_UPDATE = "ga4_update"
    HOLIDAY = "holiday"
    INDUSTRY = "industry_event"
    SEASONAL = "seasonal_pattern"
    TECHNICAL = "technical_issue"
    ECONOMIC = "economic_event"
    WEEKEND = "weekend_effect"

@dataclass
class ExternalEvent:
    """External event that might cause anomalies"""
    date: str
    event_type: EventType
    name: str
    description: str
    impact_level: str  # low, medium, high, critical
    affected_metrics: List[str]  # which metrics this typically affects
    typical_duration_days: int  # how long effects usually last
    confidence_boost: float  # how much to boost correlation confidence

class SCOUTRootCauseAnalyzer:
    """Analyzes root causes by correlating with external events"""

    def __init__(self):
        # [R11]: Root cause correlation with external factors
        self.external_events = self._load_external_events()
        self.correlation_window_days = 2  # Look ±2 days around anomaly
        self.correlations = []

    def _load_external_events(self) -> Dict[str, List[ExternalEvent]]:
        """Load database of known external events"""
        # [R11]: External factor database

        # 2024 Google Algorithm Updates (confirmed)
        google_updates = [
            ExternalEvent(
                date="2024-03-05",
                event_type=EventType.GOOGLE_ALGO,
                name="March 2024 Core Update",
                description="Google core algorithm update affecting rankings",
                impact_level="high",
                affected_metrics=["sessions", "users", "page_views"],
                typical_duration_days=14,
                confidence_boost=0.85
            ),
            ExternalEvent(
                date="2024-05-02",
                event_type=EventType.GOOGLE_ALGO,
                name="May 2024 Core Update",
                description="Google core algorithm update",
                impact_level="high",
                affected_metrics=["sessions", "users", "page_views"],
                typical_duration_days=14,
                confidence_boost=0.85
            ),
            ExternalEvent(
                date="2024-08-15",
                event_type=EventType.GOOGLE_ALGO,
                name="August 2024 Core Update",
                description="Google core algorithm update",
                impact_level="high",
                affected_metrics=["sessions", "users"],
                typical_duration_days=10,
                confidence_boost=0.85
            ),
            ExternalEvent(
                date="2024-09-19",
                event_type=EventType.GOOGLE_ALGO,
                name="September 2024 Spam Update",
                description="Google spam algorithm update",
                impact_level="medium",
                affected_metrics=["sessions", "users"],
                typical_duration_days=7,
                confidence_boost=0.70
            ),
            ExternalEvent(
                date="2024-11-05",
                event_type=EventType.GOOGLE_ALGO,
                name="November 2024 Core Update",
                description="Google core algorithm update",
                impact_level="high",
                affected_metrics=["sessions", "users", "page_views"],
                typical_duration_days=14,
                confidence_boost=0.85
            )
        ]

        # Major 2024-2025 Holidays (US market focused)
        holidays = [
            ExternalEvent(
                date="2024-11-28",
                event_type=EventType.HOLIDAY,
                name="Thanksgiving",
                description="US Thanksgiving holiday",
                impact_level="high",
                affected_metrics=["sessions", "users", "conversions"],
                typical_duration_days=4,
                confidence_boost=0.90
            ),
            ExternalEvent(
                date="2024-11-29",
                event_type=EventType.HOLIDAY,
                name="Black Friday",
                description="Major shopping holiday",
                impact_level="critical",
                affected_metrics=["sessions", "users", "conversions", "page_views"],
                typical_duration_days=3,
                confidence_boost=0.95
            ),
            ExternalEvent(
                date="2024-12-02",
                event_type=EventType.HOLIDAY,
                name="Cyber Monday",
                description="Online shopping holiday",
                impact_level="high",
                affected_metrics=["sessions", "conversions", "page_views"],
                typical_duration_days=1,
                confidence_boost=0.90
            ),
            ExternalEvent(
                date="2024-12-25",
                event_type=EventType.HOLIDAY,
                name="Christmas",
                description="Christmas holiday",
                impact_level="high",
                affected_metrics=["sessions", "users"],
                typical_duration_days=3,
                confidence_boost=0.85
            ),
            ExternalEvent(
                date="2025-01-01",
                event_type=EventType.HOLIDAY,
                name="New Year's Day",
                description="New Year holiday",
                impact_level="medium",
                affected_metrics=["sessions", "users"],
                typical_duration_days=1,
                confidence_boost=0.75
            ),
            ExternalEvent(
                date="2025-07-04",
                event_type=EventType.HOLIDAY,
                name="Independence Day",
                description="US Independence Day",
                impact_level="medium",
                affected_metrics=["sessions", "users"],
                typical_duration_days=3,
                confidence_boost=0.75
            ),
            ExternalEvent(
                date="2025-09-01",
                event_type=EventType.HOLIDAY,
                name="Labor Day",
                description="US Labor Day",
                impact_level="medium",
                affected_metrics=["sessions", "users"],
                typical_duration_days=3,
                confidence_boost=0.70
            )
        ]

        # GA4 and Technical Events
        technical_events = [
            ExternalEvent(
                date="2024-07-01",
                event_type=EventType.GA4_UPDATE,
                name="UA Sunset",
                description="Universal Analytics stopped processing data",
                impact_level="critical",
                affected_metrics=["sessions", "users", "conversions", "page_views"],
                typical_duration_days=30,
                confidence_boost=0.95
            ),
            ExternalEvent(
                date="2024-09-17",
                event_type=EventType.TECHNICAL,
                name="iOS 18 Release",
                description="iOS 18 with enhanced privacy features",
                impact_level="medium",
                affected_metrics=["users", "sessions"],
                typical_duration_days=7,
                confidence_boost=0.65
            ),
            ExternalEvent(
                date="2024-10-15",
                event_type=EventType.GA4_UPDATE,
                name="GA4 Consent Mode v2",
                description="Google Analytics consent mode v2 enforcement",
                impact_level="high",
                affected_metrics=["users", "conversions"],
                typical_duration_days=14,
                confidence_boost=0.75
            )
        ]

        # Seasonal Patterns
        seasonal_events = [
            ExternalEvent(
                date="2025-01-02",
                event_type=EventType.SEASONAL,
                name="New Year Return",
                description="Return to normal traffic after holidays",
                impact_level="medium",
                affected_metrics=["sessions", "users", "conversions"],
                typical_duration_days=5,
                confidence_boost=0.60
            ),
            ExternalEvent(
                date="2025-08-15",
                event_type=EventType.SEASONAL,
                name="Back to School",
                description="Back to school shopping season",
                impact_level="medium",
                affected_metrics=["sessions", "conversions"],
                typical_duration_days=14,
                confidence_boost=0.65
            )
        ]

        # Combine all events into a date-indexed dictionary
        all_events = google_updates + holidays + technical_events + seasonal_events

        events_by_date = {}
        for event in all_events:
            if event.date not in events_by_date:
                events_by_date[event.date] = []
            events_by_date[event.date].append(event)

        print(f"📚 Loaded {len(all_events)} external events for correlation")
        return events_by_date

    def correlate_with_anomalies(self, anomalies: List[Dict], pattern_type: str = None) -> List[Dict]:
        """Correlate anomalies with external events to find root causes"""
        # [R11]: Correlation logic
        correlations = []

        for anomaly in anomalies:
            anomaly_date = anomaly.get('date', '')
            if not anomaly_date:
                continue

            # Find potential causes within window
            potential_causes = self._find_events_in_window(
                anomaly_date,
                self.correlation_window_days
            )

            # Score each potential cause
            scored_causes = []
            for event in potential_causes:
                score = self._calculate_correlation_score(
                    anomaly, event, pattern_type
                )
                if score > 0.3:  # Minimum threshold
                    scored_causes.append({
                        'event': event,
                        'correlation_score': score,
                        'confidence': self._score_to_confidence(score)
                    })

            # Sort by score and take top causes
            scored_causes.sort(key=lambda x: x['correlation_score'], reverse=True)

            if scored_causes:
                correlation = {
                    'anomaly_date': anomaly_date,
                    'anomaly_metric': anomaly.get('metric', ''),
                    'anomaly_severity': anomaly.get('severity', 0),
                    'likely_causes': scored_causes[:3],  # Top 3 causes
                    'primary_cause': scored_causes[0]['event'].name,
                    'primary_confidence': scored_causes[0]['confidence']
                }
                correlations.append(correlation)

        self.correlations = correlations
        return correlations

    def _find_events_in_window(self, date_str: str, window_days: int) -> List[ExternalEvent]:
        """Find external events within ±window_days of the given date"""
        events = []

        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return events

        for days_offset in range(-window_days, window_days + 1):
            check_date = target_date + timedelta(days=days_offset)
            check_date_str = check_date.strftime('%Y-%m-%d')

            if check_date_str in self.external_events:
                events.extend(self.external_events[check_date_str])

        # Also check for weekend effects
        if target_date.weekday() == 0:  # Monday
            events.append(ExternalEvent(
                date=date_str,
                event_type=EventType.WEEKEND,
                name="Monday (Weekend Recovery)",
                description="Traffic recovery after weekend",
                impact_level="low",
                affected_metrics=["sessions", "users"],
                typical_duration_days=1,
                confidence_boost=0.40
            ))

        return events

    def _calculate_correlation_score(self, anomaly: Dict, event: ExternalEvent,
                                    pattern_type: str = None) -> float:
        """Calculate correlation score between anomaly and event"""
        score = 0.0

        # Base score from event confidence
        score = event.confidence_boost

        # Adjust based on metric match
        anomaly_metric = anomaly.get('metric', '').lower()
        if anomaly_metric in [m.lower() for m in event.affected_metrics]:
            score *= 1.2  # 20% boost for metric match
        else:
            score *= 0.7  # 30% penalty for metric mismatch

        # Adjust based on severity match
        anomaly_severity = anomaly.get('severity', 50)
        if event.impact_level == 'critical' and anomaly_severity > 80:
            score *= 1.3
        elif event.impact_level == 'high' and anomaly_severity > 60:
            score *= 1.2
        elif event.impact_level == 'medium' and anomaly_severity > 40:
            score *= 1.1
        elif event.impact_level == 'low' and anomaly_severity < 40:
            score *= 1.0
        else:
            score *= 0.8  # Severity mismatch

        # Boost for portfolio-wide patterns
        if pattern_type == 'portfolio_wide' and event.event_type in [
            EventType.GOOGLE_ALGO, EventType.GA4_UPDATE, EventType.TECHNICAL
        ]:
            score *= 1.4  # Portfolio patterns likely external

        # Cap at 1.0
        return min(score, 1.0)

    def _score_to_confidence(self, score: float) -> str:
        """Convert numerical score to confidence level"""
        if score > 0.8:
            return "very_high"
        elif score > 0.6:
            return "high"
        elif score > 0.4:
            return "medium"
        else:
            return "low"

    def generate_cause_summary(self) -> Dict:
        """Generate summary of root cause analysis"""
        # [R11]: Summary generation
        if not self.correlations:
            return {
                'total_correlations': 0,
                'top_causes': [],
                'cause_distribution': {}
            }

        # Count cause types
        cause_counts = {}
        for correlation in self.correlations:
            for cause in correlation['likely_causes']:
                cause_type = cause['event'].event_type.value
                cause_counts[cause_type] = cause_counts.get(cause_type, 0) + 1

        # Find most common causes
        top_causes = []
        cause_name_counts = {}
        for correlation in self.correlations:
            primary = correlation['primary_cause']
            cause_name_counts[primary] = cause_name_counts.get(primary, 0) + 1

        for cause_name, count in sorted(cause_name_counts.items(),
                                       key=lambda x: x[1], reverse=True)[:5]:
            top_causes.append({
                'cause': cause_name,
                'anomaly_count': count,
                'percentage': count / len(self.correlations) * 100
            })

        return {
            'total_correlations': len(self.correlations),
            'top_causes': top_causes,
            'cause_distribution': cause_counts,
            'high_confidence_count': sum(
                1 for c in self.correlations
                if c['primary_confidence'] in ['high', 'very_high']
            )
        }

    def enhance_alerts_with_causes(self, alerts: List[Dict]) -> List[Dict]:
        """Add root cause information to alerts"""
        # [R11]: Integration with alert system
        enhanced_alerts = []

        for alert in alerts:
            enhanced = alert.copy()

            # Find matching correlation
            matching_correlation = None
            for correlation in self.correlations:
                if (correlation['anomaly_date'] == alert.get('date') and
                    correlation['anomaly_metric'] == alert.get('metric')):
                    matching_correlation = correlation
                    break

            if matching_correlation:
                enhanced['root_cause'] = {
                    'primary_cause': matching_correlation['primary_cause'],
                    'confidence': matching_correlation['primary_confidence'],
                    'explanation': self._generate_cause_explanation(
                        matching_correlation['likely_causes'][0]
                    ),
                    'action_recommendation': self._generate_action_recommendation(
                        matching_correlation['likely_causes'][0]
                    )
                }
            else:
                enhanced['root_cause'] = {
                    'primary_cause': 'Unknown',
                    'confidence': 'low',
                    'explanation': 'No clear external cause identified',
                    'action_recommendation': 'Investigate client-specific factors'
                }

            enhanced_alerts.append(enhanced)

        return enhanced_alerts

    def _generate_cause_explanation(self, scored_cause: Dict) -> str:
        """Generate human-readable explanation of cause"""
        event = scored_cause['event']
        confidence = scored_cause['confidence']

        explanations = {
            EventType.GOOGLE_ALGO: f"This anomaly aligns with {event.name}, which typically affects organic traffic for up to {event.typical_duration_days} days.",
            EventType.HOLIDAY: f"Traffic patterns affected by {event.name}. This is expected seasonal behavior.",
            EventType.GA4_UPDATE: f"GA4 platform change: {event.description}. May require tracking adjustments.",
            EventType.TECHNICAL: f"Technical factor: {event.description}. Monitor for persistent impact.",
            EventType.SEASONAL: f"Seasonal pattern: {event.description}. Compare with previous year data.",
            EventType.WEEKEND: "Normal weekend recovery pattern. No action needed.",
        }

        base_explanation = explanations.get(
            event.event_type,
            f"External event detected: {event.description}"
        )

        return f"{base_explanation} (Confidence: {confidence})"

    def _generate_action_recommendation(self, scored_cause: Dict) -> str:
        """Generate recommended action based on cause"""
        event = scored_cause['event']

        actions = {
            EventType.GOOGLE_ALGO: "Review search rankings and content quality. Algorithm effects typically stabilize within 2 weeks.",
            EventType.HOLIDAY: "Expected variation. Compare with previous year's holiday performance.",
            EventType.GA4_UPDATE: "Check tracking implementation. May need configuration updates.",
            EventType.TECHNICAL: "Monitor closely. Contact development team if issues persist.",
            EventType.SEASONAL: "Normal seasonal variation. Adjust forecasts accordingly.",
            EventType.WEEKEND: "No action required. Normal weekly pattern.",
        }

        return actions.get(
            event.event_type,
            "Monitor situation and gather more data."
        )


def test_root_cause_analysis():
    """Test root cause correlation with sample data"""
    print("\n🔬 Testing SCOUT Root Cause Analysis")
    print("=" * 50)

    # Create analyzer
    analyzer = SCOUTRootCauseAnalyzer()

    # Create test anomalies around known events
    test_anomalies = [
        {
            'date': '2024-11-29',  # Black Friday
            'metric': 'conversions',
            'severity': 85,
            'z_score': 3.5
        },
        {
            'date': '2024-11-30',  # Day after Black Friday
            'metric': 'sessions',
            'severity': 75,
            'z_score': 2.8
        },
        {
            'date': '2024-03-06',  # Day after Google Core Update
            'metric': 'users',
            'severity': 70,
            'z_score': 2.5
        },
        {
            'date': '2024-09-20',  # Day after Spam Update
            'metric': 'sessions',
            'severity': 55,
            'z_score': 2.1
        },
        {
            'date': '2025-01-02',  # New Year return
            'metric': 'conversions',
            'severity': 45,
            'z_score': 2.0
        }
    ]

    # Run correlation analysis
    print("\n🔍 Correlating anomalies with external events...")
    correlations = analyzer.correlate_with_anomalies(test_anomalies, 'portfolio_wide')

    print(f"\n📊 Found {len(correlations)} correlations:")
    for corr in correlations:
        print(f"\n  📅 {corr['anomaly_date']} - {corr['anomaly_metric']}")
        print(f"     Primary Cause: {corr['primary_cause']}")
        print(f"     Confidence: {corr['primary_confidence']}")
        for i, cause in enumerate(corr['likely_causes'][:2], 1):
            print(f"     Alternative {i}: {cause['event'].name} "
                  f"(score: {cause['correlation_score']:.2f})")

    # Generate summary
    summary = analyzer.generate_cause_summary()
    print(f"\n📈 Root Cause Summary:")
    print(f"   Total Correlations: {summary['total_correlations']}")
    print(f"   High Confidence: {summary['high_confidence_count']}")

    if summary['top_causes']:
        print(f"\n   Top Causes:")
        for cause in summary['top_causes']:
            print(f"   • {cause['cause']}: {cause['anomaly_count']} anomalies "
                  f"({cause['percentage']:.1f}%)")

    # Test alert enhancement
    print("\n🚨 Testing Alert Enhancement...")
    test_alerts = [
        {
            'date': '2024-11-29',
            'metric': 'conversions',
            'severity': 85,
            'message': 'Critical anomaly detected'
        }
    ]

    enhanced = analyzer.enhance_alerts_with_causes(test_alerts)
    for alert in enhanced:
        print(f"\n   Original: {alert['message']}")
        print(f"   Root Cause: {alert['root_cause']['primary_cause']}")
        print(f"   Explanation: {alert['root_cause']['explanation']}")
        print(f"   Action: {alert['root_cause']['action_recommendation']}")

    # Save results
    output = {
        'test_anomalies': test_anomalies,
        'correlations': correlations,
        'summary': summary,
        'enhanced_alerts': enhanced
    }

    output_file = 'data/scout_root_cause_analysis.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\n✅ Root cause analysis complete! Results saved to {output_file}")
    print(f"\n🎯 Success: {summary['high_confidence_count']}/{len(correlations)} "
          f"correlations have high confidence!")


def main():
    """Main entry point"""
    test_root_cause_analysis()


if __name__ == "__main__":
    main()