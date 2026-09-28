# Audits Index: ЦИФРА18

**Last updated:** 2026-09-10  
**Total audits:** 3 (baseline) + planned + scripts ready

---

## 📋 Список аудитов

| Дата | Тип | Файл | Статус | Ключевые находки |
|---|---|---|---|---|
| 2026-09-10 | SEO+GEO Full (seo-geo-audit skill) | `AUDIT_REPORT.md` | ✅ Готов | 5 Blocking, 12 High, 10 Quick wins |
| 2026-09-10 | Plain Language (Template B) | `AUDIT_REPORT_EMAIL.md` | ✅ Готов | Для владельца, без терминов |
| 2026-09-10 | Raw Collector Data | `SEED_DATA.md` | ✅ Готов | 3 страницы, collector output |
| н/д | Phase 0 Fixes Tracking | `phase0_fixes.md` | ⏳ План | Трекинг 5 Blocking fixes |
| н/д | Full Service Audit (300+) | `full_service_audit.md` | 🔄 Скрипт готов | Каталог целиком (`full_catalog_audit.py`) |
| н/д | Content Audit (290 articles) | `content_audit_290.md` | 🔄 Скрипт готов | 290 статей под ключи/интент (`articles_audit.py`) |
| н/д | GEO Baseline | `geo_baseline.md` | 🔄 Скрипт готов | AI visibility baseline (`geo_baseline.py`) |
| н/д | SEO Drift Baseline | `drift_baseline.md` | 🔄 Скрипт готов | SEO elements baseline (`drift_monitor.py --baseline`) |
| н/д | Content Quality Gate | `content_quality_report.md` | 🔄 Скрипт готов | Pre-publish QA (`content_quality_gate.py`) |
| н/д | Entity Extraction | `entities_extracted.md` | 🔄 Скрипт готов | Сущности для GEO (`entity_extractor.py`) |

---

## 🔴 Blocking Findings Summary (from 2026-09-10)

| ID | Finding | Category | Fix Location | Effort |
|---|---|---|---|---|
| B1 | Sitemap 404 (19 URL, проверено 2026-09-28) | Technical | Bitrix SEO settings | 30 min |
| B2 | No canonical tags | Technical | `header.php` template | 15 min |
| B3 | meta description = "Description" | On-page | Component templates | 1 hr |
| B4 | 5 H1 on homepage | On-page | `index.php` template | 30 min |
| B5 | No JSON-LD schema | Technical/GEO | Component templates | 2-4 hr |

---

## 📊 Monitoring Reports (в `audits/monitoring/`)

| Report | Frequency | Description | Script |
|---|---|---|---|
| `weekly_YYYY-MM-DD.md` | Weekly (Mon) | Traffic, rankings, GEO, technical health, content, action items | н/д |
| `monthly_YYYY-MM.md` | Monthly (1st) | Full Template A+B, ROI, next month plan | `full_audit.py` |
| `drift_report_YYYY-MM-DD.md` | Daily | SEO element changes (titles, H1, meta, canonical, schema) | `drift_monitor.py` |
| `geo_report_YYYY-MM-DD.md` | Weekly | AI visibility, brand mentions, citability score | `geo_tracker.py` |
| `tech_health_report_YYYY-MM-DD.md` | Daily | HTTP, robots, sitemap, SSL, CSP, headers, canonical, schema presence | `tech_health.py` |
| `content_inventory_YYYY-MM-DD.md` | Weekly | New/changed pages, word count, schema status | `content_inventory.py` |

---

## 🔧 Скрипты для аудитов (все готовы к запуску)

