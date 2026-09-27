#!/usr/bin/env python3
"""
Alerting System — Telegram/Email уведомления
"""

import os
import requests
import json
from enum import Enum

class AlertLevel(Enum):
    CRITICAL = "🔴"
    WARNING = "🟠"
    INFO = "🔵"

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = "user/cifra18-seo"

def send_alert(message: str, level: AlertLevel = AlertLevel.WARNING, create_issue: bool = False):
    emoji = level.value
    text = f"{emoji} ЦИФРА18 SEO Monitor\n{message}"
    
    # Telegram
    if BOT_TOKEN and CHAT_ID:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
        )
    
    # GitHub Issue for CRITICAL
    if create_issue and level == AlertLevel.CRITICAL:
        requests.post(
            f"https://api.github.com/repos/{GITHUB_REPO}/issues",
            headers={"Authorization": f"token {GITHUB_TOKEN}"},
            json={"title": f"[CRITICAL] {message.split(chr(10))[0]}", "body": message}
        )

# Usage in collectors:
# if check_failed:
#     send_alert(f"Sitemap 404: {url}", AlertLevel.CRITICAL, create_issue=True)

# Usage examples:
# if check_failed:
#     send_alert(f"Sitemap 404: {url}", AlertLevel.CRITICAL, create_issue=True)
# if meta_desc == "Description":
#     send_alert(f"Meta description placeholder on {url}", AlertLevel.WARNING)
# if h1_count != 1:
#     send_alert(f"H1 count = {h1_count} on {url}", AlertLevel.CRITICAL)
# if json_ld_invalid:
#     send_alert(f"JSON-LD invalid on {url}", AlertLevel.CRITICAL)
# if stats["by_bot"].get("Googlebot", 0) < 50:
#     send_alert(f"Low Googlebot crawl: {stats['by_bot'].get('Googlebot', 0)}", AlertLevel.CRITICAL, create_issue=True)
# if stats["by_status"].get(500, 0) > 10:
#     send_alert(f"High 5xx rate: {stats['by_status'][500]} errors in 24h", AlertLevel.CRITICAL, create_issue=True)

# Alert Levels:
# 🔴 CRITICAL: Sitemap 404, canonical missing, meta placeholder, H1 count != 1, JSON-LD invalid, 5xx > 10, Googlebot crawl < 50
# 🟠 WARNING: Meta desc length >160/<70, H1 missing keyword, Schema coverage <90%, Page speed LCP>2.5s, New orphan pages >5
# 🔵 INFO: New pages indexed, New backlinks, New brand mentions in AI, New keywords in top-20