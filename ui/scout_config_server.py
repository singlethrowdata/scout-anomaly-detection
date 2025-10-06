import json
import os
import sys

# [FIX]: Add project root to Python path for script imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, jsonify, send_from_directory
import threading
import pandas as pd

# Try to import scripts, but gracefully handle if missing
try:
    from scripts.scout_client_discovery import discover_all_properties
except ImportError:
    discover_all_properties = None

app = Flask(__name__, static_folder='dist')

# [FIX]: Manual CORS handling instead of flask-cors
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

discovery_status = {
    'running': False,
    'progress': 0,
    'total': 0,
    'message': 'Discovery not started.',
}

@app.route('/api/discovery/start', methods=['POST'])
def start_discovery_route():
    if not discover_all_properties:
        return jsonify({'message': 'Discovery module not available'}), 503

    if discovery_status['running']:
        return jsonify({'message': 'Discovery already in progress.'}), 400

    def run_discovery():
        global discovery_status
        discovery_status = {
            'running': True,
            'progress': 0,
            'total': 0,
            'message': 'Starting discovery...',
        }

        try:
            discover_all_properties(update_status=update_discovery_status)
            discovery_status['message'] = 'Discovery completed.'
        except Exception as e:
            discovery_status['message'] = f'Error during discovery: {e}'
        finally:
            discovery_status['running'] = False

    def update_discovery_status(progress, total, message):
        global discovery_status
        discovery_status['progress'] = progress
        discovery_status['total'] = total
        discovery_status['message'] = message

    thread = threading.Thread(target=run_discovery)
    thread.start()

    return jsonify({'message': 'Discovery process started.'})

@app.route('/api/discovery/status')
def get_discovery_status():
    return jsonify(discovery_status)

@app.route('/api/config')
def get_config():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'scout_client_config.csv')
    if not os.path.exists(config_path):
        return jsonify([])
    df = pd.read_csv(config_path)
    return jsonify(json.loads(df.to_json(orient='records')))

@app.route('/api/properties')
def get_properties():
    """Merge available properties with client config data to show domains"""
    # Load available properties
    properties_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'scout_available_properties.json')
    config_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'scout_client_config.csv')

    if not os.path.exists(properties_path):
        return jsonify([])

    with open(properties_path, 'r') as f:
        properties = json.load(f)

    # Load config if exists
    config_map = {}
    if os.path.exists(config_path):
        df = pd.read_csv(config_path)
        config_map = {str(row['property_id']): row.to_dict() for _, row in df.iterrows()}

    # Merge data
    merged = []
    for prop in properties:
        prop_id = str(prop['property_id'])
        config = config_map.get(prop_id, {})

        merged.append({
            'property_id': prop['property_id'],
            'dataset_id': prop['dataset_id'],
            'client_name': config.get('client_name'),
            'domain': config.get('domain'),
            'conversion_events': config.get('conversion_events'),
            'notes': config.get('notes'),
            'is_configured': prop_id in config_map
        })

    return jsonify(merged)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    print("🔵 SCOUT Config Server starting on http://localhost:5000")
    print("📊 Serving API at /api/*")
    app.run(use_reloader=False, port=5000, threaded=True)

