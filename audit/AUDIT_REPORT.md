# SEO + GEO Аудит: цифра18.рф (Типография «Цифра», Ижевск)

**Дата:** 2026-09-10  
**Методология:** seo-geo-audit skill (14 категорий чек-листа) + seo-audit skill  
**Вердикт:** Сайт требует фундаментальных исправлений перед масштабированием контента. 5 блокирующих находок (Blocking), 12 высокоприоритетных (Fix), 8 быстрых выигрышей.

---

## 📊 Executive Summary

| Метрика | Значение | Статус |
|---|---|---|
| **Indexation foundation** | Sitemap 404, нет canonical, нет schema | 🔴 Blocking |
| **Meta basics** | meta description = "Description" (placeholder) на 2/3 страницах | 🔴 Blocking |
| **Heading structure** | 5 H1 на главной, H1-H1-H1-H1-H1 последовательно | 🔴 Blocking |
| **GEO readiness** | AI bots allowed, но контент в HTML есть — хорошо; llms.txt absent | 🟡 Fix |
| **Images** | 13 empty alt, 0 lazyload, 3.4MB GIF, 11/15 >200KB | 🟠 High |
| **Content depth** | Товарки — отличные (калькуляторы, описания); блог — 8 статей с 2021 | 🟠 High |
| **Local/NAP** | Реквизиты на /about/, Яндекс.Карты есть | 🟢 OK |
| **Competitors** | Не измерено (нужен доступ к GSC/Keys.so/Яндекс.Вебмастер) | ⚪ Unknown |

**Score (errors/pages ratio):** ~45 ошибок на 3 проверенные страницы = 15 ошибок/страницу.  
Одна ошибка в шаблоне (meta desc, canonical, schema) повторяется на сотнях страниц каталога. Один фикс в шаблоне Bitrix исправит всё сразу.

---

## 🔴 Blocking Findings (invalidates downstream work)

| # | Категория | Находка | Влияние | Fix |
|---|---|---|---|---|
| B1 | **4.3 Sitemap** | Все 23 sitemap в robots.txt возвращают 404 | GSC не может прочитать sitemap; краулинг случайный | В Bitrix: Настройки → SEO → Sitemap: включить генерацию, проверить /shop/sitemap*.xml пути |
| B2 | **4.8 Canonical** | Canonical absent на всех страницах | Дубликаты (www/non-www, trailing slash, параметры) не канонизируются | В шаблоне header.php: `<link rel="canonical" href="<?= $APPLICATION->GetCurPageParam() ?>">` |
| B3 | **2.2 Meta description** | Главная и /news/ имеют `content="Description"` (11 chars) | Google пишет свой сниппет; CTR падает | В настройках компонентов / шаблоне: прописать уникальные meta description |
| B4 | **2.3 Headings** | 5 H1 на главной подряд: H2 → H1 → H2 → H1 ×5 | Машина не понимает иерархию; AI passage retrieval ломается | Оставить один H1 («Типография Цифра — цифровая и широкоформатная печать в Ижевске»), остальные понизить до H2 |
| B5 | **4.12 JS rendering gate** | Контент в HTML есть (good), но нет JSON-LD schema | ChatGPT/Claude/Perplexity не видят структурированные данные | Добавить JSON-LD: Organization, LocalBusiness, Product, Article, BreadcrumbList |

---

## 🟠 High Priority Fixes

| # | Категория | Находка | Fix |
|---|---|---|---|
| H1 | **3.2 Images** | 11/15 проверенных изображений >200KB (до 3.45MB GIF) | Настроить Bitrix image resize: WebP/AVIF, quality 80, max 200KB. Включить lazyload для below-fold. |
| H2 | **3.1 Alt text** | 13 empty alt на главной, 5 на товаре, 5 на блоге | В компонентах каталога/новостей: `alt="<?= $arItem['NAME'] ?> — фото"`. Декоративным — `alt=""`. |
| H3 | **2.5 Placement matrix** | Ключи «печать визиток Ижевск», «широкоформатная печать Ижевск» не в H1/URL/first para | Составить keyword map (skill: seo-keyword-research) и прописать матрицу на 20+ money pages |
| H4 | **5.1 Architecture** | Один каталог на всё — нет dedicated pages под высокочастотники | Создать страницы-потомков: /poligrafiya/vizitki/izhevsk/, /shirokoformatnaya-pechat/bannery/izhevsk/ и т.д. |
| H5 | **5.5 Comparison pages** | Нет страниц «X vs Y», «альтернативы», «лучшие типографии Ижевск» | Построить кластер сравнений: «цифровая vs офсетная», «визитки на крафте vs дизайнерском», «roll-up vs х-баннер» |
| H6 | **8. Blog** | 8 статей, последние 2021-2022, темы узкие (тех. требования) | Контент-план: 2 статьи/мес под коммерческие запросы + 1 expert-статья (skill: content-decomposer) |
| H7 | **4.10 GSC/GA4** | Доступ не проверен, GA4 не видно в коде | Запросить доступ у владельца; установить GA4 + Search Console; настроить IndexNow (Bing) |
| H8 | **4.11 Bing + IndexNow** | Не настроено | Bing Webmaster Tools + IndexNow API — критично для AI visibility (ChatGPT использует Bing index) |
| H9 | **9. GEO: llms.txt** | Отсутствует | Создать llms.txt с перечислением ключевых страниц, услуг, цен, контактов |
| H10 | **13. Local** | Яндекс.Карты есть, но GBP health не проверен | Аудит Яндекс.Вебмастер + Яндекс.Карты: отзывы, фото, актуальность, категории |
| H11 | **12. Backlinks** | Не измерено | Экспорт ссылок из Яндекс.Вебмастер / GSC; разрыв с конкурентами |
| H12 | **6. Content volume** | Товарки 1300+ слов (хорошо), блог статьи ~800-1200 (но мало) | Расширить топ-10 товарок до 2000+ слов (FAQ, кейсы, таблицы сравнения) |

