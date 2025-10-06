#!/usr/bin/env python3
"""
SCOUT Client Discovery Runner
Discovers all 72+ GA4 properties and generates review files
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scout_client_discovery import run_client_discovery

if __name__ == "__main__":
    try:
        print("🔍 SCOUT Client Discovery Starting...")
        json_report, csv_review = run_client_discovery()
        print(f"\n✅ Success! Review files created:")
        print(f"   📄 JSON Report: {json_report}")
        print(f"   📊 CSV Review: {csv_review}")

    except Exception as e:
        print(f"❌ Error during discovery: {str(e)}")
        sys.exit(1)
