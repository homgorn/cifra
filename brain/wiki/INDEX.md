# Brain Wiki Index: ЦИФРА18 SEO+GEO Project

**Project:** Типография «Цифра» (цифра18.рф / xn--18-6kc5a3bxam.xn--p1ai)  
**Location:** `/Users/user/Projects/цифра 2025/2026/brain/wiki/`  
**Last updated:** 2026-10-04  
**Status:** Phase 0: Foundation (аудит завершён, стратегии созданы, скрипты готовы, ждём доступы)

---

## 📁 Структура Brain Wiki

```
brain/wiki/
├── INDEX.md # Этот файл - мастер-индекс
├── MASTER_PLAN.md                        # Единый план: 4 фазы, 6 месяцев, риски, бюджет, команда
├── audits/
│   ├── INDEX.md                          # Индекс всех аудитов
│   ├── SEED_DATA.md                      # Raw collector output (3 страницы)
│   ├── AUDIT_REPORT.md                   # Technical audit (Template A)
│   ├── AUDIT_REPORT_EMAIL.md             # Plain language audit (Template B)
│   ├── phase0_fixes.md                   # Трекинг Phase 0 исправлений
│   ├── full_service_audit.md             # Аудит 300+ услуг (план + результаты)
│   ├── content_audit_290.md              # Аудит 290 статей
│   ├── geo_baseline.md                   # GEO baseline замеры
│   ├── drift_baseline.md                 # SEO drift baseline
│   └── monitoring/
│       ├── INDEX.md
│       ├── weekly_YYYY-MM-DD.md
│       ├── monthly_YYYY-MM.md
│       ├── drift_report_YYYY-MM-DD.md
│       ├── geo_report_YYYY-MM-DD.md
│       └── tech_health_report_YYYY-MM-DD.md
├── skills/
│   ├── INDEX.md                          # Индекс используемых скиллов
│   ├── cifra18-seo.md                    # Project skill (ссылка на .claude/skills/cifra18-seo/SKILL.md)
│   ├── active_skills.md                  # Активные скиллы по фазам
│   ├── wp_subdomain_strategy.md          # WP поддомен: блог + программатик + GEO + портфолио
│   ├── content_optimization_290.md       # План оптимизации 290 статей
│   ├── smm_plan.md                       # SMM план (Дзен, ВК, Видео)
│   ├── monitoring_setup.md               # Авто-аудит и мониторинг
│   └── skills_analysis.md                # Анализ всех 200+ скиллов по фазам
├── entities/
│   ├── INDEX.md                          # Индекс сущностей + граф
│   ├── brand.md                          # Бренд: Цифра, ИП Данилов, НПП
│ ├── services.md # 300+ услуг - каталог + Россия масштабирование
│   ├── locations.md                      # Ижевск, Удмуртия, пригороды + РФ города
│   ├── competitors.md                    # Конкуренты (локальные + федералы)
│   ├── keywords.md                       # Семантическое ядро (после исследования)
│   ├── intent_map.md                     # Intent map по страницам
│   ├── materials.md                      # Материалы (бумага, пленка, ткань...)
│   ├── equipment.md                      # Оборудование (станки, возможности)
│   ├── standards.md                      # ГОСТ, ISO, тех. требования
│   └── industries.md                     # Индустрии клиентов (HoReCa, Риелторы...)
├── research/
│   ├── INDEX.md                          # Индекс исследований
│   ├── marketing_strategy.md             # Маркетинговая стратегия (AARRR, каналы, бюджет)
│   ├── content_strategy.md               # Контент-стратегия (кластеры, план, GEO, SMM)
│   ├── competitors/
│   │   ├── INDEX.md
│   │   ├── deep_analysis.md              # Глубокий разбор (Tier 1 Local + Tier 2 Federal)
│   │   └── federal/                      # Профили федеральных конкурентов
│   ├── sdek_scaling_strategy.md          # SDEK интеграция + масштабирование на Россию
│   ├── keywords/                         # Ключевые слова (после seo-keyword-research)
│   ├── competitors/                      # Профили конкурентов
│   ├── content-gaps/                     # Пропуски контента
│   └── sme/                              # Subject Matter Expertise
├── exports/
│   ├── INDEX.md                          # Индекс экспортов
│   ├── metrica_plan.md                   # План выгрузок Яндекс.Метрика
│   ├── topvisor_plan.md                  # План выгрузок Топвизор
│   └── bitrix_catalog.md                 # План экспорта каталога из Битрикса
├── scripts/
│   ├── INDEX.md                          # Индекс всех скриптов (14 готовых)
│   ├── audit/                            # Аудит 300+ услуг, 290 статей, GEO baseline
│   ├── monitoring/                       # Daily/weekly мониторинг (7 коллекторов)
│   ├── export/                           # API экспорты (Метрика, Топвизор, Битрикс, GSC, CRM)
│   ├── content/                          # Контентная фабрика (оптимизаторы, программатик, WP import)
│   ├── dev-fixes/                        # Инструкции для Bitrix/WP разработчика + JSON-LD шаблоны
│   └── utils/                            # Утилиты (DB, HTTP, Schema validator, IndexNow, Telegram)
├── prompts/
│   ├── INDEX.md                          # Индекс промптов
│   ├── subagents/                        # Промпты для сабагентов
│   ├── content/                          # Промпты контентной фабрики
│   ├── dev/                              # Промпты для разработчика
│   └── seo/                              # SEO промпты
├── landings/                            # Лендинги: 15 страниц, отчёты, сборка
│   ├── reports/                         # 00_START_HERE.md — статус и порядок работы
│   ├── _scrape/                         # Выкачка каталога, генераторы, покрытие
│   ├── build_all.py                     # Сборка всех лендингов одной командой
│   └── validate_landing.py              # 27 гейтов собранного лендинга
└── session_checkpoints/                  # Чекпоинты сессий
```

