# [R13]: Dynamic segment builder interface
# → needs: schema-registry
# → provides: client-specific-configuration

import csv
import pandas as pd
from typing import Dict, List, Optional
import os

class ScoutClientConfig:
    """
    SCOUT client configuration manager for custom conversion events and 404 pages.
    Loads from CSV file that can be maintained in Google Sheets.
    """

    def __init__(self, config_file_path: str = "data/scout_client_config.csv"):
        self.config_file = config_file_path
        self.clients = {}
        self.load_config()

    def load_config(self):
        """Load client configuration from CSV file"""
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"Client config file not found: {self.config_file}")

        with open(self.config_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                property_id = row['property_id'].strip()
                conversion_events = [event.strip() for event in row['conversion_events'].split(',') if event.strip()]

                self.clients[property_id] = {
                    'client_name': row['client_name'].strip(),
                    'domain': row['domain'].strip(),
                    'conversion_events': conversion_events,
                    'page_404_url': row['404_page_url'].strip() if row['404_page_url'].strip() else None,
                    'notes': row['notes'].strip() if row['notes'].strip() else None
                }

    def get_client_info(self, property_id: str) -> Optional[Dict]:
        """Get complete client configuration by property ID"""
        return self.clients.get(str(property_id))

    def get_conversion_events(self, property_id: str) -> List[str]:
        """Get list of conversion event names for a specific client"""
        client = self.clients.get(str(property_id))
        return client['conversion_events'] if client else []

    def get_404_page_url(self, property_id: str) -> Optional[str]:
        """Get 404 page URL for a specific client"""
        client = self.clients.get(str(property_id))
        return client.get('page_404_url') if client else None

    def get_all_property_ids(self) -> List[str]:
        """Get list of all configured property IDs"""
        return list(self.clients.keys())

    def get_client_domain(self, property_id: str) -> Optional[str]:
        """Get client domain for URL validation"""
        client = self.clients.get(str(property_id))
        return client.get('domain') if client else None

    def generate_conversion_events_sql(self, property_id: str) -> str:
        """Generate SQL WHERE clause for conversion events"""
        conversion_events = self.get_conversion_events(property_id)
        if not conversion_events:
            # Fallback to common conversion events
            conversion_events = ['purchase', 'conversion', 'lead', 'contact', 'submit']

        events_list = "', '".join(conversion_events)
        return f"event_name IN ('{events_list}')"

    def generate_404_detection_sql(self, property_id: str) -> str:
        """Generate SQL clause for 404 page detection"""
        page_404_url = self.get_404_page_url(property_id)
        domain = self.get_client_domain(property_id)

        conditions = []

        # Check for specific 404 page if configured
        if page_404_url:
            conditions.append(f"REGEXP_CONTAINS(page_location, r'.*{page_404_url}.*')")

        # Check for common 404 patterns
        conditions.extend([
            "REGEXP_CONTAINS(page_location, r'.*/404.*')",
            "REGEXP_CONTAINS(page_location, r'.*/not-found.*')",
            "REGEXP_CONTAINS(page_location, r'.*/error.*')",
            "REGEXP_CONTAINS(page_location, r'.*/page-not-found.*')"
        ])

        return f"({' OR '.join(conditions)})"

    def validate_config(self) -> Dict[str, List[str]]:
        """Validate client configuration and return any issues"""
        issues = {
            'missing_conversion_events': [],
            'missing_404_pages': [],
            'invalid_domains': []
        }

        for property_id, client in self.clients.items():
            if not client['conversion_events']:
                issues['missing_conversion_events'].append(f"{client['client_name']} ({property_id})")

            if not client.get('page_404_url'):
                issues['missing_404_pages'].append(f"{client['client_name']} ({property_id})")

            if not client.get('domain') or '.' not in client.get('domain', ''):
                issues['invalid_domains'].append(f"{client['client_name']} ({property_id})")

        return issues

# Convenience function for scripts
def load_client_config() -> ScoutClientConfig:
    """Load client configuration from default location"""
    return ScoutClientConfig()

# Example usage for testing
if __name__ == "__main__":
    config = load_client_config()

    print("Loaded configuration for properties:")
    for prop_id in config.get_all_property_ids():
        client_info = config.get_client_info(prop_id)
        print(f"  {client_info['client_name']} ({prop_id}): {len(client_info['conversion_events'])} events")

    # Validate configuration
    issues = config.validate_config()
    if any(issues.values()):
        print("\nConfiguration Issues Found:")
        for issue_type, items in issues.items():
            if items:
                print(f"  {issue_type}: {items}")
    else:
        print("\n✅ All client configurations valid")
