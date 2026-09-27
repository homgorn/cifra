# Авто-аудит и мониторинг — ЦИФРА18
## SEO Drift + GEO Tracking + Rankings + Technical Health

**Цель:** Непрерывный контроль здоровья сайта, раннее обнаружение регрессий, измерение ROI SEO/GEO инвестиций.

---

## 🏗 Архитектура мониторинга

```
┌─────────────────────────────────────────────────────────────┐
│                    MONITORING STACK                         │
├─────────────────────────────────────────────────────────────┤
│  DATA SOURCES                                               │
│  ├── Яндекс.Метрика (API / Logs API)                        │
│  ├── Топвизор (API v2)                                      │
│   │   ├── Google Search Console (API) — когда появится      │
│  ├── Яндекс.Вебмастер (API / экспорт)                       │
│  ├── Серверные логи (Nginx/Apache access.log)               │
│  ├── Bitrix (sitemap, каталог, ошибки)                      │
│  └── WP поддомен (WP REST API / sitemap)                    │
├─────────────────────────────────────────────────────────────┤
│  COLLECTORS (Python scripts, cron / systemd timers)         │
│  ├── drift_monitor.py        — ежедневно                    │
│  ├── geo_tracker.py          — еженедельно                  │
│  ├── rankings_pull.py        — ежедневно (Топвизор)         │
│  ├── tech_health.py          — ежедневно                    │
│  ├── log_analyzer.py         — ежедневно                    │
│  └── content_inventory.py    — еженедельно                  │
├─────────────────────────────────────────────────────────────┤
│  STORAGE                                                    │
│  ├── SQLite / DuckDB (локально) — метрики, история          │
│  ├── JSON/Parquet (экспорты) — для BI                       │
│  └── Git (brain/wiki/audits/) — отчёты и baseline'ы         │
├─────────────────────────────────────────────────────────────┤
│  ALERTING                                                   │
│  ├── Telegram Bot (критические алерты)                      │
│  ├── Email (суммарные отчёты)                               │
│  └── GitHub Issues (тех. долги)                             │
├─────────────────────────────────────────────────────────────┤
│  DASHBOARDS                                                 │
│  ├── Grafana (метрики) — опционально                        │
│  ├── Markdown отчёты (brain/wiki/audits/monitoring/)        │
│  └── Notion / Google Sheets (KPI трекинг)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📅 Расписание сборов

| Скрипт | Частота | Время | Выходные данные |
|---|---|---|---|
| `tech_health.py` | Ежедневно | 03:00 | HTTP коды, robots.txt, sitemap, SSL, CSP, Security headers |
| `drift_monitor.py` | Ежедневно | 04:00 | Diff titles, H1, meta desc, canonical, schema, word count |
| `rankings_pull.py` | Ежедневно | 05:00 | Позиции топ-500 ключей (Топвизор API) |
| `log_analyzer.py` | Ежедневно | 06:00 | Crawl budget, боты, 4xx/5xx, lenta-index |
| `geo_tracker.py` | Еженедельно (Пн) | 07:00 | AI visibility, brand mentions, citability score |
| `content_inventory.py` | Еженедельно (Вт) | 07:00 | Новые/изменённые страницы, word count, schema status |
| `full_audit.py` | Ежемесячно (1-е) | 02:00 | Полный seo-geo-audit (как baseline) |

---

## 🔧 Скрипты (Implementation)

### 1. `scripts/monitoring/tech_health.py`
```python
#!/usr/bin/env python3
"""
Daily Technical Health Check
Проверяет: HTTP 200, robots.txt, sitemap.xml, SSL, CSP, Security headers,
Canonical presence, JSON-LD presence, Meta robots, Viewport, H1 count
"""
import asyncio
import aiohttp
import json
from datetime import datetime
from pathlib import Path

