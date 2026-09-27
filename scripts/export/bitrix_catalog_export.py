#!/usr/bin/env python3
"""
Bitrix Catalog Export — экспорт каталога, статей, SEO шаблонов
"""

import os
import requests
import json
import csv
from datetime import datetime
from pathlib import Path

BITRIX_WEBHOOK = os.getenv("BITRIX_WEBHOOK")  # https://domain.bitrix24.ru/rest/user_id/webhook_code/
OUTPUT_DIR = Path("data/exports/bitrix")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def bitrix_call(method, params=None):
    url = f"{BITRIX_WEBHOOK}/{method}.json"
    resp = requests.post(url, json=params or {}, timeout=30)
    resp.raise_for_status()
    return resp.json().get('result', [])

def export_catalog():
    """Экспорт всего каталога"""
    # Get all sections
    sections = bitrix_call('catalog.section.list', {'filter': {'ACTIVE': 'Y'}})
    
    all_products = []
    for section in sections:
        products = bitrix_call('catalog.product.list', {
            'filter': {'SECTION_ID': section['ID'], 'ACTIVE': 'Y'},
            'select': ['ID', 'NAME', 'DETAIL_PAGE_URL', 'PRICE', 'CURRENCY', 'PROPERTY_*', 'PREVIEW_TEXT', 'DETAIL_TEXT', 'DETAIL_PICTURE', 'PREVIEW_PICTURE']
        })
        for p in products:
            p['SECTION_NAME'] = p.get('IBLOCK_SECTION_NAME', '')
        all_products.extend(products)
    
    return all_products

def export_articles():
    """Экспорт статей из инфоблока новостей"""
    articles = bitrix_call('iblock.element.getlist', {
        'IBLOCK_ID': 2,  # ID инфоблока новостей
        'FILTER': {'ACTIVE': 'Y'},
        'SELECT': ['ID', 'NAME', 'DETAIL_PAGE_URL', 'PREVIEW_TEXT', 'DETAIL_TEXT', 'DATE_CREATE', 'CREATED_BY', 'PROPERTY_*', 'DETAIL_PICTURE', 'PREVIEW_PICTURE']
    })
    return articles

def export_seo_templates():
    """Экспорт SEO шаблонов из настроек инфоблоков"""
    pass

def save_json(data, filename):
    path = Path("data/exports/bitrix") / f"{filename}_{datetime.now().strftime('%Y-%m-%d')}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    if not os.getenv("BITRIX_WEBHOOK"):
        print("ERROR: BITRIX_WEBHOOK not set")
        return
    
    print("=== Bitrix Catalog Export ===")
    
    print("Exporting catalog...")
    catalog = export_catalog()
    save_json(catalog, f"catalog_full_{datetime.now().strftime('%Y-%m-%d')}")
    print(f"Exported {len(catalog)} products")
    
    print("Exporting articles...")
    articles = export_articles()
    save_json(articles, f"articles_{datetime.now().strftime('%Y-%m-%d')}")
    print(f"Exported {len(articles)} articles")
    
    print("Done!")

if __name__ == "__main__":
    import os
    if not os.getenv("BITRIX_WEBHOOK"):
        print("Set BITRIX_WEBHOOK env var")
    else:
        import requests
        import json
        from datetime import datetime
        from pathlib import Path
        main()