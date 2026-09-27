#!/usr/bin/env python3
"""
CRM Export — Битрикс24 / amoCRM (лиды, сделки, ROI)
"""

import os
import requests
import json
from datetime import datetime, timedelta
from pathlib import Path

BITRIX24_WEBHOOK = os.getenv("BITRIX24_WEBHOOK")  # https://domain.bitrix24.ru/rest/user_id/webhook_code/

def bx_call(method, params=None):
    url = f"{BITRIX24_WEBHOOK}/{method}.json"
    resp = requests.post(url, json=params or {}, timeout=30)
    resp.raise_for_status()
    return resp.json().get('result', [])

def export_leads():
    return bx_call('crm.lead.list', {
        'filter': {'DATE_CREATE': {'>=': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')}},
        'select': ['ID', 'TITLE', 'STATUS_ID', 'OPPORTUNITY', 'CURRENCY_ID', 'DATE_CREATE', 'ASSIGNED_BY_ID', 'SOURCE_ID', 'UTM_SOURCE', 'UTM_MEDIUM', 'UTM_CAMPAIGN', 'UTM_CONTENT', 'UTM_TERM']
    })

def export_deals():
    return bx_call('crm.deal.list', {
        'filter': {'DATE_CREATE': {'>=': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')}},
        'select': ['ID', 'TITLE', 'STAGE_ID', 'OPPORTUNITY', 'CURRENCY_ID', 'DATE_CREATE', 'CLOSEDATE', 'ASSIGNED_BY_ID', 'CONTACT_ID', 'COMPANY_ID', 'UTM_SOURCE', 'UTM_MEDIUM', 'UTM_CAMPAIGN', 'UTM_CONTENT', 'UTM_TERM']
    })

def export_utm_attribution():
    deals = export_deals()
    leads = export_leads()
    
    # Атрибуция по UTM
    attribution = {}
    for deal in deals:
        source = deal.get('UTM_SOURCE', 'direct')
        medium = deal.get('UTM_MEDIUM', 'none')
        campaign = deal.get('UTM_CAMPAIGN', 'none')
        key = f"{source}/{medium}/{campaign}"
        if key not in attribution:
            attribution[key] = {'deals': 0, 'revenue': 0}
        attribution[key]['deals'] += 1
        attribution[key]['revenue'] += float(deal.get('OPPORTUNITY', 0))
    
    return attribution

def export_roi_by_channel():
    attribution = export_utm_attribution()
    roi_data = []
    for channel, data in attribution.items():
        roi_data.append({
            'channel': channel,
            'deals': data['deals'],
            'revenue': data['revenue'],
            'avg_deal': data['revenue'] / data['deals'] if data['deals'] > 0 else 0
        })
    return roi_data

def main():
    if not os.getenv("BITRIX24_WEBHOOK"):
        print("BITRIX24_WEBHOOK not set")
        return
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    out_dir = Path(f"data/exports/crm/{datetime.now().strftime('%Y-%m-%d')}")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print("Exporting leads...")
    leads = export_leads()
    with open(f"data/exports/crm/{datetime.now().strftime('%Y-%m-%d')}/leads.json", 'w') as f:
        json.dump(leads, f, ensure_ascii=False, indent=2)
    
    print("Exporting deals...")
    deals = export_deals()
    with open(f"data/exports/crm/{datetime.now().strftime('%Y-%m-%d')}/deals.json", 'w') as f:
        json.dump(deals, f, ensure_ascii=False, indent=2)
    
    print("Exporting UTM attribution...")
    utm = export_utm_attribution()
    with open(f"data/exports/crm/{datetime.now().strftime('%Y-%m-%d')}/utm_attribution.json", 'w') as f:
        json.dump(utm, f, ensure_ascii=False, indent=2)
    
    print("Exporting ROI by channel...")
    roi = export_roi_by_channel()
    with open(f"data/exports/crm/{datetime.now().strftime('%Y-%m-%d')}/roi_by_channel.json", 'w') as f:
        json.dump(roi, f, ensure_ascii=False, indent=2)
    
    print("CRM export completed!")

if __name__ == "__main__":
    import os
    import requests
    import json
    from datetime import datetime, timedelta
    from pathlib import Path
    
    if not os.getenv("BITRIX24_WEBHOOK"):
        print("Set BITRIX24_WEBHOOK env var")
    else:
        import requests
        from datetime import datetime, timedelta
        main()