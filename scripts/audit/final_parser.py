#!/usr/bin/env python3
"""
Cifra18 Catalog Parser - Complete parser for all products
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
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            html = await resp.text()
            return resp.status, html, str(resp.url)
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

async def get_product_urls(session, cat_url, max_pages=20):
    """Get all product URLs from a category page (with pagination)"""
    urls = set()
    
    for page in range(1, max_pages + 1):
        url = f"{cat_url}?PAGEN_1={page}" if page > 1 else cat_url
        print(f"  Page {page}: {url}")
        
        status, html, _ = await fetch(session, url)
        if status != 200:
            print(f"  Page {page} failed: {status}")
            break
        
        soup = BeautifulSoup(html, 'html.parser')
        found = 0
        
        # Primary selectors for product cards
        for link in soup.select('a.news-card, a.catalog-item__link, .catalog-item a[href*="/catalog/"]'):
            href = link.get('href')
            if href and '/catalog/' in href:
                full = "https://xn--18-6kc5a3bxam.xn--p1ai" + href if href.startswith('/') else href
                if full.count('/') >= 5:
                    urls.add(full.rstrip('/'))
        
        # Fallback
        if len(urls) == 0:
            for link in soup.select('a[href*="/catalog/"]'):
                href = link.get('href')
                if href and '/catalog/' in href:
                    full = "https://xn--18-6kc5a3bxam.xn--p1ai" + href if href.startswith('/') else href
                    if full.count('/') >= 5:
                        urls.add(full.rstrip('/'))
        
        # Check if we got new URLs on this page
        new_count = len(urls)
        if len(urls) == 0 and page > 1:
            break
            
        # Check for next page link
        soup = BeautifulSoup(html, 'html.parser')
        next_link = soup.select_one('.pagination .next:not(.disabled), .pagen .next:not(.disabled), a[rel="next"]')
        if not next_link:
            break
            
    return sorted(urls)

async def parse_product(session, url):
    """Parse a single product page"""
    status, html, _ = await fetch(session, url)
    if status != 200:
        return {"url": url, "status": status, "error": f"HTTP {status}"}
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Basic SEO
    title = soup.select_one('title')
    title_text = title.get_text(strip=True) if title else ""
    
    meta_desc_tag = soup.select_one('meta[name="description"]')
    meta_desc = meta_desc_tag.get('content', '').strip() if meta_desc_tag else ""
    
    meta_kw_tag = soup.select_one('meta[name="keywords"]')
    meta_kw = meta_kw_tag.get('content', '').strip() if meta_kw_tag else ""
    
    # H1
    h1_tags = soup.select('h1')
    h1_texts = [h.get_text(strip=True) for h in h1_tags]
    
    # Canonical
    canonical = soup.select_one('link[rel="canonical"]')
    canonical = canonical.get('href') if canonical else None
    
    # JSON-LD
    json_ld_count = len(soup.select('script[type="application/ld+json"]'))
    
    # Open Graph
    og = {}
    for meta in soup.select('meta[property^="og:"]'):
        og[meta.get('property')] = meta.get('content')
    
    # Breadcrumbs
    breadcrumbs = []
    for el in soup.select('.bx-breadcrumb-item a, .breadcrumb a, [class*="breadcrumb"] a'):
        breadcrumbs.append({"text": el.get_text(strip=True), "url": "https://xn--18-6kc5a3bxam.xn--p1ai" + el.get('href', '')})
    
    # Price
    price_text = ""
    for el in soup.select('.price, .calculator, [class*="price"], .news-card__type, .catalog-item__price'):
        price_text += " " + el.get_text(strip=True)
    
    price_info = {"raw": price_text, "value": None, "unit": ""}
    m = re.search(r'от\s+([\d\s]+)\s*₽/([^\s]+)', price_text)
    if m:
        price_info = {"raw": price_text, "value": int(m.group(1).replace(' ', '')), "unit": m.group(2)}
    else:
        m = re.search(r'([\d\s]+)\s*₽/([^\s]+)', price_text)
        if m:
            price_info = {"raw": price_text, "value": int(m.group(1).replace(' ', '')), "unit": m.group(2)}
    
    # Images
    images = []
    for img in soup.select('img'):
        src = img.get('src') or img.get('data-src')
        if src:
            images.append({"src": src, "alt": img.get('alt', ''), "has_alt": bool(img.get('alt', '').strip())})
    
    # Text content
    for tag in soup(['script', 'style', 'noscript']):
        tag.decompose()
    text = soup.get_text()
    words = len(re.sub(r'\s+', ' ', text).strip().split())
    
    # Calculator/Order forms
    has_calculator = bool(soup.select('.calculator, [class*="calculator"]'))
    has_quick_order = bool(soup.select('.quick-order, [class*="quick-order"]'))
    has_buy_button = bool(soup.select('button[type="submit"], .buy-btn'))
    
    # Properties
    properties = {}
    for prop_block in soup.select('.properties, .props, [class*="prop"]'):
        for row in prop_block.select('tr, .row'):
            cells = row.select('td, .name, .value')
            if len(cells) >= 2:
                properties[clean_text(cells[0].get_text())] = clean_text(cells[1].get_text())
    
    return {
        "url": url,
        "title": soup.select_one('title').get_text(strip=True) if soup.select_one('title') else "",
        "title_len": len(soup.select_one('title').get_text(strip=True)) if soup.select_one('title') else 0,
        "meta_description": meta_desc,
        "meta_desc_len": len(meta_desc),
        "meta_keywords": meta_kw,
        "h1_count": len(soup.select('h1')),
        "h1_texts": " | ".join([h.get_text(strip=True) for h in soup.select('h1')]),
        "canonical": canonical,
        "has_canonical": canonical is not None,
        "json_ld_count": len(soup.select('script[type="application/ld+json"]')),
        "og_title": og.get('og:title', ''),
        "og_description": og.get('og:description', ''),
        "og_image": og.get('og:image', ''),
        "images_count": len(soup.select('img')),
        "images_no_alt": sum(1 for img in soup.select('img') if not img.get('alt', '').strip()),
        "word_count": len(re.sub(r'\s+', ' ', soup.get_text()).strip().split()),
        "em_dashes": soup.get_text().count('—'),
        "en_dashes": soup.get_text().count('–'),
        "price_raw": extract_price(soup.get_text())['raw'],
        "price_value": extract_price(soup.get_text())['value'],
        "price_unit": extract_price(soup.get_text())['unit'],
        "breadcrumbs": breadcrumbs,
        "has_calculator": bool(soup.select('.calculator, [class*="calculator"]')),
        "has_quick_order": bool(soup.select('.quick-order, [class*="quick-order"]')),
        "has_buy_button": bool(soup.select('button[type="submit"], .buy-btn')),
        "images_count": len(soup.select('img')),
        "images_no_alt": sum(1 for img in soup.select('img') if not img.get('alt', '').strip()),
        "word_count": len(re.sub(r'\s+', ' ', BeautifulSoup(html, 'html.parser').get_text()).strip().split()),
        "em_dashes": soup.get_text().count('—'),
        "en_dashes": soup.get_text().count('–'),
        "has_calculator": bool(soup.select('.calculator, [class*="calculator"]')),
        "has_quick_order": bool(soup.select('.quick-order, [class*="quick-order"]')),
        "has_buy_button": bool(soup.select('button[type="submit"], .buy-btn')),
        "json_ld_count": len(soup.select('script[type="application/ld+json"]')),
        "images_no_alt": sum(1 for img in soup.select('img') if not img.get('alt', '').strip()),
    }

async def main():
    print("=== Cifra18 Catalog Parser ===")
    
    connector = aiohttp.TCPConnector(ssl=False, limit=10)
    timeout = aiohttp.ClientTimeout(total=60)
    
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False, limit=10), timeout=aiohttp.ClientTimeout(total=60)) as session:
        # 1. Get categories
        print("1. Getting categories...")
        cats = await get_categories(session)
        print(f"Found {len(cats)} main categories")
        
        # Build all category list
        all_cats = []
        for cat in cats:
            all_cats.append({"name": cat["name"], "url": cat["url"], "parent": None})
            for sub in cat["subcategories"]:
                all_cats.append({"name": f"{cat['name']} > {sub['name']}", "url": sub["url"], "parent": cat["name"]})
        
        print(f"Total categories to parse: {len(all_cats)}")
        
        # Parse products for each category
        all_products = {}
        total = 0
        
        for i, cat in enumerate(all_cats):
            print(f"[{i+1}/{len(all_cats)}] {cat['name']}...")
            urls = await get_product_urls(session, cat['url'], max_pages=10)
            all_products[cat['name']] = urls
            print(f"  Found {len(urls)} products")
        
        total = sum(len(v) for v in all_products.values())
        print(f"\nTotal products: {sum(len(v) for v in all_products.values())}")
        
        # Save results
        date_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
        
        # Save JSON
        json_path = OUTPUT_DIR / f"catalog_urls_{datetime.now().strftime('%Y-%m-%d')}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                "parsed_at": datetime.now().isoformat(),
                "categories": [c['name'] for c in all_cats],
                "urls_by_category": all_products
            }, f, ensure_ascii=False, indent=2)
        
        # Parse some product pages (first 20)
        print("\nParsing sample product pages...")
        sample_urls = []
        for urls in all_products.values():
            sample_urls.extend(urls[:5])
        
        results = []
        for url in sample_urls[:20]:
            print(f"Parsing: {url}")
            results.append(await parse_product(ClientSession(), url))
        
        # Save sample results
        results_path = OUTPUT_DIR / f"sample_products_{datetime.now().strftime('%Y-%m-%d')}.json"
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\nDone! Results saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    asyncio.run(main())