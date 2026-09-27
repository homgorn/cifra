# Scripts Index — ЦИФРА18

**Last updated:** 2026-09-10

---

## 📁 Структура скриптов

```
scripts/
├── INDEX.md                      # Этот файл
├── audit/                        # Скрипты аудитов
│   ├── full_catalog_audit.py     # Аудит 300+ услуг (Bitrix каталог) ✅
│   ├── articles_audit.py         # Аудит 290 статей (Bitrix новости) ✅
│   ├── geo_baseline.py           # GEO baseline замеры (citability score) ✅
│   └── competitor_audit.py       # Аудит конкурентов (Топвизор + ручной) 🔄
├── monitoring/                   # Авто-аудит и мониторинг
│   ├── tech_health.py            # Daily: HTTP, robots, sitemap, SSL, CSP, headers ✅
│   ├── drift_monitor.py          # Daily: SEO drift (titles, H1, meta, canonical, schema) ✅
│   ├── rankings_pull.py          # Daily: Топвизор API позиции ✅
│   ├── log_analyzer.py           # Daily: Nginx access.log (crawl budget, боты, ошибки) ✅
│   ├── geo_tracker.py            # Weekly: AI visibility, brand mentions, citability ✅
│   ├── content_inventory.py      # Weekly: новые/изменённые страницы, word count, schema ✅
│   ├── alerts.py                 # Telegram/Email алерты ✅
│   └── full_audit.py             # Monthly: полный seo-geo-audit ✅
├── export/                       # Экспорт данных из источников
│   ├── metrica_api_export.py     # Яндекс.Метрика Reporting API / Logs API 🔄
│   ├── topvisor_api_export.py    # Топвизор API v2 🔄
│   ├── bitrix_catalog_export.py  # Битрикс: каталог, статьи, SEO шаблоны 🔄
│   ├── gsc_api_export.py         # Google Search Console API (когда доступ) 🔄
│   ├── yw_api_export.py          # Яндекс.Вебмастер API 🔄
│   └── crm_export.py             # CRM (Битрикс24/amoCRM): лиды, сделки, ROI 🔄
├── content/                      # Контентная фабрика
│   ├── wp_import_prepare.py      # Подготовка CSV для WP All Import (статьи + каталог) ✅
│   ├── redirect_map_generator.py # 301 редиректы Bitrix → WP ✅
│   ├── content_quality_gate.py   # Pre-publish QA (seo-helpful-content + GEO) ✅
│   ├── entity_extractor.py       # Извлечение сущностей (spaCy + правила) ✅
│   ├── articles_optimizer.py     # Проверка черновика под GEO/SEO чек-лист 🔄
│   ├── programmatic_generators/  # Генераторы программатик страниц
│   │   ├── service_city.py       # Service × City страницы 🔄
│   │   ├── comparisons.py        # X vs Y, Alternatives 🔄
│   │   ├── materials.py          # Materials справочник 🔄
│   │   ├── glossary.py           # Glossary термины 🔄
│   │   └── faq_pages.py          # FAQ страницы 🔄
│   └── content_inventory.py      # Инвентаризация контента (weekly) ✅
├── dev-fixes/                    # Инструкции и фиксы для разработчика
│   ├── bitrix_phase0_fixes.md    # Phase 0: sitemap, canonical, meta desc, H1, JSON-LD ✅
│   ├── schema_templates/         # Готовые JSON-LD шаблоны для вставки
│   │   ├── organization.json     # Organization + LocalBusiness ✅
│   │   ├── product.json          # Product + Offer + AggregateRating ✅
│   │   ├── article.json          # Article + FAQPage + Speakable ✅
│   │   ├── breadcrumblist.json   # BreadcrumbList ✅
│   │   └── faq.json              # FAQPage ✅
│   ├── bitrix_component_patches/ # Патчи для компонентов Битрикса 🔄
│   └── wp_theme_setup/           # WP тема: ACF, CPT, таксономии, шаблоны 🔄
└── utils/                        # Утилиты
    ├── db.py                     # DuckDB/SQLite helpers 🔄
    ├── http_client.py            # Async HTTP клиент с retry/rate limit 🔄
    ├── schema_validator.py       # JSON-LD валидация (Rich Results Test API) 🔄
    ├── indexnow.py               # IndexNow API клиент 🔄
    └── telegram.py               # Telegram Bot уведомления 🔄
```

