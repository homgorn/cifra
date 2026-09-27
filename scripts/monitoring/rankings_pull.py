#!/usr/bin/env python3
"""
Daily Rankings Pull из Топвизор API v2
Сохраняет историю позиций для трендов
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
    resp = requests.post(f"{BASE_URL}/getKeywords_2", json=params, headers=headers)
    return resp.json()

def main():
    print(f"=== ЦИФРА18 Rankings Pull ===")
    print(f"Started: {datetime.now()}")
    
    if not API_KEY or not PROJECT_ID:
        print("ERROR: TOPVISOR_API_KEY and TOPVISOR_PROJECT_ID must be set")
        return
    
    data = get_positions()
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    out_dir = Path("data/processed/monitoring/rankings")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    with open(out_dir / f"positions_{date_str}.json", 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Positions saved: {out_dir / f'positions_{date_str}.json'}")
    print(f"Completed: {datetime.now()}")

if __name__ == "__main__":
    main()