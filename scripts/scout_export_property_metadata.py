#!/usr/bin/env python3
"""
SCOUT Property Metadata Exporter
Exports events from BigQuery to JSON for configuration UI

Purpose: Support Option 2 (Pre-generated JSON) for configuration interface
Cost: ~$0.30 for all 70 properties (one-time query)
"""

import json
import logging
from pathlib import Path
from typing import Dict, List
from google.cloud import bigquery

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScoutMetadataExporter:
    """Export property metadata from BigQuery to JSON files"""

    def __init__(self, project_id: str = "st-ga4-data"):
        self.project_id = project_id
        self.client = bigquery.Client(project=project_id)
        self.output_dir = Path("data")
        self.output_dir.mkdir(exist_ok=True)

    def get_available_properties(self) -> List[Dict[str, str]]:
        """Load property list from scout_available_properties.json"""
        properties_file = self.output_dir / "scout_available_properties.json"

        if not properties_file.exists():
            logger.error(f"Properties file not found: {properties_file}")
            return []

        with open(properties_file, 'r', encoding='utf-8-sig') as f:
            return json.load(f)

    def extract_events_for_property(self, property_id: str, dataset_id: str) -> List[Dict[str, any]]:
        """
        Extract all event names with counts from a property (last 30 days)
        Returns: List of {event_name, event_count, unique_users, is_likely_conversion}
        """
        # Parse dataset from dataset_id format "st-ga4-data:analytics_XXXXXX"
        dataset = dataset_id.split(':')[1] if ':' in dataset_id else dataset_id

        query = f"""
        SELECT
          event_name,
          COUNT(*) as event_count,
          COUNT(DISTINCT user_pseudo_id) as unique_users
        FROM `{self.project_id}.{dataset}.events_*`
        WHERE _TABLE_SUFFIX BETWEEN
          FORMAT_DATE('%Y%m%d', DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY))
          AND FORMAT_DATE('%Y%m%d', DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY))
        GROUP BY event_name
        ORDER BY event_count DESC
        """

        try:
            results = self.client.query(query).result()
            events = []

            # Conversion detection patterns (suggested, not auto-selected)
            conversion_patterns = [
                'purchase', 'conversion', 'submit', 'signup', 'register',
                'subscribe', 'download', 'contact', 'lead', 'sale',
                'form_submit', 'booking', 'appointment', 'request'
            ]

            for row in results:
                is_likely_conversion = any(pattern in row.event_name.lower() for pattern in conversion_patterns)

                events.append({
                    'event_name': row.event_name,
                    'event_count': row.event_count,
                    'unique_users': row.unique_users,
                    'is_likely_conversion': is_likely_conversion
                })

            logger.info(f"Property {property_id}: Found {len(events)} events")
            return events

        except Exception as e:
            logger.error(f"Failed to extract events for {property_id}: {str(e)}")
            return []

    def export_all_property_metadata(self) -> Dict[str, any]:
        """
        Export event metadata for all available properties
        Returns: Summary statistics
        """
        properties = self.get_available_properties()

        if not properties:
            logger.error("No properties found to process")
            return {'success': False, 'error': 'No properties found'}

        logger.info(f"Starting metadata export for {len(properties)} properties...")

        all_metadata = {}
        success_count = 0
        error_count = 0

        for prop in properties:
            property_id = prop['property_id']
            dataset_id = prop['dataset_id']

            try:
                logger.info(f"Processing property {property_id}...")

                # Extract events only
                events = self.extract_events_for_property(property_id, dataset_id)

                all_metadata[property_id] = {
                    'property_id': property_id,
                    'dataset_id': dataset_id,
                    'events': events,
                    'total_events': len(events),
                    'suggested_conversions': [e['event_name'] for e in events if e['is_likely_conversion']]
                }

                success_count += 1

            except Exception as e:
                logger.error(f"Error processing property {property_id}: {str(e)}")
                error_count += 1
                all_metadata[property_id] = {
                    'property_id': property_id,
                    'dataset_id': dataset_id,
                    'error': str(e),
                    'events': []
                }

        # Save combined metadata to JSON
        output_file = self.output_dir / "scout_property_metadata.json"
        with open(output_file, 'w') as f:
            json.dump(all_metadata, f, indent=2)

        logger.info(f"✅ Metadata exported to {output_file}")
        logger.info(f"✅ Processed: {success_count} successful, {error_count} errors")

        return {
            'success': True,
            'output_file': str(output_file),
            'properties_processed': len(properties),
            'success_count': success_count,
            'error_count': error_count
        }


def main():
    """Execute metadata export"""
    exporter = ScoutMetadataExporter()

    print("\n🔍 SCOUT Property Metadata Exporter")
    print("=" * 50)

    results = exporter.export_all_property_metadata()

    if results['success']:
        print(f"\n✅ Export Complete!")
        print(f"Output: {results['output_file']}")
        print(f"Properties Processed: {results['properties_processed']}")
        print(f"Successful: {results['success_count']}")
        print(f"Errors: {results['error_count']}")
    else:
        print(f"\n❌ Export Failed: {results.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