---

## 🔗 Быстрые ссылки на ключевые файлы

| Категория | Файл | Описание | Статус |
|---|---|---|---|
| **Аудит** | `audits/AUDIT_REPORT.md` | Technical audit (Template A) | ✅ Готов |
| | `audits/AUDIT_REPORT_EMAIL.md` | Plain language audit (Template B) | ✅ Готов |
| | `audits/SEED_DATA.md` | Raw collector data | ✅ Готов |
| **Стратегии** | `research/marketing_strategy.md` | AARRR, каналы, бюджет, ICP | ✅ Готов |
| | `research/content_strategy.md` | Кластеры, план, GEO, SMM | ✅ Готов |
| | `research/competitors/deep_analysis.md` | Tier 1 Local + Tier 2 Federal | ✅ Готов |
| | `research/sdek_scaling_strategy.md` | SDEK API + Россия масштабирование | ✅ Готов |
| **План** | `MASTER_PLAN.md` | 4 фазы, 6 мес, риски, бюджет | ✅ Готов |
| **Скиллы** | `skills/cifra18-seo.md` | Main project skill (50+ скиллов) | ✅ Готов |
| | `skills/wp_subdomain_strategy.md` | WP поддомен архитектура | ✅ Готов |
| | `skills/content_optimization_290.md` | 290 статей оптимизация | ✅ Готов |
| | `skills/smm_plan.md` | Дзен, ВК, Shorts/Клипы | ✅ Готов |
| | `skills/monitoring_setup.md` | 7 коллекторов + алерты | ✅ Готов |
| | `skills/skills_analysis.md` | 200+ скиллов по фазам | ✅ Готов |
| **Каталог** | `entities/services.md` | 300+ услуг + Россия SDEK | ✅ Готов |
| **Скрипты** | `scripts/audit/full_catalog_audit.py` | 300+ услуг аудит | ✅ Готов |
| | `scripts/audit/articles_audit.py` | 290 статей аудит | ✅ Готов |
| | `scripts/audit/geo_baseline.py` | GEO citability score | ✅ Готов |
| | `scripts/monitoring/*.py` | 7 коллекторов мониторинга | ✅ Готов |
| | `scripts/content/wp_import_prepare.py` | WP All Import CSV | ✅ Готов |
| | `scripts/content/redirect_map_generator.py` | 301 редиректы | ✅ Готов |
| | `scripts/content/content_quality_gate.py` | Pre-publish QA | ✅ Готов |
| | `scripts/content/entity_extractor.py` | Сущности для GEO | ✅ Готов |
| **Dev Fixes** | `scripts/dev-fixes/bitrix_phase0_fixes.md` | 5 Blocking fixes ТЗ | ✅ Готов |
| | `scripts/dev-fixes/schema_templates/*.json` | 5 JSON-LD шаблона | ✅ Готов |
| **Промпты** | `prompts/subagents/*.md` | Сабагенты (researcher, writer, reviewer) | ✅ Готов |
| | `prompts/content/geo_checklist.md` | 5-пилярный GEO QA | ✅ Готов |

