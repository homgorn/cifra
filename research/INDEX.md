# Research Index — ЦИФРА18

**Last updated:** 2026-09-11

---

## 📁 Структура исследований

```
research/
├── INDEX.md                              # Этот файл
├── marketing_strategy.md                 # Маркетинговая стратегия (AARRR, каналы, бюджет)
├── content_strategy.md                   # Контент-стратегия (кластеры, план, GEO, SMM)
├── competitors/
│   ├── deep_analysis.md                  # Глубокий разбор конкурентов (локальные + федералы)
│   └── INDEX.md                          # Индекс конкурентных материалов
├── sdek_scaling_strategy.md              # SDEK интеграция + масштабирование на Россию
├── keywords/                             # Ключевые слова (после seo-keyword-research)
│   ├── INDEX.md
│   ├── keyword_map_full.csv
│   ├── keyword_map_by_cluster/
│   ├── paa_questions.md
│   ├── buyer_prompt_panel.md
│   └── cannibalization_report.md
├── content-gaps/                         # Пропуски контента
│   ├── INDEX.md
│   ├── money_pages_specs.md
│   ├── internal_linking_map.md
│   ├── content_calendar_Q2.xlsx
│   └── programmatic_templates_specs.md
├── entities/                             # См. brain/wiki/entities/INDEX.md
└── sme/                                  # Subject Matter Expertise
    ├── INDEX.md
    ├── printing_technologies.md
    ├── materials_science.md
    ├── postpress.md
    ├── equipment_specs.md
    ├── color_management.md
    └── file_preparation.md
```

---

## 🎯 Статус исследований

| Исследование | Статус | Файл |
|---|---|---|
| **Маркетинговая стратегия** | ✅ Готово | `marketing_strategy.md` |
| **Контент-стратегия** | ✅ Готово | `content_strategy.md` |
| **Конкурентный анализ (глубинный)** | ✅ Готово | `competitors/deep_analysis.md` |
| **SDEK + Россия масштабирование** | ✅ Готово | `sdek_scaling_strategy.md` |
| **Семантическое ядро** | ⏳ Ждет доступы | `keywords/` |
| **PAA Questions + Buyer Prompt Panel** | ⏳ Ждет ключи | `keywords/` |
| **Конкурентный аудит (Topvisor)** | ⏳ Ждет доступы | `competitors/` |
| **SERP Features анализ** | ⏳ Ждет доступы | `competitors/` |
| **Money Pages Specs** | ⏳ Ждет ключи | `content-gaps/` |
| **Internal Linking Map** | ⏳ Ждет страницы | `content-gaps/` |
| **Content Calendar Q2** | ⏳ Планируется | `content-gaps/` |
| **SME: Printing Technologies** | ⏳ Ждет интервью | `sme/` |
| **SME: Materials Science** | ⏳ Ждет интервью | `sme/` |
| **SME: Postpress** | ⏳ Ждет интервью | `sme/` |
| **SME: Equipment Specs** | ⏳ Ждет интервью | `sme/` |
| **SME: Color Management** | ⏳ Ждет интервью | `sme/` |
| **SME: File Preparation** | ⏳ Ждет интервью | `sme/` |

---

## 🔗 Связь с Brain Wiki

| Research Output | Brain Wiki Destination |
|---|---|
| Marketing Strategy | `brain/wiki/research/marketing_strategy.md` |
| Content Strategy | `brain/wiki/research/content_strategy.md` |
| Competitor Deep Analysis | `brain/wiki/research/competitors/deep_analysis.md` |
| SDEK Scaling Strategy | `brain/wiki/research/sdek_scaling_strategy.md` |
| Keyword Map | `research/keywords/keyword_map_full.csv` |
| Competitor Profiles | `research/competitors/` |
| SERP Features | `research/competitors/serp_analysis.md` |
| Money Pages Specs | `research/content-gaps/money_pages_specs.md` |
| Internal Linking Map | `research/content-gaps/internal_linking_map.md` |
| SME Docs | `research/sme/*.md` |

---

## 📊 Методология исследований

### Keyword Research (seo-keyword-research skill)
1. **Seeds:** Категории каталога + бренд + локация + проблемы клиентов
2. **Sources:** Топвизор (экспорт), Яндекс.Вебмастер (если доступ), Яндекс.Подсказки, Google PAA, конкурентские ключи
3. **Clustering:** SERP-based (seo-cluster skill) — по пересечению выдачи
4. **Intent Classification:** Informational / Commercial / Transactional / Navigational
5. **Output:** Keyword Map (CSV) + Intent Map + Buyer Prompt Panel (50-100)

### Competitor Analysis (competitive-analysis skill)
1. **Identify:** Топвизор авто-конкуренты + ручные (3-5 локальных + 5-10 федералов)
2. **Profile:** competitor-profiling skill для каждого
3. **Gaps:** Keyword gap, Content gap, Backlink gap, SERP feature gap
4. **Benchmark:** Страницы-лендинги конкурентов под топ-ключи

### Content Gaps (topic-cluster + seo-page-sections)
1. **Cluster Model:** Pillar + Satellites для каждой категории услуг
2. **Page Sections Audit:** seo-page-sections для топ-20 money pages
3. **Programmatic Opportunities:** Service×City, X vs Y, Materials, Glossary, FAQ

---

## 📅 План интервью SME (Subject Matter Experts)

| Эксперт | Тема | Вопросы | Формат вывода |
|---|---|---|---|
| **Главный технолог** | Printing Technologies | 20 вопросов по технологиям, отличия, когда что применять | `printing_technologies.md` |
| **Менеджер по материалам** | Materials Science | Свойства 20+ материалов, когда что рекомендовать | `materials_science.md` |
| **Постпечатник** | Postpress | Виды обработки, стоимость, сроки, ограничения | `postpress.md` |
| **Начальник производства** | Equipment Specs | Парк станков, макс. форматы, скорости, возможности | `equipment_specs.md` |
| **Препресс-менеджер** | Color Management + File Prep | RGB/CMYK, профили, требования к макетам по видам | `color_management.md` + `file_preparation.md` |

---

*Все исследования версионируются. Обновлять при новых данных.*