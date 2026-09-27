# Prompts Index — ЦИФРА18

**Last updated:** 2026-09-10

---

## 📁 Структура промптов

```
prompts/
├── INDEX.md                      # Этот файл
├── subagents/                    # Промпты для сабагентов (task tool)
│   ├── researcher.md             # Глубокое исследование темы
│   ├── content_writer.md         # Написание статей/товарок/кейсов
│   ├── code_reviewer.md          # Ревью кода/фиксов разработчика
│   ├── landing_builder.md        # Сборка лендингов (Next.js + Tailwind)
│   ├── startup_analyst.md        # Анализ стартапа/бизнеса
│   ├── vision_reader.md          # Распознавание скриншотов/диаграмм
│   ├── idea_polisher.md          # Доработка файлов идеи (SPEC/TECHSTACK/ROADMAP)
│   ├── investor_pack.md          # Инвесторский пакет документов
│   └── design_scout.md           # Поиск open design референсов
├── content/                      # Промпты для контентной фабрики
│   ├── article_brief_template.md # Шаблон брифа для копирайтера (seo-content-brief)
│   ├── geo_checklist.md          # 5-пилярный GEO чек-лист для QA
│   ├── rewrite_prompt.md         # Переработка существующей статьи под ключи/интент/GEO
│   ├── merge_prompt.md           # Объединение нескольких статей в одну
│   ├── programmatic_template_prompt.md # Шаблон для программатик генерации
│   ├── faq_generator_prompt.md   # Генерация FAQ из контента статьи
│   ├── comparison_table_prompt.md # Генерация таблиц сравнения
│   ├── case_study_prompt.md      # Написание кейса из сырых данных
│   ├── material_page_prompt.md   # Страница материала (справочник)
│   ├── glossary_entry_prompt.md  # Запись глоссария
│   └── email_sequence_prompts/   # Дрип-кампании
│       ├── welcome.md
│       ├── calculation_followup.md
│       ├── case_study_nurture.md
│       ├── review_request.md
│       └── reengagement.md
├── dev/                          # Промпты для разработчика
│   ├── bitrix_fix_prompt.md      # Инструкция для исправления Phase 0
│   ├── schema_injection_prompt.md # Как вставить JSON-LD в компоненты
│   ├── canonical_implementation.md # Canonical во всех шаблонах
│   ├── sitemap_generation_prompt.md # Настройка sitemap в Битриксе
│   ├── wp_theme_setup_prompt.md  # WP тема: ACF, CPT, таксономии
│   ├── wp_programmatic_templates.md # Программатик шаблоны WP
│   └── api_integration_prompt.md # Bitrix ↔ WP API интеграция
└── seo/                          # SEO-специфичные промпты
    ├── keyword_clustering_prompt.md    # Кластеризация ключей (SERP-based)
    ├── intent_classification_prompt.md # Классификация интента ключей
    ├── paa_extraction_prompt.md        # Извлечение People Also Ask
    ├── buyer_prompt_panel_prompt.md    # Генерация 50-100 промптов для GEO
    ├── content_gap_analysis_prompt.md  # Анализ пропусков по seo-page-sections
    ├── internal_linking_strategy_prompt.md # Стратегия перелинковки
    └── schema_mapping_prompt.md        # Маппинг страниц -> Schema.org типы
```

---

## 🎯 Промпты для сабагентов (Subagents)

### `researcher.md` — Глубокое исследование
```markdown
# Role: Senior Research Analyst
## Task: Исследовать тему {topic} для типографии «Цифра» (Ижевск)
## Context: B2B/B2C полиграфия, широкоформат, мерч, стенды. Локация: Ижевск + Удмуртия.
## Output: RESEARCH.md в brain/wiki/research/{topic}/ с источниками, цитатами, confidence scores.
## Process:
1. Декомпозиция вопроса (research-decomposer skill)
2. Multi-source поиск (Google, Яндекс, Топвизор, отраслевые источники, ГОСТ)
3. Синтез с оценкой достоверности (uncertainty-quantifier skill)
4. Извлечение сущностей (entity_extractor.py)
5. Сохранение в brain/wiki + обновление entities/
```

### `content_writer.md` — Написание контента
```markdown
# Role: Expert SEO Copywriter (полиграфия, производство)
## Task: Написать {article_type} по брифу {brief_path}
## Context: Бренд «Цифра», Ижевск. Тон: экспертный, конкретный, без воды. Анти-AI-slop.
## Input: Бриф (article_brief_template.md) + SME данные (research/sme/)
## Output: Готовый текст в Google Docs / Notion + SEO QA чек-лист (geo_checklist.md)
## Requirements:
- H2 = вопросы из PAA / buyer prompt panel
- Answer-first passages (40-60 слов)
- Минимум 1 таблица сравнения / список / инструкция
- 2+ цифры с источниками
- FAQ блок (3-5 вопросов) + FAQPage schema
- Внутренние ссылки на money pages Bitrix (анкоры = ключи)
- Zero em-dash (заменить на запятые)
- Word count per брифу
```

