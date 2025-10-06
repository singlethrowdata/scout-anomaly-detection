#!/usr/bin/env python3
"""
SCOUT Schema Discovery System
Automatically discovers GA4 schemas and custom events across all STM client properties

Purpose: Foundation for automated anomaly detection [R1]
- Scans all GA4 exports in STM BigQuery project
- Identifies custom events per client dynamically  
- Builds schema registry for downstream processing
- Handles schema changes gracefully

Cost Estimate: ~$0.50 per full discovery run (50 clients)
"""

import logging
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScoutSchemaDiscovery:
    """SCOUT's reconnaissance system for GA4 schema discovery"""
    
    def __init__(self, project_id: str = "stm-analytics-project"):
        self.project_id = project_id
        self.client = bigquery.Client(project=project_id)
        self.run_id = str(uuid.uuid4())
        
    def discover_client_properties(self) -> List[Dict[str, str]]:
        """
        Find all GA4 datasets in the project [R1]
        Returns: List of {client_id, property_id, dataset_name}
        """
        query = f"""
        SELECT 
          schema_name as dataset_name,
          REGEXP_EXTRACT(schema_name, r'analytics_(\d+)') as property_id
        FROM `{self.project_id}.INFORMATION_SCHEMA.SCHEMATA`
        WHERE schema_name LIKE 'analytics_%'
        ORDER BY schema_name
        """
        
        try:
            results = self.client.query(query).result()
            properties = []
            
            for row in results:
                if row.property_id:  # Valid GA4 dataset
                    # Extract client_id from property mapping (implement based on STM naming)
                    client_id = self._map_property_to_client(row.property_id)
                    
                    properties.append({
                        'client_id': client_id,
                        'property_id': row.property_id,
                        'dataset_name': row.dataset_name
                    })
                    
            logger.info(f"Discovered {len(properties)} GA4 properties")
            return properties
            
        except Exception as e:
            logger.error(f"Failed to discover properties: {str(e)}")
            return []
    
    def _map_property_to_client(self, property_id: str) -> str:
        """
        Map GA4 property ID to STM client identifier
        TODO: Implement actual STM client mapping logic
        """
        # Placeholder - replace with actual STM client mapping
        return f"client_{property_id[:6]}"
    def discover_table_schema(self, dataset_name: str, table_name: str = "events_*") -> Dict:
        """
        Get complete schema for GA4 events table [R1]
        Returns: Schema JSON and custom events list
        """
        # Get latest events table (yesterday's partition typically)
        table_query = f"""
        SELECT table_name
        FROM `{self.project_id}.{dataset_name}.INFORMATION_SCHEMA.TABLES`
        WHERE table_name LIKE 'events_2%'
        ORDER BY table_name DESC
        LIMIT 1
        """
        
        try:
            result = list(self.client.query(table_query).result())
            if not result:
                logger.warning(f"No events tables found in {dataset_name}")
                return {'schema_json': '{}', 'custom_events': [], 'conversion_events': []}
            
            latest_table = result[0].table_name
            table_ref = f"{self.project_id}.{dataset_name}.{latest_table}"
            
            # Get table schema
            table = self.client.get_table(table_ref)
            schema_json = json.dumps([
                {
                    'name': field.name,
                    'type': field.field_type,
                    'mode': field.mode,
                    'description': field.description
                }
                for field in table.schema
            ])
            
            # Discover custom events [R3]
            custom_events = self._discover_custom_events(table_ref)
            
            # Identify conversion events
            conversion_events = self._identify_conversion_events(custom_events)
            
            return {
                'schema_json': schema_json,
                'custom_events': custom_events,
                'conversion_events': conversion_events,
                'table_name': latest_table
            }
            
        except Exception as e:
            logger.error(f"Failed to discover schema for {dataset_name}: {str(e)}")
            return {'schema_json': '{}', 'custom_events': [], 'conversion_events': []}
    
    def _discover_custom_events(self, table_ref: str) -> List[str]:
        """
        Find all custom event names in the last 7 days [R3]
        Cost optimization: Sample and limit date range
        """
        query = f"""
        SELECT DISTINCT event_name
        FROM `{table_ref}`
        WHERE _TABLE_SUFFIX BETWEEN 
          FORMAT_DATE('%Y%m%d', DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY))
          AND FORMAT_DATE('%Y%m%d', DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY))
        AND event_name NOT IN (
          'session_start', 'first_visit', 'page_view', 'scroll', 
          'click', 'file_download', 'video_start', 'video_progress',
          'video_complete', 'form_start', 'form_submit'
        )
        ORDER BY event_name
        """
        
        try:
            results = self.client.query(query).result()
            custom_events = [row.event_name for row in results]
            logger.info(f"Found {len(custom_events)} custom events in {table_ref}")
            return custom_events
            
        except Exception as e:
            logger.error(f"Failed to discover custom events: {str(e)}")
            return []
    
    def _identify_conversion_events(self, custom_events: List[str]) -> List[str]:
        """
        Identify likely conversion events from custom event names [R3]
        Uses common conversion naming patterns
        """
        conversion_patterns = [
            'purchase', 'conversion', 'submit', 'signup', 'register',
            'subscribe', 'download', 'contact', 'lead', 'sale'
        ]
        
        conversions = []
        for event in custom_events:
            if any(pattern in event.lower() for pattern in conversion_patterns):
                conversions.append(event)
                
        return conversions
    def save_schema_to_registry(self, property_data: Dict, schema_data: Dict) -> bool:
        """
        Save discovered schema to BigQuery registry [R1]
        """
        # Create schema hash for change detection
        schema_content = schema_data['schema_json'] + str(sorted(schema_data['custom_events']))
        schema_hash = hashlib.md5(schema_content.encode()).hexdigest()
        
        # Check if schema already exists and unchanged
        existing_query = f"""
        SELECT schema_hash
        FROM `{self.project_id}.scout_metadata.client_schemas`
        WHERE client_id = @client_id AND property_id = @property_id
        ORDER BY last_discovered DESC
        LIMIT 1
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("client_id", "STRING", property_data['client_id']),
                bigquery.ScalarQueryParameter("property_id", "STRING", property_data['property_id'])
            ]
        )
        
        try:
            existing = list(self.client.query(existing_query, job_config=job_config).result())
            
            if existing and existing[0].schema_hash == schema_hash:
                logger.info(f"Schema unchanged for {property_data['client_id']}")
                return True
            
            # Insert new schema record
            insert_query = f"""
            INSERT INTO `{self.project_id}.scout_metadata.client_schemas` (
                client_id, property_id, dataset_name, table_name, schema_json,
                custom_events, conversion_events, last_discovered, schema_hash
            ) VALUES (
                @client_id, @property_id, @dataset_name, @table_name, @schema_json,
                @custom_events, @conversion_events, @timestamp, @schema_hash
            )
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("client_id", "STRING", property_data['client_id']),
                    bigquery.ScalarQueryParameter("property_id", "STRING", property_data['property_id']),
                    bigquery.ScalarQueryParameter("dataset_name", "STRING", property_data['dataset_name']),
                    bigquery.ScalarQueryParameter("table_name", "STRING", schema_data['table_name']),
                    bigquery.ScalarQueryParameter("schema_json", "STRING", schema_data['schema_json']),
                    bigquery.ArrayQueryParameter("custom_events", "STRING", schema_data['custom_events']),
                    bigquery.ArrayQueryParameter("conversion_events", "STRING", schema_data['conversion_events']),
                    bigquery.ScalarQueryParameter("timestamp", "TIMESTAMP", datetime.now(timezone.utc)),
                    bigquery.ScalarQueryParameter("schema_hash", "STRING", schema_hash)
                ]
            )
            
            self.client.query(insert_query, job_config=job_config).result()
            logger.info(f"Schema saved for {property_data['client_id']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save schema: {str(e)}")
            return False
    
    def run_discovery(self) -> Dict[str, int]:
        """
        Execute full SCOUT schema discovery process [R1]
        Returns: Summary statistics
        """
        start_time = datetime.now(timezone.utc)
        logger.info(f"Starting SCOUT schema discovery run {self.run_id}")
        
        # Discover all client properties
        properties = self.discover_client_properties()
        
        schemas_discovered = 0
        errors_encountered = 0
        
        # Process each property
        for prop in properties:
            try:
                logger.info(f"Processing {prop['client_id']} - {prop['property_id']}")
                
                # Discover schema and events
                schema_data = self.discover_table_schema(prop['dataset_name'])
                
                if schema_data['schema_json'] != '{}':
                    # Save to registry
                    if self.save_schema_to_registry(prop, schema_data):
                        schemas_discovered += 1
                    else:
                        errors_encountered += 1
                else:
                    logger.warning(f"No valid schema found for {prop['client_id']}")
                    errors_encountered += 1
                    
            except Exception as e:
                logger.error(f"Error processing {prop['client_id']}: {str(e)}")
                errors_encountered += 1
        
        # Log run summary
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        status = 'success' if errors_encountered == 0 else ('partial' if schemas_discovered > 0 else 'failed')
        
        self._log_discovery_run(len(properties), schemas_discovered, errors_encountered, duration, status)
        
        return {
            'clients_processed': len(properties),
            'schemas_discovered': schemas_discovered,
            'errors_encountered': errors_encountered,
            'duration_seconds': duration,
            'status': status
        }
    
    def _log_discovery_run(self, clients: int, discovered: int, errors: int, 
                          duration: float, status: str) -> None:
        """Log discovery run to tracking table"""
        
        query = f"""
        INSERT INTO `{self.project_id}.scout_metadata.discovery_runs` (
            run_id, run_timestamp, clients_processed, schemas_discovered,
            errors_encountered, processing_duration_seconds, status
        ) VALUES (
            @run_id, @timestamp, @clients, @discovered, @errors, @duration, @status
        )
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("run_id", "STRING", self.run_id),
                bigquery.ScalarQueryParameter("timestamp", "TIMESTAMP", datetime.now(timezone.utc)),
                bigquery.ScalarQueryParameter("clients", "INT64", clients),
                bigquery.ScalarQueryParameter("discovered", "INT64", discovered),
                bigquery.ScalarQueryParameter("errors", "INT64", errors),
                bigquery.ScalarQueryParameter("duration", "FLOAT64", duration),
                bigquery.ScalarQueryParameter("status", "STRING", status)
            ]
        )
        
        try:
            self.client.query(query, job_config=job_config).result()
            logger.info(f"Discovery run logged: {status}")
        except Exception as e:
            logger.error(f"Failed to log discovery run: {str(e)}")


def main():
    """Execute SCOUT schema discovery"""
    scout = ScoutSchemaDiscovery()
    
    # Run discovery
    results = scout.run_discovery()
    
    # Print summary
    print(f"\n🔍 SCOUT Schema Discovery Complete")
    print(f"Clients Processed: {results['clients_processed']}")
    print(f"Schemas Discovered: {results['schemas_discovered']}")
    print(f"Errors: {results['errors_encountered']}")
    print(f"Duration: {results['duration_seconds']:.1f} seconds")
    print(f"Status: {results['status']}")


if __name__ == "__main__":
    main()