---

## 🟢 Quick Wins (low effort, immediate gain)

| # | Действие | Где | Время |
|---|---|---|---|
| Q1 | Заменить em-dash (—) на запятые во всём контенте | Шаблоны, новости, товары | 15 мин |
| Q2 | Добавить `loading="lazy"` для изображений ниже фолда | main-slider, catalog items, portfolio | 30 мин |
| Q3 | Прописать width/height на всех img (CLS fix) | Все компоненты | 1 ч |
| Q4 | og:image на всех страницах (уже есть на товаре, нет на главной/блоге) | Шаблоны | 30 мин |
| Q5 | Breadcrumbs JSON-LD (BreadcrumbList) | Каталог, статьи | 1 ч |
| Q6 | Organization + LocalBusiness JSON-LD на главной и /about/ | header / footer include | 1 ч |
| Q7 | Product JSON-LD с price, availability, aggregateRating | Карточки товаров | 2 ч |
| Q8 | Article JSON-LD на новостях | /news/ компонент | 1 ч |
| Q9 | Исправить title /news/ с «Новости» на «Новости и статьи — Типография Цифра Ижевск» | Настройки инфоблока | 5 мин |
| Q10 | Добавить `lastmod` в sitemap (когда заработает) | Настройки sitemap | 5 мин |

---

## 📋 Prioritized Action Plan (Phased)

### Phase 0: Foundation (Week 1-2) — MUST DO FIRST
1. **Fix sitemap generation** (B1) — Bitrix settings / cron
2. **Add canonical template-wide** (B2) — header.php
3. **Fix meta description placeholder** (B3) — компоненты catalog.section, news.list, main
4. **Restructure H1 hierarchy** (B4) — index.php шаблон
5. **Deploy JSON-LD templates** (B5) — Organization, LocalBusiness, BreadcrumbList, Product, Article
6. **GA4 + GSC + Bing Webmaster + IndexNow** (H7, H8) — настройка и верификация

### Phase 1: Technical + On-Page (Week 2-4)
7. Image optimization pipeline (H1, H2) — WebP, resize, lazyload, width/height
2. Keyword research + mapping (H3) — seo-keyword-research skill
3. Architecture audit: create local landing pages per service+city (H4) — seo-content-service-page
4. Comparison/alternatives pages cluster (H5) — seo-content-comparison-page
5. Internal linking overhaul (seo-internal-linking) — money pages, silo structure
6. Schema validation (seo-schema-markup) — Rich Results Test на всех типах страниц

### Phase 2: Content Scale (Month 2+)
7. Blog content plan: 24 статьи за 3 мес (H6) — content-decomposer + seo-content-blog
8. Expand top product pages to 2000+ words with FAQ, tables, cases (H12)
9. Portfolio case studies as SEO assets (seo-page-sections)
10. Local pages for surrounding towns (seo-local) — если есть спрос

### Phase 3: Authority + GEO (Month 3+)
11. Link building: каталоги, профили, партнеры, PR (seo-backlinks, public-relations)
12. GEO optimization: citability score, entity consistency (geo-visibility)
13. AI traffic measurement baseline (geo-tracking) — GA4 AI channel group
14. Ongoing: monthly SEO drift monitoring (seo-drift), quarterly audits

---

## 🎯 Skills Required for Full Execution

### Core SEO (from audit findings)
- `seo-technical` — crawl, indexation, speed, JS rendering, AI bot access, sitemap fix
- `seo-keyword-research` — keyword map, intent, cannibalization check, buyer prompt panel
- `seo-content-service-page` — wireframe для 7 категорий услуг + локальные лендинги
- `seo-content-product-page` — PDP optimization для 200+ товаров
- `seo-content-collection-page` — категорийные страницы (PLP) с SEO-блоком
- `seo-content-comparison-page` — «X vs Y», alternatives, best-for pages
- `seo-content-blog` — статьи под коммерческие + информационные запросы
- `seo-internal-linking` — money-page mapping, silos, anchor variation
- `seo-schema-markup` — JSON-LD для всех типов страниц
- `seo-local` — Яндекс.Карты, Google Business Profile, LocalBusiness schema
- `seo-backlinks` — профиль ссылок, gap analysis, токсичные
- `seo-drift` — мониторинг изменений SEO-элементов

