#!/usr/bin/env python3
"""
Competitor Monitoring Pipeline — Daily Automated Competitive Intelligence
Tracks: rankings, content changes, pricing, SERP features, new content
Outputs: Daily digest → Telegram + Notion + JSON archive
"""

import os
import asyncio
import aiohttp
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import logging

# ─── Configuration ──────────────────────────────────────────────
BASE_DIR = Path("/Users/user/Projects/цифра 2025/2026")
COMPETITORS_FILE = BASE_DIR / "brain/wiki/research/competitors/tracked_competitors.json"
OUTPUT_DIR = BASE_DIR / "brain/wiki/research/competitors/daily_monitoring"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; Cifra18CompetitorBot/1.0; +https://cifra18.ru)"
}

# ─── Data Models ────────────────────────────────────────────────
@dataclass
class Competitor:
    name: str
    url: str
    category: str  # "local", "federal", "marketplace", "niche"
    priority: int  # 1=critical, 2=high, 3=medium
    check_pages: List[str]  # key pages to monitor

@dataclass
class ChangeEvent:
    competitor: str
    change_type: str  # "ranking", "content", "price", "new_page", "serp_feature", "technical"
    severity: str  # "critical", "high", "medium", "low"
    description: str
    old_value: str
    new_value: str
    url: str
    timestamp: str

# ─── Default Competitors to Track ───────────────────────────────
DEFAULT_COMPETITORS = [
    # Federal
    Competitor("Printio", "https://printio.ru", "federal", 1, ["/", "/business", "/catalog"]),
    Competitor("RuPrint", "https://ruprint.ru", "federal", 1, ["/", "/catalog", "/blog"]),
    Competitor("Printful", "https://www.printful.com/ru", "federal", 2, ["/", "/catalog", "/integrations"]),
    Competitor("Canva Print", "https://www.canva.com/ru_ru/print/", "federal", 2, ["/", "/templates"]),
    # Local Izhevsk
    Competitor("Контур-Фото", "https://kontur-foto.ru", "local", 1, ["/", "/catalog", "/price"]),
    Competitor("SMART", "https://smart18.ru", "local", 2, ["/", "/services", "/portfolio"]),
    Competitor("Vaston", "https://vaston.ru", "local", 2, ["/", "/catalog", "/price"]),
    # Marketplaces
    Competitor("Wildberries", "https://www.wildberries.ru", "marketplace", 2, ["/catalog/merch", "/search"]),
    Competitor("Ozon", "https://www.ozon.ru", "marketplace", 2, ["/category/merch", "/search"]),
]

# ─── Utility Functions ──────────────────────────────────────────

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(OUTPUT_DIR / f"competitor_watch_{datetime.now().strftime('%Y-%m-%d')}.log"),
            logging.StreamHandler()
        ]
    )

async def fetch(session: aiohttp.ClientSession, url: str) -> tuple[int, str]:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                return resp.status, await resp.text()
    except Exception as e:
        return 0, str(e)

def calculate_hash(content: str) -> str:
    return hashlib.md5(content.encode()).hexdigest()[:16]

async def send_telegram(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        async with aiohttp.ClientSession() as session:
            await session.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
            )
    except Exception as e:
        logging.error(f"Telegram send failed: {e}")

# ─── Monitoring Functions ────────────────────────────────────────

async def check_rankings(competitor: Competitor) -> List[ChangeEvent]:
    """Check keyword rankings via Topvisor API (placeholder for now)"""
    changes = []
    # TODO: Integrate with Topvisor API when API key available
    # For now, return empty - will be implemented when API key available
    return changes

