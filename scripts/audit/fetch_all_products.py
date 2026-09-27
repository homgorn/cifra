#!/usr/bin/env python3
"""
Cifra18 Complete Catalog Scraper
Fetches ALL services from all 88 subcategories
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import csv
from datetime import datetime
from pathlib import Path

BASE_URL = "https://xn--18-6kc5a3bxam.xn--p1ai"
OUTPUT_DIR = Path("brain/wiki/entities/full_catalog")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

import urllib3
urllib3.disable_warnings()

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"})
SESSION.verify = False

import urllib3
urllib3.disable_warnings()

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
        categories = []
categories.append({"name": cat_name, "url": cat_url, "subcategories": subcats})
    return categories

def get_product_urls(cat_url):
    urls = set()
    for page in range(1, 6):
        url = f"{cat_url}?PAGEN_1={page}" if page > 1 else cat_url
        resp = requests.get(url, verify=False, timeout=15)
        if resp.status_code != 200: break
        soup = BeautifulSoup(resp.text, 'html.parser')
        for link in soup.select('a.news-card, a.catalog-item__link, .catalog-item a[href*="/catalog/"]'):
            href = link.get('href')
            if href and '/catalog/' in href:
                full = "https://xn--18-6kc5a3bxam.xn--p1ai" + href if href.startswith('/') else href
                if full.count('/') >= 5:
                    urls.add(full.rstrip('/'))
        # Check if next page has different content
        soup = BeautifulSoup(requests.get(f"{cat_url}?PAGEN_1={page+1}", verify=False, timeout=10).text, 'html.parser')
        if not soup.select('a.news-card, a.catalog-item__link, .catalog-item a[href*="/catalog/"]'):
            break
    return sorted(urls)

def parse_product(url):
    resp = requests.get(url, verify=False, timeout=20)
    if resp.status_code != 200:
        return {"url": url, "error": f"HTTP {resp.status_code}"}
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    title = soup.select_one('title')
    title_text = title.get_text(strip=True) if title else ""
    meta_desc = soup.select_one('meta[name="description"]').get('content', '') if soup.select_one('meta[name="description"]') else ""
    h1_texts = [h.get_text(strip=True) for h in soup.select('h1')]
    
    price_text = ""
    for el in soup.select('.price, .calculator, [class*="price"], .news-card__type, .catalog-item__price'):
        price_text += " " + el.get_text(strip=True)
    m = re.search(r'от\s+([\d\s]+)\s*₽/([^\s]+)', price_text) or re.search(r'([\d\s]+)\s*₽/([^\s]+)', price_text)
    price = {"value": int(m.group(1).replace(' ', '')) if m else None, "unit": m.group(2) if m else ""}
    
    text = BeautifulSoup(requests.get(url, verify=False, timeout=10).text, 'html.parser').get_text()
    words = len(re.sub(r'\s+', ' ', soup.get_text()).strip().split())
    
    return {
        "url": url, "title": soup.select_one('title').get_text(strip=True) if soup.select_one('title') else "",
        "meta_description": soup.select_one('meta[name="description"]').get('content', '') if soup.select_one('meta[name="description"]') else "",
        "h1": " | ".join([h.get_text(strip=True) for h in BeautifulSoup(requests.get(url, verify=False).text, 'html.parser').select('h1')]),
        "price_value": int(re.search(r'от\s+([\d\s]+)\s*₽', soup.get_text()).group(1).replace(' ', '')) if re.search(r'от\s+([\d\s]+)\s*₽', soup.get_text()) else None,
        "word_count": len(re.sub(r'\s+', ' ', BeautifulSoup(requests.get(url, verify=False).text, 'html.parser').get_text()).strip().split()),
        "json_ld": len(BeautifulSoup(requests.get(url, verify=False).text, 'html.parser').select('script[type="application/ld+json"]')),
    }

def main():
    import urllib3; urllib3.disable_warnings()
    cats = []
    resp = requests.get("https://xn--18-6kc5a3bxam.xn--p1ai/", verify=False, timeout=30)
    soup = BeautifulSoup(resp.text, 'html.parser')
    for nav in soup.select('nav.js-production-group'):
        title = nav.select_one('a.menu__list-title')
        if not title: continue
        cat_name = title.get_text(strip=True)
        cat_url = "https://xn--18-6kc5a3bxam.xn--p1ai" + title.get('href', '')
        subcats = []
        for ol in soup.select('ol.menu__list-grid, ol.menu__list-column'):
            for li in ol.select('li a'):
                subcats.append({"name": li.get_text(strip=True), "url": "https://xn--18-6kc5a3bxam.xn--p1ai" + li.get('href', '')})
        categories = []
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
            r = requests.get(url, verify=False, timeout=10)
            if r.status_code != 200: break
            s = BeautifulSoup(r.text, 'html.parser')
            for link in s.select('a.news-card, a.catalog-item__link, .catalog-item a[href*="/catalog/"]'):
                href = link.get('href')
                if href and '/catalog/' in href:
                    full = "https://xn--18-6kc5a3bxam.xn--p1ai" + href if href.startswith('/') else href
                    if full.count('/') >= 5:
                        urls.add(full.rstrip('/'))
        all_urls[subcat['cat'] + " > " + subcat['name']] = sorted(urls)
        print(f"{subcat['cat']} > {subcat['name']}: {len(urls)} products")
    
    # Save
    date_str = datetime.now().strftime("%Y-%m-%d")
    with open(f"brain/wiki/entities/full_catalog/catalog_urls_{datetime.now().strftime('%Y-%m-%d')}.json", 'w') as f:
        json.dump({"parsed_at": datetime.now().isoformat(), "urls_by_category": {k: list(v) for k, v in all_urls.items()}}, f, ensure_ascii=False, indent=2)
    
    print("Done! URLs saved.")

if __name__ == "__main__":
    main()