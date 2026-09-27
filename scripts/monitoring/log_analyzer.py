#!/usr/bin/env python3
"""
Server Log Analysis — crawl budget, боты, ошибки
Читает Nginx access.log
"""

import re
from collections import Counter
from pathlib import Path
from datetime import datetime, timedelta

LOG_FILE = Path("/var/log/nginx/access.log")
BOTS = {
    "googlebot": "Googlebot",
    "yandex": "YandexBot",
    "bingbot": "Bingbot",
    "gptbot": "GPTBot",
    "claudebot": "ClaudeBot",
    "perplexitybot": "PerplexityBot",
    "google-extended": "Google-Extended",
}

def parse_log_line(line):
    pattern = r'(\S+) - - \[(.*?)\] "(\S+) (\S+) HTTP/\d\.\d" (\d+) (\d+) ".*?" "(.*)"'
    m = re.match(pattern, line)
    if not m:
        return None
    ip, timestamp, method, url, status, size, ua = m.groups()
    return {"ip": ip, "timestamp": timestamp, "method": method, "url": url, "status": int(status), "size": int(size), "ua": ua.lower()}

def identify_bot(ua):
    for key, name in BOTS.items():
        if key in ua:
            return name
    return "user" if "mozilla" in ua else "other"

def main():
    print("=== ЦИФРА18 Log Analyzer ===")
    print(f"Started: {datetime.now()}")
    
    if not LOG_FILE.exists():
        print(f"Log file not found: {LOG_FILE}")
        return
    
    stats = {"total": 0, "by_bot": Counter(), "by_status": Counter(), "top_urls": Counter(), "bot_top_urls": Counter()}
    since = datetime.now() - timedelta(days=1)
    
    with open(LOG_FILE) as f:
        for line in f:
            parsed = parse_log_line(line)
            if not parsed:
                continue
            # Simple time filter - last N lines approximation
            stats["total"] += 1
            bot = identify_bot(parsed["ua"])
            stats["by_bot"][bot] += 1
            stats["by_status"][parsed["status"]] += 1
            stats["top_urls"][parsed["url"]] += 1
            if bot != "user":
                stats["bot_top_urls"][parsed["url"]] += 1
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    out_dir = Path("data/processed/monitoring/logs")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    report = {
        "date": date_str,
        "total_requests": stats["total"],
        "by_bot": dict(stats["by_bot"]),
        "by_status": dict(stats["by_status"]),
        "top_20_urls": dict(stats["top_urls"].most_common(20)),
        "bot_top_20_urls": dict(stats["bot_top_20_urls"].most_common(20)),
        "crawl_budget_estimate": stats["by_bot"].get("Googlebot", 0) + stats["by_bot"].get("YandexBot", 0),
    }
    
    out_dir = Path("data/processed/monitoring/logs")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    with open(out_dir / f"log_report_{date_str}.json", 'w') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"Total requests: {stats['total']}")
    print(f"By bot: {dict(stats['by_bot'])}")
    print(f"By status: {dict(stats['by_status'])}")
    print(f"Googlebot: {stats['by_bot'].get('Googlebot', 0)}")
    print(f"YandexBot: {stats['by_bot'].get('YandexBot', 0)}")
    
    # Alerts
    if stats["by_status"].get(500, 0) > 10:
        print(f"ALERT: High 5xx rate: {stats['by_status'].get(500, 0)} errors in 24h")
    if stats["by_bot"].get("Googlebot", 0) < 50:
        print(f"ALERT: Low Googlebot crawl: {stats['by_bot'].get('Googlebot', 0)} requests in 24h")

if __name__ == "__main__":
    import json
    main()