async def check_content_changes(session: aiohttp.ClientSession, competitor: Competitor, 
                                 previous_hashes: Dict[str, str]) -> List[ChangeEvent]:
    """Detect content changes on key pages"""
    changes = []
    
    for page_path in competitor.check_pages:
        url = f"{competitor.url.rstrip('/')}/{page_path.lstrip('/')}"
        status, html = await fetch_with_session(session, url)
        
        if status != 200:
            changes.append(ChangeEvent(
                competitor=competitor.name,
                change_type="technical",
                severity="high" if status == 0 else "medium",
                description=f"Page returned HTTP {status}",
                old_value="200",
                new_value=str(status),
                url=url,
                timestamp=datetime.now().isoformat()
            ))
            continue
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract main content for comparison
        main_content = soup.select_one('main, .content, .catalog, .products, .catalog-section, article, .main-content')
        content_text = soup.get_text() if not main_content else main_content.get_text()
        content_hash = calculate_hash(content_text)
        
        page_key = f"{competitor.name}:{page_path}"
        
        if page_key in previous_hashes:
            if previous_hashes[page_key] != content_hash:
                changes.append(ChangeEvent(
                    competitor=competitor.name,
                    change_type="content",
                    severity="medium",
                    description=f"Content changed on {page_path}",
                    old_value=f"hash:{previous_hashes[page_key]}",
                    new_value=f"hash:{content_hash}",
                    url=url,
                    timestamp=datetime.now().isoformat()
                ))
        else:
            # First time seeing this page
            pass
        
        previous_hashes[page_key] = content_hash
        
        # Check for new pages (simplified - would need full crawl for full detection)
        # Check for pricing changes (simplified)
        price_elements = soup.select('[class*="price"], [class*="cost"], .price, .cost, [data-price]')
        for el in price_elements[:5]:  # Check first 5 price elements
            price_text = el.get_text(strip=True)
            if price_text and any(c.isdigit() for c in price_text):
                price_key = f"{competitor.name}:price:{page_path}:{el.get('class', '')}"
                if price_key in previous_hashes:
                    if previous_hashes[price_key] != price_text:
                        changes.append(ChangeEvent(
                            competitor=competitor.name,
                            change_type="price",
                            severity="high",
                            description=f"Price changed on {page_path}",
                            old_value=previous_hashes[price_key],
                            new_value=price_text,
                            url=url,
                            timestamp=datetime.now().isoformat()
                        ))
                previous_hashes[price_key] = price_text
    
    return changes

async def check_serp_features(competitor: Competitor) -> List[ChangeEvent]:
    """Check SERP features for target keywords (placeholder)"""
    changes = []
    # TODO: Implement SERP feature tracking via scraping or API
    return changes

async def fetch_with_session(session: aiohttp.ClientSession, url: str) -> tuple[int, str]:
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                return resp.status, await resp.text()
        except Exception as e:
            return 0, str(e)

# ─── Main Monitoring Loop ────────────────────────────────────────

async def load_previous_state() -> Dict:
    """Load previous monitoring state"""
    state_file = OUTPUT_DIR / "monitoring_state.json"
    if state_file.exists():
        with open(state_file) as f:
            return json.load(f)
    return {"content_hashes": {}, "price_hashes": {}, "last_run": None}

async def save_state(state: Dict):
    state_file = OUTPUT_DIR / "monitoring_state.json"
    state["last_run"] = datetime.now().isoformat()
    with open(state_file, 'w') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