---

## 🛒 Лендинги (состояние на 2026-10-04)

Собрано **15 лендингов**, все проходят 27 гейтов, покрыты все 88
подразделов каталога. Из 386 позиций каталога на страницах показано 221.
**Ни один лендинг не выложен**: нет доступа к сайту и не заполнен `.env`.

Читать отсюда: `landings/reports/00_START_HERE.md`, там статус, порядок
работы и список блокеров. Подробности по каждому решению:
`landings/reports/`, машиночитаемый вид: `landings/_scrape/category_specs.json`.

Порядок лендингов выбран по посещаемости из выгрузки Метрики `50863157`,
срез 2026-10-04: сувенирка 374, широкоформатка 204, визитки 175,
листовки 159, стенды 142, упаковка 127, наклейки 93, инженерная печать
67, календари 58. Абсолютные значения между группами не сопоставимы:
ключи перекрываются, поэтому на страницы не вынесено ни одной цифры
посещаемости.

Проверяется тремя командами, все три должны давать ноль:

| Команда | Что проверяет |
|---|---|
| `python landings/build_all.py` | пересобрать всё и прогнать гейты |
| `python landings/_scrape/coverage_report.py` | все ли подразделы каталога накрыты |
| `python scripts/export/scan_secrets.py` | нет ли секретов в отслеживаемых файлах |

Открытая утечка: сессионные токены клиента лежали в истории git до
2026-10-04 и уже были на GitHub. Файлы убраны из индекса, история не
переписана. Подробности: `landings/reports/09_SECRETS_LEAK_RAW_SCRAPE.md`.

## 📊 Метрики проекта (baseline: TBD после доступов)

| Метрика | Baseline | Target 6m | Target 12m |
|---|---|---|---|
| Органический трафик | TBD | ×3 | ×5 |
| Небрендовые клики | TBD | ×4 | ×8 |
| Заявки из органики | TBD | ×3 | ×5 |
| AI visibility (brand mentions) | 0 | Top-3 | Top-1 |
| Страниц в индексе | TBD | 95% | 98% |
| Core Web Vitals (mobile) | TBD | All green | All green |
| Russia orders (% of total) | 0% | 25% | 40% |

---

## 🎯 Текущий фокус (Phase 0: Week 1-2)

### Блокеры (нужно от владельца День 1)
- [ ] **Яндекс.Метрика**: доступ (ID 50863157)
- [ ] **Топвизор**: доступ / API ключ
- [ ] **Битрикс админка**: для Phase 0 fixes
- [ ] **CRM / Битрикс24**: лиды, сделки, ROI

### Параллельно (можно начать сразу)
- [x] Запустить `scripts/audit/full_catalog_audit.py` → 300+ услуг
- [x] Запустить `scripts/audit/articles_audit.py` → 290 статей
- [x] Запустить `scripts/audit/geo_baseline.py` → AI visibility baseline
- [ ] Передать разработчику `scripts/dev-fixes/bitrix_phase0_fixes.md`
- [ ] Настроить мониторинг: baseline capture после Phase 0

