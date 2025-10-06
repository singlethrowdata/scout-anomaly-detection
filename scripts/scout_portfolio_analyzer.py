#!/usr/bin/env python3
"""
SCOUT Portfolio Pattern Analyzer - Cross-Client Anomaly Pattern Detection
Identifies patterns across multiple GA4 properties to detect:
- Industry-wide trends
- Google algorithm changes
- Seasonal patterns
- Common technical issues
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import statistics
from pathlib import Path

class SCOUTPortfolioAnalyzer:
    """Analyzes patterns across multiple client properties"""

    def __init__(self):
        self.patterns = {
            'simultaneous': [],      # Same day anomalies across clients
            'cascading': [],         # Sequential spread pattern
            'metric_specific': {},   # Patterns by metric type
            'day_of_week': {},       # Weekly pattern detection
            'magnitude_clusters': [] # Similar severity patterns
        }
        self.client_anomalies = {}
        self.pattern_threshold = 0.3  # 30% of clients = pattern

    def load_client_anomalies(self, client_id: str, anomaly_file: str) -> None:
        """Load anomaly data for a specific client"""
        # [R7]: Cross-client pattern recognition
        try:
            with open(anomaly_file, 'r') as f:
                data = json.load(f)
                self.client_anomalies[client_id] = data.get('anomalies', [])
                print(f"✅ Loaded {len(self.client_anomalies[client_id])} anomalies for client {client_id}")
        except FileNotFoundError:
            print(f"⚠️ No anomaly file found for client {client_id}")
            self.client_anomalies[client_id] = []

    def detect_simultaneous_patterns(self) -> List[Dict]:
        """Identify anomalies occurring on same date across multiple clients"""
        # [R7]: Portfolio-wide pattern detection
        date_anomalies = defaultdict(lambda: defaultdict(list))

        for client_id, anomalies in self.client_anomalies.items():
            for anomaly in anomalies:
                date = anomaly.get('date', '')
                metric = anomaly.get('metric', '')
                date_anomalies[date][metric].append({
                    'client': client_id,
                    'severity': anomaly.get('severity', 0),
                    'z_score': anomaly.get('z_score', 0)
                })

        # Find dates where multiple clients had anomalies
        patterns = []
        total_clients = len(self.client_anomalies)

        for date, metrics in date_anomalies.items():
            for metric, client_list in metrics.items():
                affected_ratio = len(client_list) / total_clients if total_clients > 0 else 0

                if affected_ratio >= self.pattern_threshold:
                    patterns.append({
                        'type': 'simultaneous',
                        'date': date,
                        'metric': metric,
                        'affected_clients': len(client_list),
                        'total_clients': total_clients,
                        'affected_ratio': affected_ratio,
                        'confidence': self._calculate_confidence(affected_ratio),
                        'likely_cause': self._infer_cause(date, metric, affected_ratio),
                        'client_details': client_list[:5]  # Sample for details
                    })

        self.patterns['simultaneous'] = patterns
        return patterns

    def detect_cascading_patterns(self) -> List[Dict]:
        """Identify anomalies that spread from client to client over days"""
        # [R7]: Sequential spread pattern detection
        metric_timelines = defaultdict(lambda: defaultdict(list))

        for client_id, anomalies in self.client_anomalies.items():
            for anomaly in anomalies:
                date = anomaly.get('date', '')
                metric = anomaly.get('metric', '')
                metric_timelines[metric][date].append(client_id)

        patterns = []
        for metric, timeline in metric_timelines.items():
            sorted_dates = sorted(timeline.keys())

            # Look for sequential spread over 3-7 days
            for i in range(len(sorted_dates) - 2):
                spread_window = []
                base_date = datetime.strptime(sorted_dates[i], '%Y-%m-%d')

                for j in range(i, min(i + 7, len(sorted_dates))):
                    check_date = datetime.strptime(sorted_dates[j], '%Y-%m-%d')
                    days_diff = (check_date - base_date).days

                    if days_diff <= 7:
                        spread_window.append({
                            'date': sorted_dates[j],
                            'clients': timeline[sorted_dates[j]],
                            'day_offset': days_diff
                        })

                if len(spread_window) >= 3:  # Pattern across 3+ days
                    total_affected = len(set(
                        client for day in spread_window
                        for client in day['clients']
                    ))

                    if total_affected >= len(self.client_anomalies) * self.pattern_threshold:
                        patterns.append({
                            'type': 'cascading',
                            'metric': metric,
                            'start_date': sorted_dates[i],
                            'duration_days': len(spread_window),
                            'affected_clients': total_affected,
                            'spread_pattern': spread_window[:3],  # First 3 days
                            'confidence': 'high' if total_affected > len(self.client_anomalies) * 0.5 else 'medium'
                        })

        self.patterns['cascading'] = patterns
        return patterns

    def detect_metric_correlations(self) -> Dict[str, List]:
        """Find metrics that commonly have anomalies together"""
        # [R7]: Metric correlation patterns
        client_metric_pairs = defaultdict(lambda: defaultdict(int))

        for client_id, anomalies in self.client_anomalies.items():
            # Group by date
            date_metrics = defaultdict(set)
            for anomaly in anomalies:
                date_metrics[anomaly.get('date', '')].add(anomaly.get('metric', ''))

            # Count co-occurrences
            for date, metrics in date_metrics.items():
                metrics_list = list(metrics)
                for i in range(len(metrics_list)):
                    for j in range(i + 1, len(metrics_list)):
                        pair = tuple(sorted([metrics_list[i], metrics_list[j]]))
                        client_metric_pairs[client_id][pair] += 1

        # Find common patterns
        correlations = defaultdict(list)
        for pair, client_counts in self._aggregate_metric_pairs(client_metric_pairs).items():
            if len(client_counts) >= len(self.client_anomalies) * self.pattern_threshold:
                correlations[pair[0]].append({
                    'correlated_metric': pair[1],
                    'occurrence_count': sum(client_counts.values()),
                    'affected_clients': len(client_counts),
                    'correlation_strength': self._calculate_correlation_strength(client_counts)
                })

        self.patterns['metric_specific'] = dict(correlations)
        return self.patterns['metric_specific']

    def identify_root_causes(self) -> List[Dict]:
        """Infer likely root causes for detected patterns"""
        # [R11]: Root cause correlation
        causes = []

        # Analyze simultaneous patterns
        for pattern in self.patterns['simultaneous']:
            cause = {
                'pattern_type': 'simultaneous',
                'date': pattern['date'],
                'metric': pattern['metric'],
                'affected_ratio': pattern['affected_ratio'],
                'likely_causes': []
            }

            # High ratio across all clients suggests external factor
            if pattern['affected_ratio'] > 0.7:
                cause['likely_causes'].append({
                    'cause': 'Google Algorithm Update',
                    'confidence': 0.85,
                    'evidence': f"{pattern['affected_clients']} clients affected simultaneously"
                })
            elif pattern['affected_ratio'] > 0.5:
                cause['likely_causes'].append({
                    'cause': 'Industry-wide Event',
                    'confidence': 0.7,
                    'evidence': 'Majority of portfolio impacted'
                })

            # Day of week patterns
            date_obj = datetime.strptime(pattern['date'], '%Y-%m-%d')
            if date_obj.weekday() == 0:  # Monday
                cause['likely_causes'].append({
                    'cause': 'Weekend Effect Recovery',
                    'confidence': 0.6,
                    'evidence': 'Monday anomaly pattern detected'
                })

            causes.append(cause)

        # Analyze cascading patterns
        for pattern in self.patterns['cascading']:
            causes.append({
                'pattern_type': 'cascading',
                'start_date': pattern['start_date'],
                'metric': pattern['metric'],
                'likely_causes': [{
                    'cause': 'Gradual Rollout or Propagating Issue',
                    'confidence': 0.75,
                    'evidence': f"Spread over {pattern['duration_days']} days across {pattern['affected_clients']} clients"
                }]
            })

        return causes

    def generate_portfolio_insights(self) -> Dict:
        """Generate comprehensive portfolio analysis"""
        # [R7]: Portfolio-wide insights generation
        total_anomalies = sum(len(a) for a in self.client_anomalies.values())

        insights = {
            'summary': {
                'total_clients_analyzed': len(self.client_anomalies),
                'total_anomalies_detected': total_anomalies,
                'portfolio_health_score': self._calculate_portfolio_health(),
                'analysis_timestamp': datetime.now().isoformat()
            },
            'patterns': {
                'simultaneous_events': len(self.patterns['simultaneous']),
                'cascading_patterns': len(self.patterns['cascading']),
                'correlated_metrics': len(self.patterns['metric_specific'])
            },
            'top_insights': [],
            'recommendations': []
        }

        # Generate top insights
        if self.patterns['simultaneous']:
            top_pattern = max(self.patterns['simultaneous'],
                            key=lambda x: x['affected_ratio'])
            insights['top_insights'].append({
                'insight': f"Major portfolio impact on {top_pattern['date']}",
                'detail': f"{top_pattern['affected_clients']} clients affected by {top_pattern['metric']} anomalies",
                'action': 'Investigate external factors for this date'
            })

        # Generate recommendations
        if total_anomalies > len(self.client_anomalies) * 5:
            insights['recommendations'].append({
                'priority': 'high',
                'recommendation': 'Portfolio showing elevated anomaly activity',
                'action': 'Review tracking implementation across all properties'
            })

        return insights

    def _calculate_confidence(self, affected_ratio: float) -> str:
        """Calculate pattern confidence level"""
        if affected_ratio > 0.7:
            return 'very_high'
        elif affected_ratio > 0.5:
            return 'high'
        elif affected_ratio > 0.3:
            return 'medium'
        else:
            return 'low'

    def _infer_cause(self, date: str, metric: str, ratio: float) -> str:
        """Infer likely cause based on pattern characteristics"""
        if ratio > 0.8:
            return 'External factor (Google update, industry event)'
        elif ratio > 0.5:
            return 'Common technical issue or seasonal pattern'
        elif 'conversion' in metric.lower():
            return 'Tracking or implementation issue'
        else:
            return 'Multiple independent causes'

    def _aggregate_metric_pairs(self, client_pairs: Dict) -> Dict:
        """Aggregate metric pair counts across clients"""
        total_pairs = defaultdict(dict)
        for client_id, pairs in client_pairs.items():
            for pair, count in pairs.items():
                total_pairs[pair][client_id] = count
        return total_pairs

    def _calculate_correlation_strength(self, counts: Dict) -> str:
        """Calculate strength of metric correlation"""
        avg_count = statistics.mean(counts.values()) if counts else 0
        if avg_count > 5:
            return 'strong'
        elif avg_count > 2:
            return 'moderate'
        else:
            return 'weak'

    def _calculate_portfolio_health(self) -> int:
        """Calculate overall portfolio health score (0-100)"""
        if not self.client_anomalies:
            return 100

        total_clients = len(self.client_anomalies)
        total_anomalies = sum(len(a) for a in self.client_anomalies.values())
        avg_anomalies = total_anomalies / total_clients if total_clients > 0 else 0

        # Health decreases with more anomalies
        health = max(0, 100 - (avg_anomalies * 10))

        # Penalize for widespread patterns
        if self.patterns['simultaneous']:
            health -= len(self.patterns['simultaneous']) * 5

        return max(0, min(100, int(health)))


def simulate_multi_client_anomalies():
    """Generate synthetic anomaly data for multiple clients for testing"""
    # [R7]: Test data generation for portfolio analysis
    import random

    clients = ['client_001', 'client_002', 'client_003', 'client_004', 'client_005']
    metrics = ['sessions', 'users', 'page_views', 'conversions']

    # Create a portfolio-wide event on 2025-09-15
    portfolio_event_date = '2025-09-15'

    for client_id in clients:
        anomalies = []

        # Add some random anomalies
        for _ in range(random.randint(2, 8)):
            anomalies.append({
                'date': f"2025-09-{random.randint(10, 20):02d}",
                'metric': random.choice(metrics),
                'severity': random.uniform(40, 80),
                'z_score': random.uniform(2.0, 4.0)
            })

        # Add portfolio-wide anomaly (simulating Google update)
        if random.random() > 0.2:  # 80% of clients affected
            anomalies.append({
                'date': portfolio_event_date,
                'metric': 'sessions',
                'severity': random.uniform(70, 90),
                'z_score': random.uniform(3.0, 5.0)
            })

        # Save to file
        output_file = f"data/test_anomalies_{client_id}.json"
        with open(output_file, 'w') as f:
            json.dump({'client_id': client_id, 'anomalies': anomalies}, f, indent=2)

        print(f"✅ Created test data for {client_id}: {len(anomalies)} anomalies")

    print(f"\n📊 Simulated portfolio-wide event on {portfolio_event_date}")


def main():
    """Run portfolio pattern analysis"""
    print("\n🔭 SCOUT Portfolio Pattern Analyzer")
    print("=" * 50)

    analyzer = SCOUTPortfolioAnalyzer()

    # Check for real client data first
    real_data_file = "data/scout_anomalies_249571600.json"
    if os.path.exists(real_data_file):
        print("\n📂 Loading real client anomaly data...")
        analyzer.load_client_anomalies('singlethrow_249571600', real_data_file)

    # Generate test data for additional clients
    print("\n🧪 Generating synthetic portfolio data for testing...")
    simulate_multi_client_anomalies()

    # Load all test client data
    print("\n📊 Loading portfolio anomaly data...")
    test_clients = ['client_001', 'client_002', 'client_003', 'client_004', 'client_005']
    for client_id in test_clients:
        analyzer.load_client_anomalies(client_id, f"data/test_anomalies_{client_id}.json")

    # Run pattern detection
    print("\n🔍 Detecting cross-client patterns...")

    # [R7]: Simultaneous patterns (same day anomalies)
    simultaneous = analyzer.detect_simultaneous_patterns()
    print(f"\n📍 Simultaneous Patterns Found: {len(simultaneous)}")
    for pattern in simultaneous[:3]:  # Show top 3
        print(f"  • {pattern['date']}: {pattern['metric']} affected "
              f"{pattern['affected_clients']}/{pattern['total_clients']} clients "
              f"({pattern['affected_ratio']:.1%})")
        print(f"    Likely cause: {pattern['likely_cause']}")

    # [R7]: Cascading patterns (spreading over time)
    cascading = analyzer.detect_cascading_patterns()
    print(f"\n🌊 Cascading Patterns Found: {len(cascading)}")
    for pattern in cascading[:3]:
        print(f"  • {pattern['metric']} spread over {pattern['duration_days']} days")
        print(f"    Starting {pattern['start_date']}, affected {pattern['affected_clients']} clients")

    # [R7]: Metric correlations
    correlations = analyzer.detect_metric_correlations()
    print(f"\n🔗 Metric Correlations Found: {len(correlations)} metrics with correlations")

    # [R11]: Root cause analysis
    print("\n🎯 Root Cause Analysis:")
    causes = analyzer.identify_root_causes()
    for cause in causes[:5]:  # Show top 5
        if cause['likely_causes']:
            top_cause = cause['likely_causes'][0]
            print(f"  • {cause.get('date', cause.get('start_date', 'Unknown'))}: "
                  f"{top_cause['cause']} (confidence: {top_cause['confidence']:.1%})")
            print(f"    Evidence: {top_cause['evidence']}")

    # Generate portfolio insights
    insights = analyzer.generate_portfolio_insights()

    print(f"\n📈 Portfolio Health Score: {insights['summary']['portfolio_health_score']}/100")
    print(f"   Total anomalies across portfolio: {insights['summary']['total_anomalies_detected']}")

    # Save results
    output_file = "data/scout_portfolio_analysis.json"
    with open(output_file, 'w') as f:
        json.dump({
            'insights': insights,
            'patterns': {
                'simultaneous': simultaneous,
                'cascading': cascading,
                'correlations': correlations
            },
            'root_causes': causes
        }, f, indent=2)

    print(f"\n✅ Portfolio analysis complete! Results saved to {output_file}")
    print(f"\n🎯 Key Finding: Detected portfolio-wide pattern affecting "
          f"{len(simultaneous)} simultaneous events - investigate external factors!")

    # Provide actionable next steps
    print("\n📋 Next Steps:")
    print("1. Review portfolio-wide patterns for Google algorithm updates")
    print("2. Investigate dates with >50% client impact")
    print("3. Set up automated alerts for future portfolio patterns")
    print("4. Consider creating client segments based on pattern susceptibility")


if __name__ == "__main__":
    main()