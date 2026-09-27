#!/usr/bin/env python3
"""
Topvisor API Export v2 — ежедневный pull позиций
"""

import os
import requests
import json
from datetime import datetime
from pathlib import Path

API_KEY = os.getenv("TOPVISOR_API_KEY")
PROJECT_ID = os.getenv("TOPVISOR_PROJECT_ID")
BASE_URL = "https://api.topvisor.com/v2/json"

def get_positions():
    params = {
        "project_id": PROJECT_ID,
        "fields": "keyword,position,position_prev,url,volume,top,serp_features",
        "limit": 1000
    }
    headers = {"Authorization": f"Bearer {API_KEY}"}
    resp = requests.post(f"https://api.topvisor.com/v2/json/getKeywords_2", json=params, headers={"Authorization": f"Bearer {API_KEY}"})
    return resp.json()

def main():
    print(f"=== ЦИФРА18 Topvisor Export ===")
    print(f"Started: {datetime.now()}")
    
    if not os.getenv("TOPVISOR_API_KEY") or not os.getenv("TOPVISOR_PROJECT_ID"):
        print("ERROR: TOPVISOR_API_KEY and TOPVISOR_PROJECT_ID must be set")
        return
    
    data = get_positions()
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    out_dir = Path("data/processed/monitoring/rankings")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    with open(out_dir / f"positions_{datetime.now().strftime('%Y-%m-%d')}.json", 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Positions saved: positions_{datetime.now().strftime('%Y-%m-%d')}.json")

if __name__ == "__main__":
    import os
    import requests
    import json
    from datetime import datetime
    from pathlib import Path
    
    if not os.getenv("TOPVISOR_API_KEY") or not os.getenv("TOPVISOR_PROJECT_ID"):
        print("Set TOPVISOR_API_KEY and TOPVISOR_PROJECT_ID env vars")
    else:
        data = requests.post(
            "https://api.topvisor.com/v2/json/getKeywords_2",
            json={"project_id": os.getenv("TOPVISOR_PROJECT_ID"), "fields": "keyword,position,position_prev,url,volume,top,serp_features", "limit": 1000},
            headers={"Authorization": f"Bearer {os.getenv('TOPVISOR_API_KEY')}"}
        ).json()
        
        out_dir = Path("data/processed/monitoring/rankings")
        out_dir.mkdir(parents=True, exist_ok=True)
        
        with open(out_dir / f"positions_{datetime.now().strftime('%Y-%m-%d')}.json", 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"Positions saved to data/processed/monitoring/rankings/")