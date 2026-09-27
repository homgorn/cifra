#!/usr/bin/env python3
"""
SEO Drift Monitor — сравнивает текущие SEO-элементы с baseline
"""

import asyncio
import aiohttp
import json
import re
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from bs4 import SoupStrainer

BASE_URL = "https://xn--18-6kc5a3bxam.xn--p1ai"
OUTPUT_DIR = Path("brain/wiki/audits/monitoring")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BASELINE_FILE = Path("data/baseline/seo_elements.json")
CURRENT_FILE = Path("data/processed/monitoring/drift_latest.jsonl")
REPORT_DIR = Path("brain/wiki/audits/monitoring")
REPORT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Cifra18Drift/1.0)"}
SEMAPHORE = asyncio.Semaphore(5)

def load_jsonl(file):
    data = {}
    if file.exists():
        with open(file) as f:
            for line in f:
                r = json.loads(line)
                data[r['url']] = r
    return data

def save_jsonl(file, data):
    file.parent.mkdir(parents=True, exist_ok=True)
    with open(file, 'w', encoding='utf-8') as f:
        for r in data:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')

async def fetch(session, url):
    async with asyncio.Semaphore(5):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as resp:
                    return resp.status, await resp.text()
        except Exception as e:
            return 0, str(e)

async def check_url(session, url):
    status, html = await fetch(session, url)
    if status != 200:
        return {"url": url, "status": status, "error": f"HTTP {status}"}
    
    soup = BeautifulSoup(html, 'html.parser')
    
    title = soup.select_one('title')
    title_text = clean_text(title.get_text()) if title else ""
    
    meta_desc = soup.select_one('meta[name="description"]')
    meta_desc_text = clean_text(meta_desc.get('content', '')) if meta_desc else ""
    
    h1s = soup.select('h1')
    h1_texts = [clean_text(h.get_text()) for h in h1s]
    
    canonical = soup.select_one('link[rel="canonical"]')
    canonical_href = canonical.get('href') if canonical else None
    
    json_ld = []
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            json_ld.append(json.loads(script.string))
        except:
            pass
    
    # Visible text
    for tag in soup(['script', 'style', 'noscript']):
        tag.decompose()
    visible_text = clean_text(soup.get_text())
    word_count = len(visible_text.split())
    
    em_dashes = visible_text.count('—')
    en_dashes = visible_text.count('–')
    
    return {
        "url": url,
        "status": status,
        "title": title_text,
        "title_len": len(title_text),
        "meta_description": meta_desc_text,
        "meta_desc_len": len(meta_desc_text),
        "h1_count": len(h1_texts),
        "h1_texts": " | ".join(h1_texts),
        "canonical": canonical_href,
        "has_canonical": canonical_href is not None,
        "json_ld_count": len(json_ld),
        "word_count": word_count,
        "em_dashes": em_dashes,
        "en_dashes": en_dashes,
    }

def clean_text(text: str) -> str:
    if not text: return ""
    return re.sub(r'\s+', ' ', text.strip())

def compare(baseline, current):
    drift = {}
    for url, base in baseline.items():
        if url not in current:
            drift[url] = {"status": "missing", "details": "Page not found in current crawl"}
            continue
        
        cur = current[url]
        changes = {}
        for field in ['title', 'h1_texts', 'meta_description', 'canonical', 'json_ld_count', 'word_count']:
            b_val = base.get(field)
            c_val = cur.get(field)
            if b_val != c_val:
                changes[field] = {"baseline": b_val, "current": c_val}
        
        if changes:
            drift[url] = {"status": "changed", "changes": changes}
    
    # New pages
    for url in current:
        if url not in baseline:
            drift[url] = {"status": "new", "details": "New page detected"}
    
    return drift

async def fetch(session, url):
    async with asyncio.Semaphore(5):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30) as resp:
                    return resp.status, await resp.text()
        except Exception as e:
            return 0, str(e)

async def main():
    import sys
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', action='store_true', help='Create baseline')
    args = parser.parse_args()
    
    print(f"=== ЦИФРА18 SEO Drift Monitor ===")
    print(f"Mode: {'Baseline' if args.baseline else 'Check'}")
    print(f"Started: {datetime.now()}")
    
    urls = [
        "https://xn--18-6kc5a3bxam.xn--p1ai/",
        "https://xn--18-6kc5a3bxam.xn--p1ai/catalog/poligrafiya/vizitki/",
        "https://xn--18-6kc5a3bxam.xn--p1ai/catalog/suvenirnaya-produktsiya/",
        "https://xn--18-6kc5a3bxam.xn--p1ai/catalog/shirokoformatnaya-pechat/",
        "https://xn--18-6kc5a3bxam.xn--p1ai/about/",
    ]
    
    async with aiohttp.ClientSession() as session:
        tasks = [check_url(session, u) for u in urls]
        results = await asyncio.gather(*tasks)
    
    current = {r['url']: r for r in results if 'error' not in r}
    
    if args.baseline:
        save_jsonl(BASELINE_FILE, current)
        print(f"Baseline saved to {BASELINE_FILE} ({len(current)} URLs)")
    else:
        baseline = load_jsonl(BASELINE_FILE)
        drift = compare(baseline, current)
        
        date_str = datetime.now().strftime("%Y-%m-%d")
        report = {
            "date": date_str,
            "baseline_date": "2026-09-10",
            "total_pages_baseline": len(baseline),
            "total_pages_current": len(current),
            "changed_pages": len([d for d in drift.values() if d['status'] == 'changed']),
            "new_pages": len([d for d in drift.values() if d['status'] == 'new']),
            "missing_pages": len([d for d in drift.values() if d['status'] == 'missing']),
            "drift_details": drift
        }
        
        with open(REPORT_DIR / f"drift_report_{date_str}.json", 'w') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        with open(REPORT_DIR / f"drift_report_{date_str}.md", 'w') as f:
            f.write(f"# SEO Drift Report — {date_str}\n\n")
            f.write(f"- Baseline pages: {report['total_pages_baseline']}\n")
            f.write(f"- Current pages: {report['total_pages_current']}\n")
            f.write(f"- Changed: {report['changed_pages']}\n")
            f.write(f"- New: {report['new_pages']}\n")
            f.write(f"- Missing: {report['missing_pages']}\n\n")
            
            if report['changed_pages'] > 0:
                f.write("## Изменения\n\n")
                for url, d in drift.items():
                    if d['status'] == 'changed':
                        f.write(f"### {url}\n")
                        for field, ch in d['changes'].items():
                            f.write(f"- **{field}**: `{ch['baseline']}` → `{ch['current']}`\n")
                        f.write("\n")
        
        save_jsonl(CURRENT_FILE, current)
        print(f"\nReports saved to {REPORT_DIR}")
        print(f"Changed: {report['changed_pages']}, New: {report['new_pages']}, Missing: {report['missing_pages']}")

if __name__ == "__main__":
    asyncio.run(main())