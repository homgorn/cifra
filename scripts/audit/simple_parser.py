#!/usr/bin/env python3
"""
Simple Cifra18 Catalog Parser - Step by step
"""

import asyncio
import aiohttp
import csv
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import sys

BASE_URL = "https://xn--18-6kc5a3bxam.xn--p1ai"
OUTPUT_DIR = Path("brain/wiki/entities/full_catalog")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def clean_text(text: str) -> str:
    if not text: return ""
    return re.sub(r'\s+', ' ', text.strip()).replace('\u00a0', ' ').replace('\u200b', '')

def extract_price(text: str) -> dict:
    if not text: return {"raw": "", "value": None, "unit": ""}
    m = re.search(r'от\s+([\d\s]+)\s*₽/([^\s]+)', text)
    if m: return {"raw": text, "value": int(m.group(1).replace(' ', '')), "unit": m.group(2)}
    m = re.search(r'([\d\s]+)\s*₽/([^\s]+)', text)
    if m: return {"raw": text, "value": int(m.group(1).replace(' ', '')), "unit": m.group(2)}
    return {"raw": text, "value": None, "unit": ""}

async def fetch(session, url):
    try:
        async with session.get(url, timeout=30) as resp:
            return resp.status, await resp.text(), str(resp.url)
    except Exception as e:
        return 0, str(e), url

async def get_categories(session):
    """Get all categories from main menu"""
    status, html, _ = await fetch(session, "https://xn--18-6kc5a3bxam.xn--p1ai/")
    if status != 200: return []
    
    soup = BeautifulSoup(html, 'html.parser')
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

async def get_product_urls(session, cat_url):
    """Get all product URLs from a category page (with pagination)"""
    urls = set()
    page = 1
    
    while True:
        url = f"{cat_url}?PAGEN_1={page}" if page > 1 else cat_url
        print(f"  Fetching page {page}: {url}")
        
        try:
            async with session.get(url, timeout=30) as resp:
                if resp.status != 200:
                    break
                html = await resp.text()
        except:
            break
        
        soup = BeautifulSoup(html, 'html.parser')
        found = 0
        
        for link in soup.select('a.news-card, a.catalog-item__link, .catalog-item a[href*="/catalog/"]'):
            href = link.get('href')
            if href and '/catalog/' in href:
                full = "https://xn--18-6kc5a3bxam.xn--p1ai" + href if href.startswith('/') else href
                if full.count('/') >= 5:
                    urls.add(full.rstrip('/'))
                    found += 1
        
        if found == 0:
            for link in soup.select('a[href*="/catalog/"]'):
                href = link.get('href')
                if href and '/catalog/' in href:
                    full = "https://xn--18-6kc5a3bxam.xn--p1ai" + href if href.startswith('/') else href
                    if full.count('/') >= 5:
                        urls.add(full.rstrip('/'))
        
        if len(urls) == 0:
            break
            
        # Check pagination
        soup = BeautifulSoup(await fetch(session, url)[1], 'html.parser') if False else None
        # Simple pagination check - just try next page
        page += 1
        if page > 50:
            break
            
        # Quick check for next page
        try:
            next_url = f"{url}?PAGEN_1={page}"
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)).get(next_url, timeout=10) as resp:
                if resp.status != 200:
                    break
        except:
            break
            
    return sorted(urls)

