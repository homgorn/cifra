#!/usr/bin/env python3
"""
Cifra18 Complete Catalog Fetcher - All 88 subcategories
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import csv
from datetime import datetime
from pathlib import Path
import urllib3

urllib3.disable_warnings()

BASE_URL = "https://xn--18-6kc5a3bxam.xn--p1ai"
OUTPUT_DIR = Path("brain/wiki/entities/full_catalog")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

import urllib3
urllib3.disable_warnings()

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

def get_all_subcategories():
    """Get all 88 subcategories from main menu"""
    resp = requests.get("https://xn--18-6kc5a3bxam.xn--p1ai/", verify=False, timeout=30)
    soup = BeautifulSoup(resp.text, 'html.parser')
    all_subcats = []
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

def get_product_urls(cat_url):
    """Get all product URLs from a category (up to 5 pages)"""
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
        if len(urls) == 0 and page > 1:
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
    
    canonical = soup.select_one('link[rel="canonical"]')
    canonical = canonical.get('href') if canonical else None
    
    json_ld_count = len(soup.select('script[type="application/ld+json"]'))
    
    price_text = ""
    for el in soup.select('.price, .calculator, [class*="price"], .news-card__type, .catalog-item__price'):
        price_text += " " + el.get_text(strip=True)
    
    price_info = {"raw": "", "value": None, "unit": ""}
    m = re.search(r'от\s+([\d\s]+)\s*₽/([^\s]+)', price_text)
    if m: price_info = {"value": int(m.group(1).replace(' ', '')), "unit": m.group(2)}
    else:
        m = re.search(r'([\d\s]+)\s*₽/([^\s]+)', price_text)
        if m: price_info = {"value": int(m.group(1).replace(' ', '')), "unit": m.group(2)}
    
    for tag in soup(['script', 'style', 'noscript']):
        tag.decompose()
    text = soup.get_text()
    words = len(re.sub(r'\s+', ' ', text).strip().split())
    
    images = []
    for img in soup.select('img'):
        src = img.get('src') or img.get('data-src')
        if src:
            images.append({"src": src, "alt": img.get('alt', ''), "has_alt": bool(img.get('alt', '').strip())})
    
    return {
        "url": url,
        "title": soup.select_one('title').get_text(strip=True) if soup.select_one('title') else "",
        "meta_description": soup.select_one('meta[name="description"]').get('content', '') if soup.select_one('meta[name="description"]') else "",
        "h1": " | ".join([h.get_text(strip=True) for h in soup.select('h1')]),
        "canonical": canonical.get('href') if canonical else None,
        "json_ld_count": len(soup.select('script[type="application/ld+json"]')),
        "images_count": len(soup.select('img')),
        "images_no_alt": sum(1 for img in soup.select('img') if not img.get('alt', '').strip()),
        "word_count": len(re.sub(r'\s+', ' ', BeautifulSoup(requests.get(url, verify=False).text, 'html.parser').get_text()).strip().split()),
        "price_value": int(re.search(r'от\s+([\d\s]+)\s*₽', soup.get_text()).group(1).replace(' ', '')) if re.search(r'от\s+([\d\s]+)\s*₽', soup.get_text()) else None,
        "price_unit": "руб/шт",
    }

def main():
    import urllib3; urllib3.disable_warnings()
    
    print("=== Cifra18 Complete Catalog Fetcher ===")
    
    # Get all subcategories
    print("1. Fetching all 88 subcategories...")
    subcategories = []
    resp = requests.get("https://xn--18-6kc5a3bxam.xn--p1ai/", verify=False, timeout=30)
    soup = BeautifulSoup(resp.text, 'html.parser')
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
    
    print(f"Total subcategories: {len(all_subcats)}")
    
    OUTPUT_DIR = Path("brain/wiki/entities/full_catalog")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Get all product URLs
    print("2. Fetching product URLs from all subcategories...")
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
    
    # Save URLs
    date_str = datetime.now().strftime("%Y-%m-%d")
    with open(f"brain/wiki/entities/full_catalog/catalog_urls_{datetime.now().strftime('%Y-%m-%d')}.json", 'w') as f:
        json.dump({"parsed_at": datetime.now().isoformat(), "urls_by_category": {k: list(v) for k, v in all_urls.items()}}, f, ensure_ascii=False, indent=2)
    
    # Parse sample products
    print("\nParsing sample products (up to 100)...")
    sample_urls = []
    for urls in all_urls.values():
        sample_urls.extend(urls[:3])
    
    results = []
    for url in sample_urls[:100]:
        print(f"Parsing: {url}")
        results.append(parse_product(url))
    
    # Save results
    date_str = datetime.now().strftime("%Y-%m-%d")
    with open(f"brain/wiki/entities/full_catalog/sample_products_{datetime.now().strftime('%Y-%m-%d')}.json", 'w') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # Create comprehensive markdown
    print("\nGenerating comprehensive markdown documentation...")
    
    # Master index
    md = f"# ЦИФРА18 — Полный каталог услуг\n\n"
    md += f"**Дата парсинга:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    md += f"**Всего подкатегорий:** {len(all_subcats)}\n"
    md += f"**Всего товаров/услуг:** {sum(len(v) for v in all_urls.values())}\n\n"
    
    md += "## Структура каталога\n\n"
    for cat in categories:
        cat_subs = [s for s in all_subcats if s['cat'] == cat['name']]
        md += f"### {cat['name']} ({len(cat_subs)} подкатегорий)\n\n"
        for sub in cat_subs:
            count = len(all_urls.get(sub['cat'] + " > " + sub['name'], []))
            md += f"- [{sub['name']}]({sub['url']}) — {count} товаров\n"
        md += "\n"
    
    md += "## Все товары/услуги\n\n"
    for cat_name, urls in sorted(all_urls.items(), key=lambda x: -len(x[1])):
        md += f"### {cat_name} ({len(urls)} товаров)\n\n"
        for url in urls:
            md += f"- {url}\n"
        md += "\n"
    
    # Save master markdown
    with open(f"brain/wiki/entities/full_catalog/FULL_CATALOG_{datetime.now().strftime('%Y-%m-%d')}.md", 'w') as f:
        f.write(md)
    
    print("\nDone! All data saved.")

if __name__ == "__main__":
    main()