### GEO / AI Visibility
- `geo-visibility` — passage-level citability, 5-pillar score, entity consistency
- `geo-tracking` — GA4 AI traffic, brand mentions, share of voice vs competitors
- `seo-llms-txt` — генерация и валидация llms.txt
- `ai-seo` — оптимизация под AI Overviews, ChatGPT, Perplexity
- `seo-geo-audit` — повторные аудиты с GEO-слоем

### Content Production
- `content-decomposer` — контент-пайплайн: темы, шаблоны, календарь, QA gates
- `content-factory` — потоковое производство статей/товарок
- `content-calendar` — editorial calendar с привязкой к сезонам/спросу
- `seo-content-brief` — брифы для копирайтеров с competitor scoring
- `copywriter` / `copywriting` — продающие тексты для лендингов, товарок, CTA
- `writing-coach` / `writing-beats` / `writing-shape` — качество текстов

### Conversion & Marketing
- `cro` — оптимизация форм заявки, калькуляторов, CTA
- `signup` / `onboarding` — воронка от лида до заказа
- `popups` / `paywalls` — exit-intent, lead capture
- `emails` / `newsletter-writer` — дрип-кампании после заявки
- `offers` / `pricing` — упаковка офферов, калькуляторы цен
- `ab-testing` — эксперименты с заголовками, формами, калькуляторами
- `marketing-plan` — комплексный план по AARRR
- `growth-hacker` — воронка, retention, viral loops

### Analytics & Measurement
- `analytics` — GA4/Yandex.Metrika setup, event tracking, UTM
- `attribution` — multi-touch, self-reported attribution
- `seo-report` — ежемесячные отчёты
- `seo-gsc-*` skills (overview, drops, opportunities, cannibalization, decay, new keywords, compare, brand vs nonbrand)

### Technical / Platform
- `cloudflare` / `wrangler` — если перенести на Cloudflare Workers/Pages для edge SEO
- `seo-unlighthouse` — массовый Lighthouse аудит всех URL
- `seo-page-sections` — блоковый аудит underperforming страниц
- `site-architecture` — пересмотр ИА, URL structure, навигация

### Business / Strategy
- `product-marketing` — ICP, positioning, messaging (создать в начале)
- `business-analyst` — анализ юнит-экономики типографии
- `financial-modeler` — ROI от SEO инвестиций
- `project-manager` / `task-decomposer` — управление исполнением

---

## 📁 Deliverables Structure (outputs/2026-09-10/)

```
audit/
  SEED_DATA.md              # raw collector output (this file)
  AUDIT_REPORT.md           # this report (Template A)
  AUDIT_REPORT_EMAIL.md     # Template B — plain language for owner
  KEYWORD_MAP.csv           # (to produce via seo-keyword-research)
  COMPETITOR_GAP.xlsx       # (to produce via competitive-analysis)
  CONTENT_PLAN.xlsx         # (to produce via content-decomposer)
  SCHEMA_TEMPLATES/         # JSON-LD templates per page type
  LLMS_TXT.md               # generated llms.txt
  GEO_BASELINE.json         # geo-visibility score per key page
```

---

## ⚠️ What Was NOT Verified (requires owner access)

| Item | Why it matters | How to get |
|---|---|---|
| GSC Indexation ratio | 300/4000 = fire; 3000/4000 = healthy | Owner: Settings → Users → add email |
| GA4 / Yandex.Metrika real traffic | Baseline for growth measurement | Owner: share access or screenshots |
| PageSpeed Mobile/Desktop | CWV tiebreaker; competitors may be faster | Owner: run pagespeed.web.dev on 5 key URLs |
| Backlink profile (Яндекс.Вебмастер / GSC Links) | Authority gap vs competitors | Owner: export from Webmaster Tools |
| Яндекс.Карты / GBP health | Local pack visibility, reviews | Owner: Яндекс.Бизнес доступ |
| Competitor keyword rankings | Benchmark for content plan | Keys.so / Serpstat / ручной сбор |
| Sales/CRM data (leads → deals) | True ROI, not just traffic | Owner: CRM export or Bitrix24 access |

---

## 🏁 Next Steps (Owner Actions)

1. **Дать доступ** к GSC, Яндекс.Вебмастер, Яндекс.Метрика, GA4 (если есть), CRM/лиды
2. **Запустить PageSpeed** на 5 URL: главная, /catalog/poligrafiya/vizitki/, /catalog/shirokoformatnaya-pechat/, /news/, /about/ — скрины в чат
3. **Подтвердить/опровергнуть** competitor list (собрать 3-5 конкурентов в Ижевске + федеральные)
4. **Согласовать Phase 0** — начать с исправления sitemap, canonical, meta desc, H1, JSON-LD
5. **Назначить ответственного** за контент (внутренний или агентство) — для Phase 2

---

*Report generated per seo-geo-audit skill methodology. All measured findings traceable to collector script output. Unverified items marked explicitly.*
