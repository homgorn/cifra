#!/usr/bin/env python3
"""
Monthly Full SEO+GEO Audit
Запускается 1-го числа каждого месяца
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup

BASE_URL = "https://xn--18-6kc5a3bxam.xn--p1ai"
OUTPUT_DIR = Path("brain/wiki/audits/monitoring")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

async def fetch(session, url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=30) as resp:
                return resp.status, await resp.text()
    except Exception as e:
        return 0, str(e)

async def audit_page(session, url):
    status, html = await fetch(session, url)
    if status != 200:
        return {"url": url, "status": status, "error": f"HTTP {status}"}
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Technical checks
    title = soup.select_one('title')
    title_text = title.get_text(strip=True) if title else ""
    
    meta_desc = soup.select_one('meta[name="description"]')
    desc = meta_desc.get('content', '').strip() if meta_desc else ""
    
    h1s = soup.select('h1')
    h1_count = len(h1s)
    h1_texts = [h.get_text(strip=True) for h in h1s]
    
    canonical = soup.select_one('link[rel="canonical"]')
    canonical_href = canonical.get('href') if canonical else None
    
    json_ld = []
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            json_ld.append(json.loads(script.string))
        except:
            pass
    
    return {
        "url": url,
        "status": status,
        "title": title_text,
        "meta_description": desc,
        "h1_count": h1_count,
        "canonical": canonical_href,
        "json_ld_count": len(json_ld),
    }

async def main():
    print("=== ЦИФРА18 Monthly Full Audit ===")
    print(f"Started: {datetime.now()}")
    
    # Key pages to audit
    urls = [
        BASE_URL,
        f"{BASE_URL}/catalog/poligrafiya/vizitki/",
        f"{BASE_URL}/catalog/suvenirnaya-produktsiya/",
        f"{BASE_URL}/catalog/shirokoformatnaya-pechat/",
        f"{BASE_URL}/about/",
        f"{BASE_URL}/news/",
    ]
    
    async with aiohttp.ClientSession() as session:
        results = []
        for url in urls:
            print(f"Auditing: {url}")
            results.append(await audit_page(session, url))
    
    # Save report
    date_str = datetime.now().strftime("%Y-%m-%d")
    out_dir = Path("brain/wiki/audits/monitoring")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    report = {
        "date": date_str,
        "pages_audited": len(results),
        "results": results
    }
    
    with open(f"brain/wiki/audits/monitoring/monthly_{date_str}.json", 'w') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # Markdown report
    with open(f"brain/wiki/audits/monitoring/monthly_{date_str[:7]}.md", 'w') as f:
        f.write(f"# Monthly SEO/GEO Audit — {date_str[:7]}\n\n")
        f.write(f"**Pages audited:** {len(results)}\n\n")
        
        for r in results:
            f.write(f"## {r['url']}\n")
            f.write(f"- Status: {r['status']}\n")
            f.write(f"- Title: {r['title'][:60]} (len: {len(r['title'])})\n")
            f.write(f"- Meta Description: {r['meta_description'][:80]} (len: {len(r['meta_description'])})\n")
            f.write(f"- H1 Count: {r['h1_count']}\n")
            f.write(f"- Canonical: {'✅' if r['canonical'] else '❌'}\n")
            f.write(f"- JSON-LD Count: {r['json_ld_count']}\n\n")
        
        # Summary
        issues = []
        for r in results:
            if r['status'] != 200: issues.append(f"HTTP {r['status']}: {r['url']}")
            if r['h1_count'] != 1: issues.append(f"H1 count = {r['h1_count']}: {r['url']}")
            if not r['canonical']: issues.append(f"No canonical: {r['url']}")
            if r['json_ld_count'] == 0: issues.append(f"No JSON-LD: {r['url']}")
        
        f.write(f"\n## Issues Found ({len(issues)})\n\n")
        for issue in issues:
            f.write(f"- {issue}\n")
    
    print(f"\nMonthly audit saved to brain/wiki/audits/monitoring/")

if __name__ == "__main__":
    asyncio.run(main())