# Monitoring Index: ЦИФРА18

**Last updated:** 2026-09-10

---

## 📊 Monitoring Stack Overview

```
MONITORING STACK
├── DATA SOURCES
│   ├── Яндекс.Метрика (API / Logs API)
│   ├── Топвизор (API v2)
│ ├── Google Search Console (API) - когда доступ
│   ├── Яндекс.Вебмастер (API / экспорт)
│   ├── Серверные логи (Nginx access.log)
│   ├── Bitrix (sitemap, каталог, ошибки)
│   └── WP поддомен (WP REST API / sitemap)
├── COLLECTORS (Python scripts, systemd timers)
│ ├── tech_health.py - Daily 03:00 ✅
│ ├── drift_monitor.py - Daily 04:00 ✅
│ ├── rankings_pull.py - Daily 05:00 ✅
│ ├── log_analyzer.py - Daily 06:00 ✅
│ ├── geo_tracker.py - Weekly Mon 07:00 ✅
│ ├── content_inventory.py - Weekly Tue 07:00 ✅
│ ├── full_audit.py - Monthly 1st 02:00 ✅
│ └── alerts.py - Telegram/Email алерты ✅
├── STORAGE
│   ├── DuckDB (data/processed/monitoring/monitoring.duckdb)
│   ├── JSONL/JSON (data/processed/monitoring/)
│   ├── Markdown reports (brain/wiki/audits/monitoring/)
│   └── Git history (brain/wiki/audits/monitoring/)
├── ALERTING
│   ├── Telegram Bot (critical/warning/info)
│   ├── Email (weekly/monthly summaries)
│   └── GitHub Issues (tech debt)
└── DASHBOARDS
    ├── Markdown reports (primary)
    ├── Notion / Google Sheets (KPI tracking)
    └── Grafana (optional, if DuckDB connected)
```

---

## 📅 Collection Schedule

| Script | Frequency | Time (UTC+3) | Output |
|---|---|---|---|
| `tech_health.py` | Daily | 03:00 | `data/processed/monitoring/tech_health/YYYY-MM-DD.jsonl` |
| `drift_monitor.py` | Daily | 04:00 | `brain/wiki/audits/monitoring/drift_report_YYYY-MM-DD.md/.json` |
| `rankings_pull.py` | Daily | 05:00 | `data/processed/monitoring/rankings/positions_YYYY-MM-DD.json` |
| `log_analyzer.py` | Daily | 06:00 | `data/processed/monitoring/logs/log_report_YYYY-MM-DD.json` |
| `geo_tracker.py` | Weekly (Mon) | 07:00 | `brain/wiki/audits/monitoring/geo_report_YYYY-MM-DD.md/.json` |
| `content_inventory.py` | Weekly (Tue) | 07:00 | `data/processed/monitoring/content_inventory/YYYY-MM-DD.json` |
| `full_audit.py` | Monthly (1st) | 02:00 | `brain/wiki/audits/monitoring/monthly_YYYY-MM.md` |

---

## 📁 Report Locations

| Report Type | Location | Format |
|---|---|---|
| Weekly Summary | `brain/wiki/audits/monitoring/weekly_YYYY-MM-DD.md` | Markdown |
| Monthly Full | `brain/wiki/audits/monitoring/monthly_YYYY-MM.md` | Markdown (Template A+B) |
| Daily Drift | `brain/wiki/audits/monitoring/drift_report_YYYY-MM-DD.md` | Markdown + JSON |
| Weekly GEO | `brain/wiki/audits/monitoring/geo_report_YYYY-MM-DD.md` | Markdown + JSON |
| Daily Tech Health | `brain/wiki/audits/monitoring/tech_health_report_YYYY-MM-DD.md` | Markdown + JSON |
| Raw Data | `data/processed/monitoring/{collector}/` | JSONL/JSON |

---

## 🚨 Alert Rules

### 🔴 CRITICAL (Immediate Telegram + GitHub Issue)
| Condition | Threshold | Action |
|---|---|---|
| Sitemap 404 | Any sitemap in robots.txt returns 404 | Alert + auto-create GitHub issue |
| Canonical missing | >5% pages missing canonical | Alert |
| Meta description placeholder | Any page has "Description" | Alert |
| H1 count ≠ 1 | Any page has 0 or >1 H1 | Alert |
| JSON-LD invalid | Rich Results Test errors on money pages | Alert |
| 5xx errors | >10 in 24h (logs) | Alert |
| Googlebot crawl | <50 requests/24h | Alert |
| Rankings drop | Top-10 keyword drops >5 positions | Alert |
| AI visibility drop | Brand mentions = 0 for 3 days | Alert |

