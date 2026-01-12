#!/usr/bin/env python3
"""Test Vertex AI Search connection and permissions."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.cloud import discoveryengine_v1 as discoveryengine
from google.auth import default


def main():
    print("=" * 60)
    print("Vertex AI Search Connection Test")
    print("=" * 60)
    print()

    # Check credentials
    print("[1/4] Checking credentials...")
    try:
        credentials, project = default()
        print(f"  Project: {project}")
        print(f"  Credentials type: {type(credentials).__name__}")
        if hasattr(credentials, 'service_account_email'):
            print(f"  Service account: {credentials.service_account_email}")

        # Check if using key file
        key_file = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        if key_file:
            print(f"  Using key file: {key_file}")
        else:
            print("  Using Application Default Credentials (ADC)")
    except Exception as e:
        print(f"  ERROR: {e}")
        return 1
    print()

    # Load settings
    print("[2/4] Loading app settings...")
    try:
        from src.config import get_settings
        settings = get_settings()
        print(f"  GCP Project: {settings.gcp_project_id}")
        print(f"  Data Store: {settings.vertex_search_data_store_id}")
        print(f"  Engine: {settings.vertex_search_engine_id}")
    except Exception as e:
        print(f"  ERROR loading settings: {e}")
        print("  Make sure .env is configured correctly")
        return 1
    print()

    # Build serving config path
    serving_config = (
        f"projects/{settings.gcp_project_id}/locations/global"
        f"/collections/default_collection"
        f"/engines/{settings.vertex_search_engine_id}"
        f"/servingConfigs/default_search"
    )
    print(f"[3/4] Serving config path:")
    print(f"  {serving_config}")
    print()

    # Test search
    print("[4/4] Testing search...")
    try:
        client = discoveryengine.SearchServiceClient()
        request = discoveryengine.SearchRequest(
            serving_config=serving_config,
            query="test",
            page_size=1,
        )
        response = client.search(request)
        print("  SUCCESS! Search API is working.")
        print(f"  Results returned: {len(list(response.results)) if response.results else 0}")
    except Exception as e:
        print(f"  ERROR: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Check IAM permissions for your credentials")
        print("  2. Verify the search engine exists in GCP Console")
        print("  3. Try: gcloud auth application-default login")
        print("  4. Or use service account key:")
        print("     export GOOGLE_APPLICATION_CREDENTIALS=./key.json")
        return 1

    print()
    print("=" * 60)
    print("All tests passed!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