---

## 🚀 Quick Start

### Установка зависимостей
```bash
cd /Users/user/Projects/цифра\ 2025/2026
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### requirements.txt
```
aiohttp>=3.9
beautifulsoup4>=4.12
lxml>=5.0
pandas>=2.1
duckdb>=0.9
requests>=2.31
python-dotenv>=1.0
spacy>=3.7
ru_core_news_md>=3.7  # для entity_extractor
rich>=13.7  # красивый CLI output
pyyaml>=6.0
schedule>=1.2  # для простого шедулинга
```

Установка spaCy модели:
```bash
python -m spacy download ru_core_news_md
```

### Запуск аудитов (ручной)
```bash
# Аудит каталога (300+ услуг)
python scripts/audit/full_catalog_audit.py

# Аудит статей (290)
python scripts/audit/articles_audit.py

# GEO baseline для топ-20 страниц
python scripts/audit/geo_baseline.py

# Content Quality Gate на черновике
python scripts/content/content_quality_gate.py draft.html --keyword "визитки на крафте" --location "Ижевск"

# Entity Extractor на папке с черновиками
python scripts/content/entity_extractor.py drafts/ --update-wiki --min-count 2
```

### Запуск мониторинга (systemd timer рекомендуется)
```bash
# Ежедневные проверки
python scripts/monitoring/tech_health.py
python scripts/monitoring/drift_monitor.py
python scripts/monitoring/rankings_pull.py
python scripts/monitoring/log_analyzer.py

# Еженедельные
python scripts/monitoring/geo_tracker.py
python scripts/monitoring/content_inventory.py
```

### Экспорт данных
```bash
# Топвизор (ежедневно)
python scripts/export/topvisor_api_export.py

# Метрика (ежедневно/еженедельно)
python scripts/export/metrica_api_export.py

# Битрикс каталог (полный раз в неделю, инкремент ежедневно)
python scripts/export/bitrix_catalog_export.py --full
python scripts/export/bitrix_catalog_export.py --incremental
```

### WP Migration
```bash
# Подготовка CSV для WP All Import
python scripts/content/wp_import_prepare.py

# Генерация 301 редиректов
python scripts/content/redirect_map_generator.py
```

---

## 🔧 Конфигурация (.env)

```env
# Топвизор
TOPVISOR_API_KEY=your_key
TOPVISOR_PROJECT_ID=your_project_id

# Яндекс.Метрика
METRIKA_COUNTER_ID=50863157
METRIKA_API_TOKEN=your_token
METRIKA_LOGS_API_TOKEN=your_logs_token

# Google Search Console (когда доступ)
GSC_SERVICE_ACCOUNT_JSON=/path/to/service-account.json
GSC_PROPERTY_URL=https://xn--18-6kc5a3bxam.xn--p1ai/

# Яндекс.Вебмастер
YW_USER_ID=your_user_id
YW_API_KEY=your_key

# IndexNow
INDEXNOW_KEY=your_key
INDEXNOW_HOST=xn--18-6kc5a3bxam.xn--p1ai