### 🟠 WARNING (Telegram, next business day)
| Condition | Threshold |
|---|---|
| Meta description length | >160 or <70 chars |
| H1 missing keyword | Primary keyword not in H1 |
| Schema coverage | <90% money pages have schema |
| Page speed | LCP > 2.5s or INP > 200ms (sample) |
| New orphan pages | >5 new pages with 0 internal links |
| Content decay | Page losing clicks + impressions 90d (GSC) |

### 🔵 INFO (Weekly summary only)
- New pages indexed
- New backlinks found
- New brand mentions in AI
- New keywords in top-20
- Content published this week

---

## 🔧 Alert Implementation (Telegram Bot)

```python
# scripts/monitoring/alerts.py
import os
import requests
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
```

---

## 📊 KPI Dashboard (Notion / Google Sheets)

| Metric | Source | Frequency | Target |
|---|---|---|---|
| Organic Traffic | Метрика / GA4 | Weekly | +10% MoM |
| Non-brand Clicks | Метрика / GSC | Weekly | +15% MoM |
| Leads from Organic | CRM + UTM | Weekly | +10% MoM |
| Top-10 Keywords | Топвизор | Daily | +2/week |
| Visibility % | Топвизор | Daily | +1%/week |
| AI Brand Mentions | GEO tracker | Weekly | >0 |
| Citability Score (avg top-20) | GEO tracker | Weekly | >80 |
| Schema Coverage | Tech health | Daily | 100% money pages |
| Canonical Coverage | Drift monitor | Daily | 100% |
| 5xx Rate | Log analyzer | Daily | <0.1% |
| Googlebot Crawl | Log analyzer | Daily | >200/day |

---

## 🗄 Data Retention

| Data Type | Retention | Storage |
|---|---|---|
| Raw collector JSONL | 90 days | Local disk → archive to R2/S3 |
| Daily reports (Markdown) | 1 year | Git (brain/wiki/audits/monitoring/) |
| Monthly reports | Forever | Git |
| DuckDB metrics | 2 years | Local disk |
| Exports (CSV/JSON) | 1 year | data/exports/ → archive |

---

## 🚀 Deployment Checklist

- [ ] Server/container for monitoring (can be same as production or separate)
- [ ] Python 3.11+ + dependencies (requirements.txt)
- [ ] `.env` with all API keys
- [ ] Systemd timers installed and enabled
- [ ] Telegram bot created, chat ID obtained, test alert sent
- [ ] GitHub token for issue creation (optional)
- [ ] DuckDB initialized (`python -c "import duckdb; duckdb.connect('data/processed/monitoring/monitoring.duckdb').execute('CREATE TABLE IF NOT EXISTS metrics (ts TIMESTAMP, metric VARCHAR, value DOUBLE, tags JSON)')"`)
- [ ] Baseline capture run (after Phase 0 fixes)
- [ ] First 3 daily reports received and validated
- [ ] Weekly review meeting scheduled (Mon 10:00)
- [ ] Documentation in `brain/wiki/audits/monitoring/INDEX.md`

---

## 📈 First Week Validation

| Day | Check |
|---|---|
| Day 1 | All collectors run without errors, data in `data/processed/monitoring/` |
| Day 2 | Drift monitor baseline captured, no false positives |
| Day 3 | Rankings pull working, data in `data/processed/monitoring/rankings/` |
| Day 4 | Log analyzer parsing correctly, bot detection working |
| Day 5 | GEO tracker manual run successful (brand prompts) |
| Day 6 | Weekly report generated automatically Mon 10:00 |
| Day 7 | Review all reports, tune alert thresholds, document in `session_checkpoints/` |

---

## 📦 Scripts в стеке мониторинга

| Script | Path | Status | Description |
|---|---|---|---|
| `tech_health.py` | `scripts/monitoring/` | ✅ | HTTP, robots, sitemap, SSL, CSP, headers, canonical, schema |
| `drift_monitor.py` | `scripts/monitoring/` | ✅ | SEO drift (titles, H1, meta, canonical, schema, word count) |
| `rankings_pull.py` | `scripts/monitoring/` | ✅ | Топвизор API позиции, история изменений |
| `log_analyzer.py` | `scripts/monitoring/` | ✅ | Nginx access.log (crawl budget, боты, ошибки) |
| `geo_tracker.py` | `scripts/monitoring/` | ✅ | AI visibility, brand mentions, citability score |
| `content_inventory.py` | `scripts/monitoring/` | ✅ | Новые/изменённые страницы, word count, schema status |
| `alerts.py` | `scripts/monitoring/` | ✅ | Telegram/Email/GitHub алерты |
| `full_audit.py` | `scripts/monitoring/` | 🔄 | Ежемесячный полный seo-geo-audit |

---

*Мониторинг: это страховка. Настройка займёт 1-2 дня, а сэкономит недели поиска причин падений.*