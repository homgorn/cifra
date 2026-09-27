#!/usr/bin/env python3
"""
Cifra18 Complete Catalog Scraper - Fetches all products from all subcategories
"""

import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime
from pathlib import Path
import urllib3

urllib3.disable_warnings()

BASE_URL = "https://xn--18-6kc5a3bxam.xn--p1ai"
OUTPUT_DIR = Path("brain/wiki/entities/full_catalog")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"})
SESSION.verify = False

def clean_text(text: str) -> str:
    if not text: return ""
    return re.sub(r'\s+', ' ', text.strip()).replace('\u00a0', ' ').replace('\u200b', '')

def fetch(url):
    try:
        resp = requests.get(url, verify=False, timeout=15)
        return resp.status_code, resp.text, resp.url
    except Exception as e:
        return 0, str(e), url

def get_all_categories():
    resp = requests.get("https://xn--18-6kc5a3bxam.xn--p1ai/", verify=False, timeout=30)
    soup = BeautifulSoup(resp.text, 'html.parser')
    categories = []
    for nav in soup.select('nav.js-production-group'):
        title = nav.select_one('a.menu__list-title')
        if not title: continue
        cat_name = title.get_text(strip=True)
        cat_url = "https://xn--18-6kc5a3bxam.xn--p1ai" + title.get('href', '')
        subcats = []
        for ol in nav.select('ol.menu__list-grid, ol.menu__list-column'):
            for li in ol.select('li a'):
                subcats.append({
                    "name": li.get_text(strip=True),
                    "url": "https://xn--18-6kc5a3bxam.xn--p1ai" + li.get('href', '')
                })
        categories.append({"name": cat_name, "url": cat_url, "subcategories": subcats})
    return categories

def get_product_urls(cat_url):
    urls = set()
    for page in range(1, 6):
        url = f"{cat_url}?PAGEN_1={page}" if page > 1 else cat_url
        resp = requests.get(url, verify=False, timeout=15)
        if resp.status_code != 200: break
        soup = BeautifulSoup(resp.text, 'html.parser')
        found = 0
        for link in soup.select('a.news-card, a.catalog-item__link, .catalog-item a[href*="/catalog/"]'):
            href = link.get('href')
            if href and '/catalog/' in href:
                full = "https://xn--18-6kc5a3bxam.xn--p1ai" + href if href.startswith('/') else href
                if full.count('/') >= 5:
                    urls.add(full.rstrip('/'))
                    found += 1
        if found == 0:
            break
    return sorted(urls)

def main():
    import urllib3
    urllib3.disable_warnings()
    
    # Get categories
    resp = requests.get("https://xn--18-6kc5a3bxam.xn--p1ai/", verify=False, timeout=30)
    soup = BeautifulSoup(resp.text, 'html.parser')
    categories = []
    for nav in soup.select('nav.js-production-group'):
        title = soup.select_one('a.menu__list-title')
        if not title: continue
        cat_name = title.get_text(strip=True)
        cat_url = "https://xn--18-6kc5a3bxam.xn--p1ai" + title.get('href', '')
        subcats = []
        for ol in soup.select('ol.menu__list-grid, ol.menu__list-column'):
            for li in ol.select('li a'):
                subcats.append({
                    "name": li.get_text(strip=True),
                    "url": "https://xn--18-6kc5a3bxam.xn--p1ai" + li.get('href', '')
                })
        categories.append({"name": cat_name, "url": cat_url, "subcategories": subcats})
    
    # Build all subcats
    all_subcats = []
    for cat in categories:
        for sub in cat["subcategories"]:
            all_subcats.append({"cat": cat["name"], "name": sub["name"], "url": sub["url"]})
    
    print(f"Total subcategories: {len(all_subcats)}")
    
    OUTPUT_DIR = Path("brain/wiki/entities/full_catalog")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Get all URLs
    all_urls = {}
    for subcat in all_subcats:
        urls = set()
        for page in range(1, 6):
            url = f"{subcat['url']}?PAGEN_1={page}" if page > 1 else subcat['url']
            r = requests.get(url, verify=False, timeout=15)
            if r.status_code != 200: break
            s = BeautifulSoup(r.text, 'html.parser')
            found = 0
            for link in s.select('a.news-card, a.catalog-item__link, .catalog-item a[href*="/catalog/"]'):
                href = link.get('href')
                if href and '/catalog/' in href:
                    full = "https://xn--18-6kc5a3bxam.xn--p1ai" + href if href.startswith('/') else href
                    if full.count('/') >= 5:
                        urls.add(full.rstrip('/'))
                        found += 1
            if found == 0:
                break
        all_urls[subcat['cat'] + " > " + subcat['name']] = sorted(urls)
        print(f"{subcat['cat']} > {subcat['name']}: {len(urls)} products")
    
    # Save
    date_str = datetime.now().strftime("%Y-%m-%d")
    with open(f"brain/wiki/entities/full_catalog/catalog_urls_{datetime.now().strftime('%Y-%m-%d')}.json", 'w') as f:
        json.dump({"parsed_at": datetime.now().isoformat(), "urls_by_category": {k: list(v) for k, v in all_urls.items()}}, f, ensure_ascii=False, indent=2)
    
    print("Done! URLs saved.")

if __name__ == "__main__":
    main()