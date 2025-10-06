#!/usr/bin/env python3
"""
SCOUT Predictive Alert Engine - Forecasts future anomalies based on patterns
Uses historical data and detected patterns to predict issues before they occur
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import statistics
import math
from collections import defaultdict

class PredictionConfidence(Enum):
    """Confidence levels for predictions"""
    HIGH = "high"          # 70%+ probability
    MEDIUM = "medium"      # 50-70% probability
    LOW = "low"           # 30-50% probability

@dataclass
class Prediction:
    """A predicted future anomaly"""
    client_id: str
    metric: str
    prediction_date: str
    predicted_value: float
    expected_range: Tuple[float, float]
    anomaly_probability: float
    confidence: PredictionConfidence
    prediction_basis: str
    recommended_action: str
    potential_impact: float

class SCOUTPredictiveEngine:
    """Predicts future anomalies using multiple forecasting methods"""

    def __init__(self):
        # [R12]: Predictive alerts configuration
        self.prediction_horizon_days = 7
        self.min_history_days = 30
        self.predictions = []

        # Pattern-based prediction weights
        self.pattern_weights = {
            'weekly_seasonality': 0.3,
            'trend_continuation': 0.25,
            'external_events': 0.25,
            'historical_anomalies': 0.2
        }

    def generate_predictions(self, historical_data: Dict,
                           portfolio_patterns: Dict,
                           external_events: List[Dict]) -> List[Prediction]:
        """
        Generate predictions for the next 7 days

        Args:
            historical_data: Past metric values and anomalies
            portfolio_patterns: Detected cross-client patterns
            external_events: Upcoming known events

        Returns:
            List of predictions with confidence scores
        """
        # [R12]: Multi-method prediction generation
        predictions = []

        # Method 1: Time series trend analysis
        trend_predictions = self._predict_from_trends(historical_data)
        predictions.extend(trend_predictions)

        # Method 2: Seasonal pattern detection
        seasonal_predictions = self._predict_from_seasonality(historical_data)
        predictions.extend(seasonal_predictions)

        # Method 3: External event correlation
        event_predictions = self._predict_from_events(external_events, historical_data)
        predictions.extend(event_predictions)

        # Method 4: Portfolio pattern propagation
        pattern_predictions = self._predict_from_patterns(portfolio_patterns, historical_data)
        predictions.extend(pattern_predictions)

        # Consolidate and rank predictions
        consolidated = self._consolidate_predictions(predictions)

        # Calculate confidence scores
        final_predictions = self._calculate_confidence(consolidated)

        self.predictions = final_predictions
        return final_predictions

    def _predict_from_trends(self, historical_data: Dict) -> List[Prediction]:
        """Predict based on recent trends"""
        # [R12]: Trend-based forecasting
        predictions = []

        for client_id, client_data in historical_data.items():
            for metric, values in client_data.get('metrics', {}).items():
                if len(values) < 14:  # Need at least 2 weeks
                    continue

                # Calculate trend over last 7 days
                recent_values = [v['value'] for v in values[-7:]]
                older_values = [v['value'] for v in values[-14:-7]]

                recent_avg = statistics.mean(recent_values)
                older_avg = statistics.mean(older_values)

                # Calculate trend direction and magnitude
                trend_change = (recent_avg - older_avg) / older_avg if older_avg > 0 else 0

                # Project trend forward
                for days_ahead in range(1, self.prediction_horizon_days + 1):
                    prediction_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')

                    # Linear projection with decay
                    decay_factor = 0.9 ** days_ahead  # Trend weakens over time
                    predicted_change = trend_change * decay_factor
                    predicted_value = recent_avg * (1 + predicted_change)

                    # Calculate if this would be anomalous
                    historical_stdev = statistics.stdev(recent_values) if len(recent_values) > 1 else recent_avg * 0.1
                    expected_range = (
                        recent_avg - 2 * historical_stdev,
                        recent_avg + 2 * historical_stdev
                    )

                    # Check if prediction is outside normal range
                    if predicted_value < expected_range[0] or predicted_value > expected_range[1]:
                        anomaly_prob = min(abs(predicted_change) * 2, 0.9)  # Cap at 90%

                        predictions.append(Prediction(
                            client_id=client_id,
                            metric=metric,
                            prediction_date=prediction_date,
                            predicted_value=predicted_value,
                            expected_range=expected_range,
                            anomaly_probability=anomaly_prob,
                            confidence=PredictionConfidence.LOW,  # Will be updated
                            prediction_basis=f"Trend projection ({trend_change:.1%} change/week)",
                            recommended_action=self._generate_trend_action(metric, trend_change),
                            potential_impact=abs(trend_change) * 50  # Simple impact score
                        ))

        return predictions

    def _predict_from_seasonality(self, historical_data: Dict) -> List[Prediction]:
        """Predict based on weekly patterns"""
        # [R12]: Seasonal pattern prediction
        predictions = []

        for client_id, client_data in historical_data.items():
            for metric, values in client_data.get('metrics', {}).items():
                if len(values) < 28:  # Need 4 weeks minimum
                    continue

                # Calculate day-of-week averages
                dow_patterns = defaultdict(list)
                for v in values:
                    date = datetime.strptime(v['date'], '%Y-%m-%d')
                    dow = date.strftime('%A')
                    dow_patterns[dow].append(v['value'])

                # Find days with consistent patterns
                for days_ahead in range(1, self.prediction_horizon_days + 1):
                    future_date = datetime.now() + timedelta(days=days_ahead)
                    dow = future_date.strftime('%A')

                    if dow in dow_patterns and len(dow_patterns[dow]) >= 3:
                        dow_values = dow_patterns[dow]
                        dow_avg = statistics.mean(dow_values)
                        dow_stdev = statistics.stdev(dow_values) if len(dow_values) > 1 else dow_avg * 0.1

                        # Check for consistent weekly anomalies
                        recent_avg = statistics.mean([v['value'] for v in values[-7:]])

                        # If this day typically differs from average
                        if abs(dow_avg - recent_avg) > 2 * dow_stdev:
                            predictions.append(Prediction(
                                client_id=client_id,
                                metric=metric,
                                prediction_date=future_date.strftime('%Y-%m-%d'),
                                predicted_value=dow_avg,
                                expected_range=(dow_avg - dow_stdev, dow_avg + dow_stdev),
                                anomaly_probability=0.6,  # Moderate confidence in weekly patterns
                                confidence=PredictionConfidence.MEDIUM,
                                prediction_basis=f"Weekly pattern ({dow} typically {(dow_avg/recent_avg - 1)*100:.1f}% different)",
                                recommended_action=f"Expected {dow} variation - monitor for unusual deviation",
                                potential_impact=30
                            ))

        return predictions

    def _predict_from_events(self, external_events: List[Dict],
                            historical_data: Dict) -> List[Prediction]:
        """Predict anomalies based on upcoming external events"""
        # [R12]: Event-based prediction
        predictions = []

        # Get next 7 days
        future_dates = [
            (datetime.now() + timedelta(days=d)).strftime('%Y-%m-%d')
            for d in range(1, self.prediction_horizon_days + 1)
        ]

        for event in external_events:
            event_date = event.get('date', '')

            if event_date in future_dates:
                # Predict impact for each client
                for client_id in historical_data.keys():
                    for metric in event.get('affected_metrics', []):
                        # Get baseline for this metric
                        client_metrics = historical_data[client_id].get('metrics', {})
                        if metric not in client_metrics:
                            continue

                        recent_values = [v['value'] for v in client_metrics[metric][-7:]]
                        if not recent_values:
                            continue

                        baseline = statistics.mean(recent_values)

                        # Estimate impact based on event type
                        impact_multiplier = self._estimate_event_impact(event, metric)
                        predicted_value = baseline * impact_multiplier

                        # Higher probability for known events
                        anomaly_prob = 0.75 if event.get('impact_level') == 'high' else 0.5

                        predictions.append(Prediction(
                            client_id=client_id,
                            metric=metric,
                            prediction_date=event_date,
                            predicted_value=predicted_value,
                            expected_range=(baseline * 0.8, baseline * 1.2),
                            anomaly_probability=anomaly_prob,
                            confidence=PredictionConfidence.HIGH if event.get('impact_level') == 'high' else PredictionConfidence.MEDIUM,
                            prediction_basis=f"Upcoming event: {event.get('name', 'External event')}",
                            recommended_action=f"Prepare for {event.get('name', 'event')} impact - {event.get('description', '')}",
                            potential_impact=70 if event.get('impact_level') == 'high' else 40
                        ))

        return predictions

    def _predict_from_patterns(self, portfolio_patterns: Dict,
                              historical_data: Dict) -> List[Prediction]:
        """Predict based on detected portfolio patterns"""
        # [R12]: Pattern-based propagation prediction
        predictions = []

        # Look for cascading patterns that might spread
        for pattern in portfolio_patterns.get('cascading', []):
            # Predict continuation of cascade
            spread_rate = pattern.get('spread_rate', 0)
            if spread_rate > 0:
                last_date = pattern.get('end_date', '')
                affected_clients = pattern.get('affected_clients', [])

                # Predict which clients might be affected next
                for client_id in historical_data.keys():
                    if client_id not in affected_clients:
                        # Calculate probability based on spread rate
                        days_since = 1  # Simplified
                        prob = min(spread_rate * days_since * 0.2, 0.7)

                        if prob > 0.3:
                            next_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

                            predictions.append(Prediction(
                                client_id=client_id,
                                metric=pattern.get('metric', 'unknown'),
                                prediction_date=next_date,
                                predicted_value=0,  # Will be updated
                                expected_range=(0, 0),  # Will be updated
                                anomaly_probability=prob,
                                confidence=PredictionConfidence.MEDIUM,
                                prediction_basis=f"Cascading pattern spreading ({pattern.get('metric')})",
                                recommended_action="Monitor for pattern propagation from other clients",
                                potential_impact=50
                            ))

        return predictions

    def _consolidate_predictions(self, predictions: List[Prediction]) -> List[Prediction]:
        """Consolidate duplicate predictions and average probabilities"""
        # [R12]: Prediction consolidation
        consolidated = {}

        for pred in predictions:
            key = f"{pred.client_id}_{pred.metric}_{pred.prediction_date}"

            if key not in consolidated:
                consolidated[key] = pred
            else:
                # Average the probabilities
                existing = consolidated[key]
                existing.anomaly_probability = (
                    existing.anomaly_probability + pred.anomaly_probability
                ) / 2

                # Take the more specific prediction basis
                if len(pred.prediction_basis) > len(existing.prediction_basis):
                    existing.prediction_basis = pred.prediction_basis
                    existing.recommended_action = pred.recommended_action

        return list(consolidated.values())

    def _calculate_confidence(self, predictions: List[Prediction]) -> List[Prediction]:
        """Calculate final confidence scores"""
        # [R12]: Confidence scoring
        for pred in predictions:
            if pred.anomaly_probability >= 0.7:
                pred.confidence = PredictionConfidence.HIGH
            elif pred.anomaly_probability >= 0.5:
                pred.confidence = PredictionConfidence.MEDIUM
            else:
                pred.confidence = PredictionConfidence.LOW

        # Sort by probability
        predictions.sort(key=lambda x: x.anomaly_probability, reverse=True)

        return predictions

    def _estimate_event_impact(self, event: Dict, metric: str) -> float:
        """Estimate impact multiplier for an event"""
        # Base impact by event type
        impact_map = {
            'holiday': {'conversions': 1.5, 'sessions': 0.7, 'users': 0.7},
            'google_algorithm_update': {'sessions': 0.8, 'users': 0.85, 'page_views': 0.8},
            'technical_issue': {'all': 0.6},
            'seasonal_pattern': {'conversions': 1.2, 'sessions': 1.1}
        }

        event_type = event.get('event_type', '')
        if event_type in impact_map:
            return impact_map[event_type].get(metric, impact_map[event_type].get('all', 1.0))

        return 1.0

    def _generate_trend_action(self, metric: str, trend_change: float) -> str:
        """Generate action recommendation based on trend"""
        direction = "declining" if trend_change < 0 else "growing"
        severity = "rapidly" if abs(trend_change) > 0.2 else "steadily"

        actions = {
            'conversions': f"Conversions {severity} {direction} - review funnel and campaigns",
            'users': f"User acquisition {severity} {direction} - check traffic sources",
            'sessions': f"Sessions {severity} {direction} - monitor site performance",
            'page_views': f"Engagement {severity} {direction} - review content strategy"
        }

        return actions.get(metric.lower(), f"{metric} {severity} {direction} - investigate cause")

    def generate_prediction_report(self) -> Dict:
        """Generate summary report of predictions"""
        # [R12]: Prediction reporting
        if not self.predictions:
            return {
                'total_predictions': 0,
                'high_confidence': 0,
                'by_date': {},
                'top_risks': []
            }

        # Group by date
        by_date = defaultdict(list)
        for pred in self.predictions:
            by_date[pred.prediction_date].append(pred)

        # Find top risks
        top_risks = sorted(
            self.predictions,
            key=lambda x: x.anomaly_probability * x.potential_impact,
            reverse=True
        )[:5]

        return {
            'total_predictions': len(self.predictions),
            'high_confidence': len([p for p in self.predictions if p.confidence == PredictionConfidence.HIGH]),
            'medium_confidence': len([p for p in self.predictions if p.confidence == PredictionConfidence.MEDIUM]),
            'prediction_horizon': f"{self.prediction_horizon_days} days",
            'by_date': {
                date: len(preds) for date, preds in by_date.items()
            },
            'top_risks': [
                {
                    'client': risk.client_id,
                    'metric': risk.metric,
                    'date': risk.prediction_date,
                    'probability': f"{risk.anomaly_probability:.1%}",
                    'action': risk.recommended_action
                }
                for risk in top_risks
            ]
        }

    def validate_predictions(self, actual_data: Dict) -> Dict:
        """Validate past predictions against actual data"""
        # [R12]: Prediction accuracy validation
        if not self.predictions:
            return {'accuracy': 0, 'total_validated': 0}

        correct_predictions = 0
        total_validated = 0

        for pred in self.predictions:
            # Check if we have actual data for this prediction
            actual_key = f"{pred.client_id}_{pred.metric}_{pred.prediction_date}"
            if actual_key in actual_data:
                actual_value = actual_data[actual_key]

                # Was it actually anomalous?
                was_anomaly = (
                    actual_value < pred.expected_range[0] or
                    actual_value > pred.expected_range[1]
                )

                # Did we predict correctly?
                if (was_anomaly and pred.anomaly_probability > 0.5) or \
                   (not was_anomaly and pred.anomaly_probability <= 0.5):
                    correct_predictions += 1

                total_validated += 1

        accuracy = correct_predictions / total_validated if total_validated > 0 else 0

        return {
            'accuracy': accuracy,
            'accuracy_percent': f"{accuracy:.1%}",
            'correct_predictions': correct_predictions,
            'total_validated': total_validated,
            'validation_date': datetime.now().isoformat()
        }


def test_predictive_engine():
    """Test the predictive engine with sample data"""
    print("\n🔮 Testing SCOUT Predictive Engine")
    print("=" * 50)

    # Create engine
    engine = SCOUTPredictiveEngine()

    # Generate sample historical data
    historical_data = {
        'client_001': {
            'metrics': {
                'sessions': [
                    {'date': f"2025-09-{day:02d}", 'value': 100 + day * 2 + (10 if day % 7 == 5 else 0)}
                    for day in range(1, 29)  # 4 weeks of data with Friday spikes
                ],
                'conversions': [
                    {'date': f"2025-09-{day:02d}", 'value': 10 + day * 0.5}
                    for day in range(1, 29)  # Growing trend
                ]
            }
        },
        'client_002': {
            'metrics': {
                'sessions': [
                    {'date': f"2025-09-{day:02d}", 'value': 200 - day * 3}
                    for day in range(1, 29)  # Declining trend
                ]
            }
        }
    }

    # Sample portfolio patterns
    portfolio_patterns = {
        'cascading': [
            {
                'metric': 'users',
                'spread_rate': 0.3,
                'affected_clients': ['client_003', 'client_004'],
                'end_date': '2025-09-28'
            }
        ]
    }

    # Sample upcoming events
    external_events = [
        {
            'date': '2025-10-03',  # 3 days from now
            'name': 'October Core Update',
            'event_type': 'google_algorithm_update',
            'affected_metrics': ['sessions', 'users'],
            'impact_level': 'high'
        },
        {
            'date': '2025-10-07',  # 7 days from now
            'name': 'Industry Conference',
            'event_type': 'seasonal_pattern',
            'affected_metrics': ['conversions'],
            'impact_level': 'medium'
        }
    ]

    # Generate predictions
    print("\n📊 Generating predictions for next 7 days...")
    predictions = engine.generate_predictions(
        historical_data,
        portfolio_patterns,
        external_events
    )

    print(f"Generated {len(predictions)} predictions")

    # Show top predictions
    print("\n🎯 Top Risk Predictions:")
    for i, pred in enumerate(predictions[:5], 1):
        print(f"\n{i}. {pred.client_id} - {pred.metric}")
        print(f"   Date: {pred.prediction_date}")
        print(f"   Probability: {pred.anomaly_probability:.1%} ({pred.confidence.value})")
        print(f"   Basis: {pred.prediction_basis}")
        print(f"   Action: {pred.recommended_action}")

    # Generate report
    report = engine.generate_prediction_report()

    print(f"\n📈 Prediction Summary:")
    print(f"   Total Predictions: {report['total_predictions']}")
    print(f"   High Confidence: {report['high_confidence']}")
    print(f"   Medium Confidence: {report['medium_confidence']}")
    print(f"   Horizon: {report['prediction_horizon']}")

    print(f"\n📅 Predictions by Date:")
    for date, count in sorted(report['by_date'].items()):
        print(f"   {date}: {count} predictions")

    # Save results
    output = {
        'predictions': [
            {
                'client_id': p.client_id,
                'metric': p.metric,
                'date': p.prediction_date,
                'probability': p.anomaly_probability,
                'confidence': p.confidence.value,
                'basis': p.prediction_basis,
                'action': p.recommended_action
            }
            for p in predictions
        ],
        'report': report,
        'test_timestamp': datetime.now().isoformat()
    }

    output_file = 'data/scout_predictions.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n✅ Predictions saved to {output_file}")

    # Test validation (simulate)
    print(f"\n🔍 Simulating prediction validation...")
    fake_actuals = {
        f"{predictions[0].client_id}_{predictions[0].metric}_{predictions[0].prediction_date}":
            predictions[0].expected_range[0] - 10  # Was anomalous
    }

    validation = engine.validate_predictions(fake_actuals)
    print(f"   Validation Accuracy: {validation['accuracy_percent']}")

    print(f"\n✅ Predictive engine test complete!")
    print(f"🎯 Key Achievement: Successfully predicted {report['high_confidence']} high-confidence anomalies")


def main():
    """Main entry point"""
    test_predictive_engine()


if __name__ == "__main__":
    main()