### `code_reviewer.md` — Ревью кода разработчика
```markdown
# Role: Senior Bitrix/Fullstack Developer
## Task: Проверить реализацию Phase 0 fixes от разработчика
## Input: PR/коммит / файлы из scripts/dev-fixes/
## Checks:
1. Sitemap: генерируется, 200 OK, валидный XML, в robots.txt правильные URLs
2. Canonical: на всех страницах, правильный URL, пагинация → на первую страницу
3. Meta description: нет placeholder "Description", уникальные, 120-160 chars
4. H1: ровно 1 на странице, содержит главный ключ, иерархия H1→H2→H3
5. JSON-LD: Organization, LocalBusiness, Product, Article, BreadcrumbList — валидны (Rich Results Test)
6. Performance: нет регрессий, lazyload, width/height на img, WebP
## Output: APPROVE / REQUEST CHANGES с конкретными комментариями к строкам
```

---

## 📝 Content Prompts — детали

### `article_brief_template.md` (seo-content-brief skill)
```markdown
# SEO Content Brief: {title}

## Target
- **URL:** {target_url}
- **Cluster:** {cluster_name}
- **Intent:** {Informational|Commercial|Transactional|Navigational}
- **Primary Keyword:** {kw} (volume: {vol}, difficulty: {diff})
- **LSI Keywords:** {list of 5-10}

## Competitor Benchmark
- **Top 3 URLs:** {url1}, {url2}, {url3}
- **Their word count:** {avg}
- **Their structure:** {H2 list}
- **Content gaps vs them:** {what they miss}

## Structure (H2 Outline)
1. {H2 as question} — answer-first passage
2. {H2 as question} — table/list
3. {H2 as question} — steps/process
4. {H2 as question} — mistakes to avoid
5. FAQ (3-5 questions)

## Requirements
- **Word count:** {min}-{max}
- **Tone:** Expert, conversational, no fluff
- **Author:** {Expert name + role + photo}
- **Images:** {count} photos from production (specs in brief)
- **Internal links:** 3-5 to Bitrix money pages (anchor = keyword)
- **External links:** 1-2 to ГОСТ/производители
- **Schema:** Article + FAQPage
- **GEO:** 5-pillar citability score target > 80

## Deadline: {date}
```

### `geo_checklist.md` (5-pillar GEO QA)
```markdown
# GEO Citability QA Checklist (5 Pillars)

## Проверка перед публикацией
- [ ] **Pillar 1: Answer-First** — Каждый H2 = вопрос, 1-й абзац = прямой ответ (40-60 слов)
- [ ] **Pillar 2: Stats & Quotes** — Минимум 2 цифры с источником (ГОСТ, внутренние данные, эксперт)
- [ ] **Pillar 3: Tables & Lists** — Минимум 1 таблица сравнения ИЛИ маркированный список ИЛИ нумерованная инструкция
- [ ] **Pillar 4: Question Headings** — Все H2/H3 формулируются как вопросы пользователя (PAA / buyer prompts)
- [ ] **Pillar 5: E-E-A-T** — Автор (имя, роль, фото), dateModified, ссылки на кейсы/производство, экспертные цитаты

## Technical SEO + Schema
- [ ] Article / BlogPosting JSON-LD (author, datePublished, dateModified, publisher, image)
- [ ] FAQPage JSON-LD (3-5 вопросов из FAQ блока)
- [ ] BreadcrumbList JSON-LD
- [ ] Canonical (self-referencing)
- [ ] Meta title (30-60 chars, keyword first)
- [ ] Meta description (120-160 chars, keyword, CTA)
- [ ] H1 = 1, содержит keyword + локация
- [ ] H2-H3 иерархия, нет пропусков уровней
- [ ] Images: alt = keyword + описание, WebP, <200KB, lazyload, width/height
- [ ] Internal links: 3-5 на money pages (Bitrix каталог), анкоры = ключи
- [ ] External links: 1-2 авторитетных (ГОСТ, ISO, производители)
- [ ] No em-dash (—), no en-dash (–) — replaced with commas
- [ ] Word count >= brief target

## Score Target: 80+/100
```

---

## 🔧 Dev Prompts — детали