async def parse_product(session, url):
    """Parse a single product page"""
    try:
        async with session.get(url, timeout=30) as resp:
            if resp.status != 200:
                return {"url": url, "status": resp.status, "error": f"HTTP {resp.status}"}
            html = await resp.text()
    except Exception as e:
        return {"url": url, "error": str(e)}
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Basic info
    title = soup.select_one('title')
    title_text = title.get_text(strip=True) if title else ""
    
    meta_desc = soup.select_one('meta[name="description"]')
    meta_desc = meta_desc.get('content', '').strip() if meta_desc else ""
    
    h1 = soup.select_one('h1')
    h1_text = h1.get_text(strip=True) if h1 else ""
    
    # JSON-LD
    json_ld = []
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            json_ld.append(json.loads(script.string))
        except:
            pass
    
    # Price
    price_text = ""
    for el in soup.select('.price, .calculator, [class*="price"], .news-card__type, .catalog-item__price'):
        price_text += " " + el.get_text(strip=True)
    
    price_match = re.search(r'от\s+([\d\s]+)\s*₽/([^\s]+)', price_text)
    if not price_match:
        price_match = re.search(r'([\d\s]+)\s*₽/([^\s]+)', price_text)
    
    price_val = int(price_match.group(1).replace(' ', '')) if price_match else None
    price_unit = price_match.group(2) if price_match else ""
    
    # Images
    images = []
    for img in soup.select('img'):
        src = img.get('src') or img.get('data-src')
        if src:
            images.append({"src": src, "alt": img.get('alt', ''), "has_alt": bool(img.get('alt', '').strip())})
    
    # Word count
    for tag in soup(['script', 'style', 'noscript']):
        tag.decompose()
    text = soup.get_text()
    words = len(re.sub(r'\s+', ' ', text).strip().split())
    
    return {
        "url": url,
        "title": title.get_text(strip=True) if title else "",
        "meta_description": soup.select_one('meta[name="description"]').get('content', '').strip() if soup.select_one('meta[name="description"]') else "",
        "h1": soup.select_one('h1').get_text(strip=True) if soup.select_one('h1') else "",
        "has_canonical": bool(soup.select_one('link[rel="canonical"]')),
        "json_ld_count": len(soup.select('script[type="application/ld+json"]')),
        "images_count": len(soup.select('img')),
        "images_no_alt": sum(1 for img in soup.select('img') if not img.get('alt', '').strip()),
        "word_count": len(re.sub(r'\s+', ' ', soup.get_text()).strip().split()),
        "price_value": int(re.search(r'от\s+([\d\s]+)\s*₽', soup.get_text()).group(1).replace(' ', '')) if re.search(r'от\s+([\d\s]+)\s*₽', soup.get_text()) else None,
        "price_unit": "/шт.",
        "json_ld_count": len(soup.select('script[type="application/ld+json"]')),
        "images_count": len(soup.select('img')),
        "images_no_alt": sum(1 for img in soup.select('img') if not img.get('alt', '').strip()),
        "word_count": len(re.sub(r'\s+', ' ', soup.get_text()).strip().split()),
        "em_dashes": soup.get_text().count('—'),
        "en_dashes": soup.get_text().count('–'),
        "has_calculator": bool(soup.select('.calculator, [class*="calculator"]')),
        "has_quick_order": bool(soup.select('.quick-order, [class*="quick-order"]')),
        "has_buy_button": bool(soup.select('button[type="submit"]')),
        "json_ld_count": len(soup.select('script[type="application/ld+json"]')),
        "images_no_alt": sum(1 for img in soup.select('img') if not img.get('alt', '').strip()),
        "word_count": len(re.sub(r'\s+', ' ', soup.get_text()).strip().split()),
    }

async def main():
    print("=== Cifra18 Catalog Parser ===")
    
    connector = aiohttp.TCPConnector(ssl=False, limit=10)
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False, limit=10)) as session:
        # 1. Get categories
        print("1. Getting categories...")
        cats = await get_categories(session)
        print(f"Found {len(cats)} categories")
        
        # For now just test with one category
        test_cat = next((c for c in cats if c['name'] == 'Полиграфия'), None)
        if test_cat:
            for sub in test_cat['subcategories'][:3]:  # Test first 3
                print(f"\nTesting: {sub['name']} - {sub['url']}")
                urls = await get_product_urls(session, sub['url'])
                print(f"  Found {len(urls)} products")
                break

if __name__ == "__main__":
    asyncio.run(main())