### Phase 0 Checklist
- [ ] B1: Sitemap 404 → 200 OK
- [ ] B2: Canonical на всех страницах
- [ ] B3: Meta description ≠ "Description"
- [ ] B4: 1 H1 на главной (вместо 5)
- [ ] B5: JSON-LD (Org, LocalBusiness, Product, Article, BreadcrumbList)
- [ ] GA4 + GSC + Яндекс.Вебмастер + Bing + IndexNow подключены
- [ ] Повторный seo-geo-audit → 0 Blocking findings

---

## 📅 Near-term Timeline

| Неделя | Фокус | Ключевые делитевераблы |
|---|---|---|
| **Week 1 (Sep 11-17)** | Phase 0 fixes + Access + Baseline audits | Fixed sitemap, canonical, meta, H1, schema; 300+ services audit CSV; 290 articles audit CSV; GEO baseline |
| **Week 2 (Sep 18-24)** | Phase 0 validation + Keyword Research start | Clean seo-geo-audit re-run; Keyword map v1; Intent map v1 |
| **Week 3 (Sep 25-Oct 1)** | Phase 1: Money pages + Local + Comparisons | 20+ service pages; Local SEO; Comparison cluster; Internal linking |
| **Week 4 (Oct 2-8)** | Phase 2 prep: WP subdomain setup | WP installed; ACF/CPT/Taxonomies; Theme ready |
| **Week 5-6** | Migration + Programmatic launch | 290 articles on WP; 301 redirects; 200+ programmatic pages |
| **Month 2+** | Content factory + GEO + Authority | 8-12 articles/month; GEO baseline; Link building; CRO tests |

---

## 📁 Output Structure Created

```
/Users/user/Projects/цифра 2025/2026/
├── CLAUDE.md
├── .claude/skills/cifra18-seo/SKILL.md
├── audit/
│   ├── SEED_DATA.md
│   ├── AUDIT_REPORT.md
│   └── AUDIT_REPORT_EMAIL.md
├── brain/wiki/
│   ├── INDEX.md (this file)
│   ├── MASTER_PLAN.md
│   ├── audits/
│   ├── skills/
│   ├── entities/
│   ├── research/
│   ├── exports/
│   ├── scripts/
│   ├── prompts/
│   └── session_checkpoints/
├── scripts/
│   ├── audit/ (3 scripts)
│   ├── monitoring/ (7 scripts)
│   ├── export/ (6 scripts)
│   ├── content/ (5 scripts)
│   ├── dev-fixes/ (1 MD + 5 JSON)
│   └── utils/ (5 scripts)
├── prompts/
│   ├── subagents/ (3)
│   ├── content/ (4)
│   ├── dev/ (2)
│   └── seo/ (4)
└── research/
    ├── marketing_strategy.md
    ├── content_strategy.md
    ├── competitors/deep_analysis.md
    └── sdek_scaling_strategy.md
```

---

## 🚀 Следующие действия (Immediate)

1. **Владелец:** Дать 4 доступа (Метрика, Топвизор, Битрикс, CRM)
2. **Dev:** Запустить Phase 0 fixes по `scripts/dev-fixes/bitrix_phase0_fixes.md`
3. **SEO Lead:** Запустить базовые аудиты:
   ```bash
   python3 scripts/audit/full_catalog_audit.py
   python3 scripts/audit/articles_audit.py
   python3 scripts/audit/geo_baseline.py
   ```
4. **После Phase 0:** Baseline мониторинга:
   ```bash
   python3 scripts/monitoring/drift_monitor.py --baseline
   python3 scripts/monitoring/tech_health.py
   ```

---

*Этот файл: точка входа в контекст проекта. Всегда читать первым при новой сессии.*