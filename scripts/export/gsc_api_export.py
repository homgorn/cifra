#!/usr/bin/env python3
"""
GSC API Export — Google Search Console
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']
SERVICE_ACCOUNT_FILE = os.getenv("GSC_SERVICE_ACCOUNT_JSON")
PROPERTY_URL = os.getenv("GSC_PROPERTY_URL", "https://xn--18-6kc5a3bxam.xn--p1ai/")

def get_gsc_service():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('webmasters', 'v3', credentials=credentials)

def export_search_analytics():
    service = get_gsc_service()
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=90)
    
    request = {
        'startDate': (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'),
        'endDate': datetime.now().strftime('%Y-%m-%d'),
        'dimensions': ['query', 'page', 'device', 'country'],
        'rowLimit': 25000
    }
    
    response = service.searchanalytics().query(
        siteUrl='https://xn--18-6kc5a3bxam.xn--p1ai/',
        body=request
    ).execute()
    
    return response.get('rows', [])

def main():
    if not os.getenv("GSC_SERVICE_ACCOUNT_JSON"):
        print("GSC_SERVICE_ACCOUNT_JSON not set")
        return
    
    data = export_search_analytics()
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    Path("data/exports/gsc").mkdir(parents=True, exist_ok=True)
    with open(f"data/exports/gsc/{datetime.now().strftime('%Y-%m-%d')}/search_analytics.json", 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("GSC export completed")

if __name__ == "__main__":
    import os
    if not os.getenv("GSC_SERVICE_ACCOUNT_JSON"):
        print("GSC_SERVICE_ACCOUNT_JSON not set")
    else:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        import json
        from datetime import datetime
        from pathlib import Path
        main()