# Telegram алерты
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# База данных
DUCKDB_PATH=data/processed/monitoring/monitoring.duckdb
```

---

## 📊 Output форматы

| Скрипт | Выходные файлы | Куда класть |
|---|---|---|
| `full_catalog_audit.py` | `brain/wiki/audits/full_service_audit_YYYY-MM-DD.md/.csv` | `brain/wiki/audits/` |
| `articles_audit.py` | `brain/wiki/audits/content_audit_290_YYYY-MM-DD.md/.csv` | `brain/wiki/audits/` |
| `geo_baseline.py` | `brain/wiki/audits/geo_baseline_YYYY-MM-DD.md/.json` | `brain/wiki/audits/` |
| `tech_health.py` | `data/processed/monitoring/tech_health/YYYY-MM-DD.jsonl` | `data/processed/monitoring/` |
| `drift_monitor.py` | `brain/wiki/audits/monitoring/drift_report_YYYY-MM-DD.md/.json` | `brain/wiki/audits/monitoring/` |
| `rankings_pull.py` | `data/processed/monitoring/rankings/positions_YYYY-MM-DD.json` | `data/processed/monitoring/` |
| `log_analyzer.py` | `data/processed/monitoring/logs/log_report_YYYY-MM-DD.json` | `data/processed/monitoring/` |
| `geo_tracker.py` | `brain/wiki/audits/monitoring/geo_report_YYYY-MM-DD.md/.json` | `brain/wiki/audits/monitoring/` |
| `content_quality_gate.py` | JSON report (stdout + --output) | CI/CD integration |
| `entity_extractor.py` | `brain/wiki/entities/{type}.md` + JSON | `brain/wiki/entities/` |
| `wp_import_prepare.py` | `data/exports/wp_import/wp_*.csv` | WP All Import |
| `redirect_map_generator.py` | `scripts/dev-fixes/redirects/redirects_nginx_*.conf` | Nginx config |
| `*_export.py` | `data/exports/{source}/YYYY-MM-DD/*.csv` | `data/exports/` |

---

## 🛠 Разработка новых скриптов

### Шаблон нового скрипта аудита
```python
#!/usr/bin/env python3
"""
Краткое описание: что делает скрипт
Запуск: python3 scripts/category/script_name.py
Результат: путь к выходным файлам
"""

import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime

# Константы
BASE_URL = "https://xn--18-6kc5a3bxam.xn--p1ai"
OUTPUT_DIR = Path("brain/wiki/audits/category")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

async def main():
    print(f"=== Script Name ===")
    print(f"Started: {datetime.now()}")
    
    # Логика...
    
    # Сохранение
    date_str = datetime.now().strftime("%Y-%m-%d")
    # ... запись файлов
    
    print(f"=== Completed: {datetime.now()} ===")

if __name__ == "__main__":
    asyncio.run(main())
```

### Правила
1. **Async first** — использовать `aiohttp` для HTTP, `asyncio.Semaphore` для rate limiting
2. **Structured output** — JSONL для стриминговых данных, JSON для отчётов, CSV для таблиц
3. **Error handling** — try/except, логирование ошибок, продолжение при частичных ошибках
4. **Progress reporting** — `rich` progress bars для долгих задач
5. **Config via .env** — никаких хардкодов ключей/путей
6. **Tests** — минимум smoke test: `python script.py --dry-run`

---

## 📅 Cron / Systemd Timers (Production)

### Systemd (рекомендуется)
```ini
# /etc/systemd/system/cifra18-tech-health.service
[Unit]
Description=Cifra18 Tech Health Check
After=network-online.target

[Service]
Type=oneshot
WorkingDirectory=/opt/cifra18
ExecStart=/opt/cifra18/.venv/bin/python scripts/monitoring/tech_health.py
EnvironmentFile=/opt/cifra18/.env
User=cifra18

# /etc/systemd/system/cifra18-tech-health.timer
[Unit]
Description=Daily Tech Health Check
[Timer]
OnCalendar=*-*-* 03:00:00
Persistent=true
[Install]
WantedBy=timers.target
```

Аналогично для: `drift_monitor`, `rankings_pull`, `log_analyzer` (daily), `geo_tracker`, `content_inventory` (weekly), `full_audit` (monthly).

### Logs
- Stdout/stderr → systemd journal (`journalctl -u cifra18-tech-health -f`)
- Structured logs → `data/logs/scripts/` (JSONL)

---

## 📋 Status Legend

| Symbol | Meaning |
|---|---|
| ✅ | Ready / Implemented |
| 🔄 | In Progress / Needs API access |
| 📝 | Planned / Stub |
| ❌ | Blocked |

---

*Все скрипты должны быть идемпотентными и безопасными для повторного запуска.*