URLS = [
    "https://xn--18-6kc5a3bxam.xn--p1ai/",
    "https://xn--18-6kc5a3bxam.xn--p1ai/catalog/",
    "https://xn--18-6kc5a3bxam.xn--p1ai/catalog/poligrafiya/vizitki/",
    "https://xn--18-6kc5a3bxam.xn--p1ai/news/",
    "https://xn--18-6kc5a3bxam.xn--p1ai/about/",
    # + топ-50 money pages из конфига
]

CHECKS = [
    ("http_status", lambda r: r.status == 200),
    ("has_canonical", lambda soup: bool(soup.select_one('link[rel="canonical"]'))),
    ("has_json_ld", lambda soup: len(soup.select('script[type="application/ld+json"]')) > 0),
    ("meta_robots_ok", lambda soup: "noindex" not in (soup.select_one('meta[name="robots"]') or {}).get('content', '')),
    ("has_h1", lambda soup: len(soup.select('h1')) == 1),
    ("has_viewport", lambda soup: bool(soup.select_one('meta[name="viewport"]'))),
    ("ssl_valid", lambda r: r.url.scheme == 'https'),
]

async def check_url(session, url):
    async with session.get(url, timeout=30) as resp:
        html = await resp.text()
        soup = BeautifulSoup(html, 'html.parser')
        return {
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "http_status": resp.status,
            "checks": {name: check(resp if 'resp' in check.__code__.co_varnames else soup) 
                      for name, check in CHECKS}
        }

async def main():
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(*[check_url(session, u) for u in URLS])
    
    # Save
    date_str = datetime.now().strftime("%Y-%m-%d")
    out_dir = Path("data/processed/monitoring/tech_health")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    with open(out_dir / f"{date_str}.jsonl", 'w') as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    
    # Alert on failures
    for r in results:
        failed = [k for k, v in r['checks'].items() if not v]
        if failed:
            send_alert(f"Tech Health FAIL: {r['url']} — {', '.join(failed)}")
```

### 2. `scripts/monitoring/drift_monitor.py`
```python
#!/usr/bin/env python3
"""
SEO Drift Monitor — сравнивает текущие SEO-элементы с baseline
Baseline хранится в data/baseline/seo_elements.json
"""
import json
from pathlib import Path
from datetime import datetime

BASELINE_FILE = Path("data/baseline/seo_elements.json")
CURRENT_FILE = Path("data/processed/monitoring/drift_latest.json")
REPORT_DIR = Path("brain/wiki/audits/monitoring/drift")
REPORT_DIR.mkdir(parents=True, exist_ok=True)

def load_jsonl(file):
    data = {}
    with open(file) as f:
        for line in f:
            r = json.loads(line)
            data[r['url']] = r
    return data

def compare(baseline, current):
    drift = {}
    for url, base in baseline.items():
        if url not in current:
            drift[url] = {"status": "missing", "details": "Page not found in current crawl"}
            continue
        
        cur = current[url]
        changes = {}
        for field in ['title', 'h1', 'meta_description', 'canonical', 'schema_types', 'word_count']:
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

def main():
    baseline = load_jsonl(BASELINE_FILE)
    current = load_jsonl(CURRENT_FILE)
    drift = compare(baseline, current)
    
    # Report
    date_str = datetime.now().strftime("%Y-%m-%d")
    report = {
        "date": date_str,
        "baseline_date": "2026-09-10",  # обновить после первого baseline
        "total_pages_baseline": len(baseline),
        "total_pages_current": len(current),
        "changed_pages": len([d for d in drift.values() if d['status'] == 'changed']),
        "new_pages": len([d for d in drift.values() if d['status'] == 'new']),
        "missing_pages": len([d for d in drift.values() if d['status'] == 'missing']),
        "drift_details": drift
    }
    
    with open(REPORT_DIR / f"drift_report_{date_str}.json", 'w') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # Markdown summary
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
    
    # Alert if critical changes
    critical_changes = [u for u, d in drift.items() 
                       if d['status'] == 'changed' and 
                       any(f in d['changes'] for f in ['canonical', 'h1', 'meta_description', 'schema_types'])]
    if critical_changes:
        send_alert(f"CRITICAL SEO DRIFT: {len(critical_changes)} pages with canonical/H1/meta/schema changes")