async def save_changes(changes: List[ChangeEvent]):
    """Save changes to daily file and send alerts"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    changes_file = OUTPUT_DIR / f"changes_{date_str}.jsonl"
    
    with open(changes_file, 'a', encoding='utf-8') as f:
        for change in changes:
            f.write(json.dumps(asdict(change), ensure_ascii=False) + '\n')
    
    # Send Telegram alerts for critical/high changes
    critical_changes = [c for c in changes if c.severity in ("critical", "high")]
    if critical_changes and TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        message = f"🚨 <b>Competitor Alert</b> — {len(critical_changes)} critical/high changes\n\n"
        for c in critical_changes[:5]:
            message += f"• <b>{c.competitor}</b>: {c.change_type} — {c.description}\n  <a href='{c.url}'>Open</a>\n"
        await send_telegram(message)

async def generate_daily_report(changes: List[ChangeEvent], competitors: List[Competitor]):
    """Generate daily monitoring report"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    report_file = OUTPUT_DIR / f"daily_report_{date_str}.md"
    
    with open(OUTPUT_DIR / f"daily_report_{date_str}.md", 'w', encoding='utf-8') as f:
        f.write(f"# Daily Competitor Monitoring Report — {date_str}\n\n")
        f.write(f"**Run Time:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"**Competitors Monitored:** {len(competitors)}\n\n")
        
        if not changes:
            f.write("✅ <b>No significant changes detected</b>\n")
        else:
            f.write(f"## Changes Detected: {len(changes)}\n\n")
            
            # Group by competitor
            by_competitor = {}
            for change in changes:
                if change.competitor not in by_competitor:
                    by_competitor[change.competitor] = []
                by_competitor[change.competitor].append(change)
            
            for comp, changes_list in by_competitor.items():
                f.write(f"### {comp} ({len(changes_list)} changes)\n\n")
                for c in changes_list:
                    severity_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(c.severity, "⚪")
                    f.write(f"- {severity_emoji} <b>{c.change_type}</b>: {c.description}\n")
                    f.write(f"  <i>Old:</i> {c.old_value[:100]} → <i>New:</i> {c.new_value[:100]}\n")
                    f.write(f"  🔗 <a href='{c.url}'>Open page</a>\n\n")
        
        f.write(f"\n---\n*Generated: {datetime.now().isoformat()}*")
    
    # Also save JSON for programmatic access
    with open(OUTPUT_DIR / f"changes_{date_str}.json", 'w', encoding='utf-8') as f:
        json.dump([asdict(c) for c in changes], f, ensure_ascii=False, indent=2)

async def run_monitoring_cycle(competitors: List[Competitor]):
    """Run one complete monitoring cycle"""
    logging.info(f"Starting monitoring cycle for {len(competitors)} competitors")
    
    # Load previous state
    state = await load_previous_state()
    content_hashes = state.get("content_hashes", {})
    price_hashes = state.get("price_hashes", {})
    
    all_changes = []
    
    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl=False, limit=10),
        timeout=aiohttp.ClientTimeout(total=30)
    ) as session:
        
        # Run checks for each competitor
        for competitor in competitors:
            logging.info(f"Checking {competitor.name} ({competitor.url})")
            
            # Check content changes
            changes = await check_content_changes(session, competitor, content_hashes)
            all_changes.extend(changes)
            
            # Check rankings (placeholder)
            ranking_changes = await check_rankings(competitor)
            all_changes.extend(ranking_changes)
            
            # Check SERP features (placeholder)
            serp_changes = await check_serp_features(competitor)
            all_changes.extend(serp_changes)
            
            # Small delay between competitors
            await asyncio.sleep(1)
    
    # Save results
    if all_changes:
        await save_changes(all_changes)
        await generate_daily_report(all_changes, competitors)
        logging.warning(f"Found {len(all_changes)} changes!")
    else:
        logging.info("No changes detected")
    
    # Update state
    state["content_hashes"] = content_hashes
    state["price_hashes"] = price_hashes
    await save_state(state)
    
    logging.info("Monitoring cycle complete")

async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--daemon', action='store_true', help='Run as daemon (every 6 hours)')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    args = parser.parse_args()
    
    setup_logging()
    logging.info("Starting Competitor Watch")
    
    # Load competitors (from file or use defaults)
    competitors_file = COMPETITORS_FILE
    if competitors_file.exists():
        with open(competitors_file) as f:
            data = json.load(f)
            competitors = [Competitor(**c) for c in data]
    else:
        competitors = DEFAULT_COMPETITORS
        # Save defaults
        with open(competitors_file, 'w') as f:
            json.dump([asdict(c) for c in DEFAULT_COMPETITORS], f, ensure_ascii=False, indent=2)
    
    logging.info(f"Monitoring {len(competitors)} competitors")
    
    if args.daemon:
        while True:
            await run_monitoring_cycle(DEFAULT_COMPETITORS)
            logging.info("Sleeping 6 hours...")
            await asyncio.sleep(6 * 3600)
    else:
        await run_monitoring_cycle(competitors)

if __name__ == "__main__":
    asyncio.run(main())