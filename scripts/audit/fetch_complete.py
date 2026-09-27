#!/usr/bin/env python3
"""
Cifra18 Complete Catalog Fetcher
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

import urllib3; urllib3.disable_warnings()

def get_all_subcats():
    resp = requests.get("https://xn--18-6kc5a3bxam.xn--p1ai/", verify=False, timeout=30)
    soup = BeautifulSoup(resp.text, 'html.parser')
    subcats = []
    for nav in soup.select('nav.js-production-group'):
        title = nav.select_one('a.menu__list-title')
        if not title: continue
        cat_name = title.get_text(strip=True)
        cat_url = "https://xn--18-6kc5a3bxam.xn--p1ai" + title.get('href', '')
        for ol in soup.select('ol.menu__list-grid, ol.menu__list-column'):
            for li in ol.select('li a'):
                all_subcats.append({
                    "cat": cat_name,
                    "name": li.get_text(strip=True),
                    "url": "https://xn--18-6kc5a3bxam.xn--p1ai" + li.get('href', '')
                })
    return all_subcats

def get_urls(cat_url):
    urls = set()
    for page in range(1, 6):
        url = f"{cat_url}?PAGEN_1={page}" if page > 1 else cat_url
        r = requests.get(url, verify=False, timeout=15)
        if r.status_code != 200: break
        s = BeautifulSoup(r.text, 'html.parser')
        for link in s.select('a.news-card, a.catalog-item__link, .catalog-item a[href*="/catalog/"]'):
            href = link.get('href')
            if href and '/catalog/' in href:
                full = "https://xn--18-6kc5a3bxam.xn--p1ai" + href if href.startswith('/') else href
                if full.count('/') >= 5:
                    urls.add(full.rstrip('/'))
        if len(urls) == 0 and page > 1: break
    return sorted(urls)

def main():
    import urllib3; urllib3.disable_warnings()
    cats = []
    resp = requests.get("https://xn--18-6kc5a3bxam.xn--p1ai/", verify=False, timeout=30)
    soup = BeautifulSoup(resp.text, 'html.parser')
    cats = []
    for nav in BeautifulSoup(resp.text, 'html.parser').select('nav.js-production-group'):
        title = nav.select_one('a.menu__list-title')
        if not title: continue
        cat_name = title.get_text(strip=True)
        cat_url = "https://xn--18-6kc5a3bxam.xn--p1ai" + title.get('href', '')
        subcats = []
        for ol in nav.select('ol.menu__list-grid, ol.menu__list-column'):
            for li in ol.select('li a'):
                subcats.append({'name': li.get_text(strip=True), 'url': 'https://xn--18-6kc5a3bxam.xn--p1ai' + li.get('href', '')})
        cats.append({"name": cat_name, "url": cat_url, "subcategories": subcats})
    
    all_subcats = []
    for cat in cats:
        for sub in cat["subcategories"]:
            all_subcats.append({"cat": cat["name"], "name": sub["name"], "url": sub["url"]})
    
    print(f"Total subcategories: {len(all_subcats)}")
    
    OUTPUT_DIR = Path("brain/wiki/entities/full_catalog")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
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
            if len(urls) == 0 and page > 1: break
        all_urls[subcat['cat'] + " > " + subcat['name']] = sorted(urls)
        print(f"{subcat['cat']} > {subcat['name']}: {len(urls)} products")
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    with open(f"brain/wiki/entities/full_catalog/catalog_urls_{datetime.now().strftime('%Y-%m-%d')}.json", 'w') as f:
        json.dump({"parsed_at": datetime.now().isoformat(), "urls_by_category": {k: list(v) for k, v in all_urls.items()}}, f, ensure_ascii=False, indent=2)
    
    print("Done! URLs saved.")

if __name__ == "__main__":
    main()