```

### 3. `scripts/monitoring/geo_tracker.py`
```python
#!/usr/bin/env python3
"""
GEO Tracking — измерение AI visibility
Использует: GA4 (AI traffic channel), брендовые упоминания, citability score
"""
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from pathlib import Path

# Промпты для проверки брендовых упоминаний
BRAND_PROMPTS = [
    "Какие типографии в Ижевске печатают визитки быстро?",
    "Где заказать баннеры в Ижевске?",
    "Лучшая типография для мерча в Удмуртии",
    "Цифра типография Ижевск отзывы",
    "Стоимость печати листовок в Ижевске",
]

AI_ENDPOINTS = {
    "chatgpt": "https://api.openai.com/v1/chat/completions",  # требует ключ
    "perplexity": "https://api.perplexity.ai/chat/completions",  # требует ключ
    # Бесплатные: ручной запуск через браузер или сервисы вроде otter.ai
}

async def check_brand_mentions():
    """Ручной/полуавтомат: запускать промпты, парсить ответы"""
    # Для автоматизации нужен доступ к API или browser automation
    # MVP: ручной запуск раз в неделю, сохранение в JSON
    pass

def calculate_citability_score(page_data):
    """5-пилярный скор (0-100) по geo-visibility skill"""
    score = 0
    # Answer-first passages
    if page_data.get('has_answer_first'): score += 20
    # Stats & quotes
    if page_data.get('stats_count', 0) >= 2: score += 20
    # Tables & lists
    if page_data.get('has_tables') or page_data.get('has_lists'): score += 20
    # Question headings
    if page_data.get('question_headings', 0) >= 3: score += 20
    # E-E-A-T
    if page_data.get('has_author') and page_data.get('has_date_modified'): score += 20
    return score

def main():
    # 1. Загрузить GA4 AI traffic (через API или ручной экспорт)
    # 2. Проверить брендовые упоминания (ручной/API)
    # 3. Посчитать citability score для топ-20 страниц
    # 4. Сохранить отчёт
    pass
```

### 4. `scripts/monitoring/rankings_pull.py`
```python
#!/usr/bin/env python3
"""
Daily Rankings Pull из Топвизор API v2
Сохраняет историю позиций для трендов
"""
import os
import requests
import json
from datetime import datetime
from pathlib import Path

API_KEY = os.getenv("TOPVISOR_API_KEY")
PROJECT_ID = os.getenv("TOPVISOR_PROJECT_ID")
BASE_URL = "https://api.topvisor.com/v2/json"

def get_positions():
    params = {
        "project_id": PROJECT_ID,
        "fields": "keyword,position,position_prev,url,volume,top,serp_features",
        "limit": 1000
    }
    headers = {"Authorization": f"Bearer {API_KEY}"}
    resp = requests.post(f"{BASE_URL}/getKeywords_2", json=params, headers=headers)
    return resp.json()

