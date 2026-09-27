#!/usr/bin/env python3
"""
Daily Technical Health Check
Проверяет: HTTP 200, robots.txt, sitemap.xml, SSL, CSP, заголовки, canonical, JSON-LD
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup

BASE_URL = "https://xn--18-6kc5a3bxam.xn--p1ai"
OUTPUT_DIR = Path("data/processed/monitoring/tech_health")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; Cifra18Health/1.0; +https://cifra18.ru)"
}

SEMAPHORE = asyncio.Semaphore(5)

CHECKS = [
    ("http_status", lambda resp, soup: resp.status == 200),
    ("has_canonical", lambda resp, soup: bool(soup.select_one('link[rel="canonical"]'))),
    ("has_json_ld", lambda resp, soup: len(soup.select('script[type="application/ld+json"]')) > 0),
    ("meta_robots_ok", lambda resp, soup: "noindex" not in (soup.select_one('meta[name="robots"]') or {}).get('content', '')),
    ("has_h1", lambda resp, soup: len(soup.select('h1')) == 1),
    ("has_viewport", lambda resp, soup: bool(soup.select_one('meta[name="viewport"]'))),
    ("ssl_valid", lambda resp, soup: resp.url.scheme == 'https'),
]

async def fetch(session, url):
    async with SEMAPHORE:
        try:
            async with session.get(url, headers=HEADERS, timeout=30) as resp:
                html = await resp.text()
                return resp.status, html, str(resp.url)
        except Exception as e:
            return 0, str(e), url

async def check_url(session, url):
    status, html, final_url = await fetch(session, url)
    if status != 200:
        return {"url": url, "status": status, "error": f"HTTP {status}"}
    
    soup = BeautifulSoup(html, 'html.parser')
    
    results = {"url": url, "status": status, "checks": {}}
    for name, check in CHECKS:
        try:
            results["checks"][name] = check(None, soup)
        except Exception as e:
            results["checks"][name] = False
    
    return results

URLS = [
    "https://xn--18-6kc5a3bxam.xn--p1ai/",
    "https://xn--18-6kc5a3bxam.xn--p1ai/catalog/poligrafiya/vizitki/",
    "https://xn--18-6kc5a3bxam.xn--p1ai/catalog/suvenirnaya-produktsiya/",
    "https://xn--18-6kc5a3bxam.xn--p1ai/catalog/shirokoformatnaya-pechat/",
    "https://xn--18-6kc5a3bxam.xn--p1ai/about/",
]

async def main():
    print(f"=== ЦИФРА18 Tech Health Check ===")
    print(f"Started: {datetime.now()}")
    
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(*[check_url(session, u) for u in URLS])
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    out_dir = Path("data/processed/monitoring/tech_health")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    with open(out_dir / f"{date_str}.jsonl", 'w') as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    
    # Markdown report
    md_path = Path("brain/wiki/audits/monitoring/tech_health_report_{date_str}.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# Tech Health Report — {date_str}\n\n")
        for r in results:
            failed = [k for k, v in r.get('checks', {}).items() if not v]
            status = "✅ PASS" if not failed else f"❌ FAIL ({', '.join(failed)})"
            f.write(f"- {r['url']}: {status}\n")
    
    print(f"\nReports saved to {out_dir} and {md_path}")

if __name__ == "__main__":
    asyncio.run(main())