### `bitrix_fix_prompt.md`
```markdown
# Задача для Bitrix разработчика: Phase 0 SEO Fixes

## Контекст
Сайт: https://xn--18-6kc5a3bxam.xn--p1ai (Типография «Цифра», Ижевск)
CMS: 1С-Битрикс 23.300, шаблон `/local/templates/cifra_new/`
Аудит: seo-geo-audit skill, 5 Blocking findings

## ТЗ (5 задач)

### 1. Sitemap (Приоритет: CRITICAL)
**Проблема:** В robots.txt 23 sitemap URLs — все 404.
**Решение:**
- Админка → Настройки → SEO → Карта сайта: включить, путь `/sitemap.xml` (не `/shop/`)
- Агент `CSitemap::Generate()`: активен, интервал 3600 сек
- Проверить права на запись в `/bitrix/sitemap/` или корень
- Запустить вручную для теста
- Обновить robots.txt: убрать `/shop/`, добавить реальные URLs

### 2. Canonical (Приоритет: CRITICAL)
**Проблема:** Нет canonical ни на одной странице.
**Решение:** В `header.php` внутри `<head>`:
```php
$canonicalUrl = $APPLICATION->GetCurPageParam('', ['PAGEN_1', 'SORT', 'ORDER', 'set_filter', 'clear_cache'], true);
$canonicalFull = 'https://' . $_SERVER['HTTP_HOST'] . $canonicalUrl;
```
Для пагинации (`?PAGEN_1=N`): canonical на страницу БЕЗ пагинации.

### 3. Meta Description (Приоритет: CRITICAL)
**Проблема:** Главная и /news/ имеют `content="Description"`.
**Решение:**
- Главная: `$APPLICATION->SetPageProperty("description", "Типография «Цифра» в Ижевске: цифровая и широкоформатная печать, сувенирка, мерч, стенды. Калькулятор онлайн. Сроки от 1 часа. Доставка по РФ.");`
- Каталог/товары: настройка компонентов — meta description из PREVIEW_TEXT/DETAIL_TEXT (первые 160 симв.)
- Новости: из PREVIEW_TEXT статьи
- Фолбэк в header.php: если пусто — генерировать из H1 + Title

### 4. H1 Hierarchy (Приоритет: CRITICAL)
**Проблема:** 5 H1 на главной подряд.
**Решение:** В `index.php` / включаемых областях:
- Оставить 1 H1: «Типография «Цифра» — цифровая и широкоформатная печать в Ижевске»
- Остальные понизить до H2
- Проверить компоненты `news.list`, `catalog.section.list` — у них H2, не H1

### 5. JSON-LD Schema (Приоритет: CRITICAL)
**Проблема:** Нет ни одной схемы.
**Решение:** Добавить в соответствующие шаблоны (см. `scripts/dev-fixes/schema_templates/`):
- `header.php` / `footer.php`: Organization + LocalBusiness + BreadcrumbList
- `catalog.section`: ItemList + CollectionPage
- `catalog.element`: Product + Offer + AggregateRating
- `news.detail`: Article / BlogPosting
- `about/`, `contacts/`: LocalBusiness + ContactPage

## Приёмка (Definition of Done)
- [ ] Sitemap.xml → 200 OK, валидный XML, в GSC/Яндекс.Вебмастер добавлен
- [ ] Canonical на всех страницах (проверить 10 случайных)
- [ ] Meta description уникальные, нет "Description" (проверить 10 случайных)
- [ ] H1 = 1 на каждой странице, на главной — с ключом
- [ ] Rich Results Test: 0 ошибок для 5 типов схем
- [ ] seo_audit.py проходит без Blocking findings
```

---

## 🔄 Использование промптов

| Промпт | Когда использовать | Сабагент |
|---|---|---|
| `researcher.md` | Новая тема для статьи, конкурент, технология | `researcher` |
| `content_writer.md` + `article_brief_template.md` | Написание новой статьи/товарки/кейса | `content-writer` |
| `rewrite_prompt.md` + `geo_checklist.md` | Переработка существующей статьи | `content-writer` |
| `merge_prompt.md` | Объединение 2+ тонких статей | `content-writer` |
| `code_reviewer.md` | Проверка PR от разработчика | `code-reviewer` |
| `bitrix_fix_prompt.md` | Отдача ТЗ разработчику | — (прямая передача) |
| `schema_injection_prompt.md` | Помощь деву вставке JSON-LD | — |
| `wp_theme_setup_prompt.md` | Настройка WP поддомена | `landing-builder` / прямая передача |
| `keyword_clustering_prompt.md` | Кластеризация семантического ядра | `researcher` |
| `buyer_prompt_panel_prompt.md` | Генерация GEO промптов | `researcher` |

---

## 📋 Version Control для промптов

- Все промпты версионируются в Git
- Изменения промптов → коммит с префиксом `prompt:`
- Тестирование: запуск через сабагента на тестовой задаче
- Обратная связь: `reflect` skill после использования

---

*Промпты — это код для LLM. Относиться к ним как к production коду: ревью, тесты, версионирование.*