def main():
    data = get_positions()
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    out_dir = Path("data/processed/monitoring/rankings")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    with open(out_dir / f"positions_{date_str}.json", 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # Анализ изменений
    # Сравнить с вчерашним файлом, найти рост/падение >3 позиций
    # Алерт если топ-10 ключей упало >5
```

### 5. `scripts/monitoring/log_analyzer.py`
```python
#!/usr/bin/env python3
"""
Server Log Analysis — crawl budget, боты, ошибки
Читает Nginx access.log (или Apache)
"""
import re
from collections import Counter
from pathlib import Path
from datetime import datetime, timedelta

LOG_FILE = Path("/var/log/nginx/access.log")  # путь на сервере
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
    # Nginx combined format
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
    since = datetime.now() - timedelta(days=1)
    stats = {"total": 0, "by_bot": Counter(), "by_status": Counter(), "top_urls": Counter(), "bot_top_urls": Counter()}
    
    with open(LOG_FILE) as f:
        for line in f:
            parsed = parse_log_line(line)
            if not parsed:
                continue
            # Фильтр по времени (упрощённо — последние N строк)
            stats["total"] += 1
            bot = identify_bot(parsed["ua"])
            stats["by_bot"][bot] += 1
            stats["by_status"][parsed["status"]] += 1
            stats["top_urls"][parsed["url"]] += 1
            if bot != "user":
                stats["bot_top_urls"][parsed["url"]] += 1
    
    # Сохранить отчёт
    date_str = datetime.now().strftime("%Y-%m-%d")
    out_dir = Path("data/processed/monitoring/logs")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    report = {
        "date": date_str,
        "total_requests": stats["total"],
        "by_bot": dict(stats["by_bot"]),
        "by_status": dict(stats["by_status"]),
        "top_20_urls": dict(stats["top_urls"].most_common(20)),
        "bot_top_20_urls": dict(stats["bot_top_urls"].most_common(20)),
        "crawl_budget_estimate": stats["by_bot"].get("Googlebot", 0) + stats["by_bot"].get("YandexBot", 0),
    }
    
    with open(out_dir / f"log_report_{date_str}.json", 'w') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # Алерты
    if stats["by_status"].get(500, 0) > 10:
        send_alert(f"High 5xx rate: {stats['by_status'][500]} errors in 24h")
    if stats["by_bot"].get("Googlebot", 0) < 100:
        send_alert("Low Googlebot crawl — check robots.txt, sitemap, server health")
```

---

## 🚨 Alerting (Telegram Bot)

```python
# scripts/monitoring/alerts.py
import os
import requests

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_alert(message: str, level: str = "warning"):
    emoji = {"critical": "🔴", "warning": "🟠", "info": "🔵"}.get(level, "⚪")
    text = f"{emoji} ЦИФРА18 SEO Monitor\n{message}"
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                  json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"})

# Уровни алертов:
# 🔴 CRITICAL: sitemap 404, canonical пропал, хак, 5xx > 50, Googlebot crawl < 50
# 🟠 WARNING: meta desc изменилась, H1 изменился, схема сломалась, позиция топ-10 упала >5
# 🔵 INFO: новая страница, новый бэклинк, брендовое упоминание в ИИ
```

---

## 📊 Дашборды и отчёты

### Еженедельный отчёт (Markdown → brain/wiki/audits/monitoring/weekly_YYYY-MM-DD.md)
```markdown
# Weekly SEO/GEO Monitor — Week of YYYY-MM-DD

## 📈 Traffic & Rankings
- Органический трафик (Метрика): X (+Y% WoW)
- Топвизор видимость: X% (+Y%)
- Топ-10 ключей: X (изменение: +Y/-Z)
- Новые ключи в топе: N

## 🤖 GEO / AI Visibility
- GA4 AI Traffic: X сессий (+Y%)
- Брендовые упоминания (ChatGPT/Perplexity/Яндекс): X новых
- Citability score (топ-20): средний XX/100

## 🔧 Technical Health
- Drift alerts: N (критичных: X)
- Sitemap: OK / ISSUES
- Canonical coverage: XX%
- Schema coverage: XX%
- Core Web Vitals (sample): LCP/INP/CLS

## 📝 Content
- Новых статей на WP: N
- Обновлено старых: N
- Программатик страниц добавлено: N
- Индексация новых: X% за неделю

## 🚨 Action Items
1. [ ] Исправить drift на страницах X, Y, Z
2. [ ] Добавить схему на страницу Z
3. [ ] Проверить падение позиций по ключу K
```

### Ежемесячный отчёт (seo-report skill format)
- Полный Template A + B
- ROI расчёт (лиды из органики × средний чек)
- План следующего месяца

---

## 🗄 Baseline Management

### Baseline Capture (один раз после Phase 0 fixes)
```bash
# 1. Запустить полный аудит
python3 .config/opencode/skills/seo-geo-audit/scripts/seo_audit.py https://xn--18-6kc5a3bxam.xn--p1ai [money pages...]

# 2. Запустить drift_monitor.py в режиме baseline
python3 scripts/monitoring/drift_monitor.py --mode baseline

# 3. Сохранить baseline
cp data/processed/monitoring/drift_latest.json data/baseline/seo_elements.json
```

### Baseline Update Policy
- **Auto-update:** Новые страницы добавляются в baseline автоматически
- **Manual review:** Изменения в canonical/H1/meta/schema — требуют ручного подтверждения перед обновлением baseline
- **Quarterly:** Полная перебазировка после крупных релизов

---

## 📁 Структура данных

```
data/
├── baseline/
│   ├── seo_elements.json          # Baseline для drift monitor
│   ├── geo_scores.json            # Baseline GEO scores
│   └── rankings_snapshot.json     # Baseline rankings
├── processed/monitoring/
│   ├── tech_health/YYYY-MM-DD.jsonl
│   ├── drift/YYYY-MM-DD.jsonl
│   ├── rankings/positions_YYYY-MM-DD.json
│   └── logs/log_report_YYYY-MM-DD.json
└── exports/
    ├── metrica/YYYY-MM-DD/
    └── topvisor/YYYY-MM-DD/

brain/wiki/audits/monitoring/
├── INDEX.md
├── weekly_YYYY-MM-DD.md
├── monthly_YYYY-MM.md
├── drift_report_YYYY-MM-DD.md
├── geo_report_YYYY-MM-DD.md
└── tech_health_report_YYYY-MM-DD.md
```

---

## 🚀 Deployment (на сервере мониторинга)

### Systemd Timers (рекомендуется вместо cron)
```ini
# /etc/systemd/system/cifra18-tech-health.service
[Unit]
Description=Cifra18 Tech Health Check
[Service]
Type=oneshot
WorkingDirectory=/opt/cifra18-monitoring
ExecStart=/opt/cifra18-monitoring/.venv/bin/python scripts/monitoring/tech_health.py
EnvironmentFile=/opt/cifra18-monitoring/.env

# /etc/systemd/system/cifra18-tech-health.timer
[Unit]
Description=Daily Tech Health Check
[Timer]
OnCalendar=*-*-* 03:00:00
Persistent=true
[Install]
WantedBy=timers.target
```

Аналогично для остальных скриптов.

### Docker Compose (альтернатива)
```yaml
# docker-compose.monitoring.yml
services:
  monitoring:
    build: .
    volumes:
      - ./data:/app/data
      - ./brain/wiki/audits:/app/brain/wiki/audits
      - /var/log/nginx:/var/log/nginx:ro
    environment:
      - TOPVISOR_API_KEY=${TOPVISOR_API_KEY}
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID}
    # Запуск через cron внутри контейнера или systemd снаружи