| Скрипт | Назначение | Путь | Запуск |
|---|---|---|---|
| `seo_audit.py` | Collector (seo-geo-audit skill) | `.config/opencode/skills/seo-geo-audit/scripts/` | `python3 .../seo_audit.py https://xn--18-6kc5a3bxam.xn--p1ai ...` |
| `full_catalog_audit.py` | Аудит 300+ услуг | `scripts/audit/` ✅ | `python3 scripts/audit/full_catalog_audit.py` |
| `articles_audit.py` | Аудит 290 статей | `scripts/audit/` ✅ | `python3 scripts/audit/articles_audit.py` |
| `geo_baseline.py` | GEO baseline замеры (5 pillars) | `scripts/audit/` ✅ | `python3 scripts/audit/geo_baseline.py` |
| `drift_monitor.py` | SEO drift monitoring | `scripts/monitoring/` ✅ | `python3 scripts/monitoring/drift_monitor.py` |
| `tech_health.py` | Daily technical health | `scripts/monitoring/` ✅ | `python3 scripts/monitoring/tech_health.py` |
| `rankings_pull.py` | Daily rankings (Топвизор API) | `scripts/monitoring/` ✅ | `python3 scripts/monitoring/rankings_pull.py` |
| `log_analyzer.py` | Daily server log analysis | `scripts/monitoring/` ✅ | `python3 scripts/monitoring/log_analyzer.py` |
| `geo_tracker.py` | Weekly GEO tracking | `scripts/monitoring/` ✅ | `python3 scripts/monitoring/geo_tracker.py` |
| `content_inventory.py` | Weekly content inventory | `scripts/monitoring/` ✅ | `python3 scripts/monitoring/content_inventory.py` |
| `content_quality_gate.py` | Pre-publish QA (SEO + GEO) | `scripts/content/` ✅ | `python3 scripts/content/content_quality_gate.py draft.html --keyword "..."` |
| `entity_extractor.py` | Entity extraction для GEO | `scripts/content/` ✅ | `python3 scripts/content/entity_extractor.py drafts/ --update-wiki` |

---

## 📈 План следующих аудитов

### Неделя 1 (после доступов)
- [ ] Повторный seo-geo-audit после Phase 0 фиксов
- [ ] Запуск `full_catalog_audit.py` → 300+ услуг
- [ ] Запуск `articles_audit.py` → 290 статей
- [ ] Запуск `geo_baseline.py` → AI visibility baseline на 20 страницах
- [ ] Запуск `drift_monitor.py --baseline` → capture titles, H1, canonical, schema
- [ ] Запуск `tech_health.py` → baseline технического здоровья

### Неделя 2
- [ ] Keyword research audit (seo-keyword-research skill)
- [ ] Competitor gap audit (competitive-analysis skill)
- [ ] Local audit: Яндекс.Карты, Google Business Profile (seo-local)
- [ ] Backlink audit (seo-backlinks + Яндекс.Вебмастер экспорт)
- [ ] Content Quality Gate на всех новых страницах Phase 1

### Ежемесячно
- [ ] SEO drift monitoring (daily auto via `drift_monitor.py`)
- [ ] GSC insights (seo-gsc-* skills: когда появится доступ)
- [ ] GEO tracking (weekly auto via `geo_tracker.py`)
- [ ] Full re-audit квартально (seo-geo-audit skill)

---

## 📝 Как добавлять новые аудиты

1. Сохранить отчёт в `audits/` с префиксом даты: `YYYY-MM-DD_type.md`
2. Обновить эту таблицу
3. Обновить мастер-индекс `brain/wiki/INDEX.md`
4. Запустить `scripts/utils/update_indexes.py` для перегенерации индексов (to create)

---

## 📁 Output Structure

```
audits/
├── INDEX.md                           # This file
├── SEED_DATA.md                       # Raw collector output
├── AUDIT_REPORT.md                    # Template A (technical)
├── AUDIT_REPORT_EMAIL.md              # Template B (plain language)
├── phase0_fixes.md                    # Phase 0 tracking
├── full_service_audit_YYYY-MM-DD.md   # Full catalog audit results
├── full_service_audit_YYYY-MM-DD.csv  # CSV export
├── content_audit_290_YYYY-MM-DD.md    # Articles audit results
├── content_audit_290_YYYY-MM-DD.csv   # CSV export
├── geo_baseline_YYYY-MM-DD.md         # GEO baseline report
├── geo_baseline_YYYY-MM-DD.json       # JSON export
├── drift_baseline_YYYY-MM-DD.md       # Drift baseline
├── content_quality_report_YYYY-MM-DD.json
├── entities_extracted_YYYY-MM-DD.json
└── monitoring/
    ├── INDEX.md
    ├── weekly_YYYY-MM-DD.md
    ├── monthly_YYYY-MM.md
    ├── drift_report_YYYY-MM-DD.md
    ├── geo_report_YYYY-MM-DD.md
    ├── tech_health_report_YYYY-MM-DD.md
    └── content_inventory_YYYY-MM-DD.md
```
Проверка пункта один и пункт два.