```

---

## 🔑 Переменные окружения (.env)

```env
# Топвизор
TOPVISOR_API_KEY=xxx
TOPVISOR_PROJECT_ID=xxx

# Яндекс.Метрика
METRIKA_COUNTER_ID=50863157
METRIKA_API_TOKEN=xxx

# GA4
GA4_PROPERTY_ID=xxx
GA4_SERVICE_ACCOUNT_JSON=/path/to/sa.json

# Telegram
TELEGRAM_BOT_TOKEN=xxx
TELEGRAM_CHAT_ID=xxx

# Сервер
LOG_PATH=/var/log/nginx/access.log
```

---

## ✅ Чек-лист запуска мониторинга

- [ ] Настроен сервер/контейнер для мониторинга
- [ ] Установлены Python зависимости (aiohttp, beautifulsoup4, requests, pandas, duckdb)
- [ ] Созданы .env с ключами API
- [ ] Запущен baseline capture (после Phase 0 fixes)
- [ ] Настроены systemd timers / cron
- [ ] Telegram бот создан, чат ID получен, тест алерта пройден
- [ ] Первые 3 ежедневных отчёта получены и проверены
- [ ] Настроен еженедельный ревью (понедельник 10:00)
- [ ] Документировано в brain/wiki/audits/monitoring/INDEX.md

---

*Мониторинг — это страховка. Настройка займёт 1-2 дня, а сэкономит недели поиска причин падений.*