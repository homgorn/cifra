# Project: ЦИФРА18 — SEO + GEO Promotion

## Суть
Комплексное SEO/GEO продвижение типографии «Цифра» (Ижевск). Цель: x3-5 органического трафика за 6-9 месяцев, рост заявок и продаж. Домен: cifra18.рф (punycode xn--18-6kc5a3bxam.xn--p1ai). CMS: 1С-Битрикс 23.300.

## Тип
hybrid (dev + content + automation + marketing)

## Домен
Полиграфия / широкоформатная печать / мерч / сувенирка / B2B локальный (Ижевск + Удмуртия) + B2C e-commerce элементы

## Метрика успеха
- Органический трафик: baseline TBD -> x3 (6м) -> x5 (12м)
- Небрендовые клики: x4 / x8
- Заявки из органики: x3 / x5
- AI visibility (brand mentions в ChatGPT/Perplexity/AIO): 0 -> Top-3 -> Top-1
- Страниц в индексе: 95% / 98%

## Стандарты
- Все измерения — факты из скриптов / GSC / Метрика, никаких догадок
- Один фикс в шаблоне Bitrix = исправление на сотнях страницах
- Контент: human-first, экспертный, факточекинг, анти-AI-slop (em-dash -> запятые)
- GEO: llms.txt, JSON-LD, AI bot access, citability score
- Качество: verification-before-completion на каждом тикете

## Скиллы (активные)
- cifra18-seo (project skill, см. .claude/skills/cifra18-seo/SKILL.md)
- Фаза 0: seo-technical, seo-schema-markup, seo-geo-audit
- Фаза 1: seo-keyword-research, seo-content-service-page, seo-content-collection-page, seo-content-product-page, seo-content-comparison-page, seo-internal-linking, seo-local
- Фаза 2: content-decomposer, content-factory, content-calendar, seo-content-blog, seo-content-brief, copywriter, writing-coach
- Фаза 3: geo-visibility, geo-tracking, seo-llms-txt, ai-seo, seo-robots-ai
- Фаза 4: seo-backlinks, cro, signup, onboarding, popups, emails, offers, ab-testing
- Analytics: analytics, attribution, seo-report, seo-gsc-*, seo-drift, seo-unlighthouse
- Strategy: product-marketing, business-analyst, financial-modeler, project-manager, marketing-plan, growth-hacker

## Статус
**Текущий этап:** Phase 0 — Foundation (аудит завершён: audit/AUDIT_REPORT.md, CLIENT_REPORT.md, сайт отчёта reports/cifra18-audit/ — 22 стр.)
**Следующий шаг:** Получить доступы (Яндекс.Вебмастер, Метрика, GA4, CRM; Google вне скоупа) и запустить Phase 0 фиксы: sitemap, canonical, meta description placeholder, H1 hierarchy, JSON-LD templates.
**Деплой отчёта:** Worker cifra18-audit-report готов к заливке (`python scripts/export/deploy_worker.py`, нужен CLOUDFLARE_API_TOKEN).

## SDD
Спеки: `specs/` (README + 001-webmaster-report done + 002-worker-deploy ready + 003-offline-vendor done).
Гейты перед done: `validate_report.py`, `smoke_wm_js.js`, `validate_worker.py`.
Правила отчёта клиенту: нейтральный тон (без имени, без 1-го лица), только Яндекс, sitemap = панель Вебмастера + legacy /shop/ под удаление.

## Структура папок
```
цифра 2025/2026/
├── CLAUDE.md                    # этот файл
├── .claude/skills/cifra18-seo/  # project skill
├── audit/
│   ├── SEED_DATA.md             # raw collector output
│   ├── AUDIT_REPORT.md          # Template A (technical)
│   └── AUDIT_REPORT_EMAIL.md    # Template B (plain language)
├── outputs/YYYY-MM-DD/          # результаты этапов
├── research/                    # keyword maps, competitor gaps
├── scripts/                     # кастомные скрипты
└── prompts/                     # шаблоны промптов для сабагентов
```

## Быстрые команды
- `gbrain query "цифра18"` — контекст из памяти
- `python3 .config/opencode/skills/seo-geo-audit/scripts/seo_audit.py https://xn--18-6kc5a3bxam.xn--p1ai ...` — перезапуск коллектора
- `npx skills find seo` — поиск дополнительных скиллов

## Важные напоминания
- Не начинать контент до закрытия 5 Blocking findings
- Все sitemap URLs в robots.txt сейчас 404 — приоритет #1
- meta description = "Description" на главной и блоге — приоритет #2
- 5 H1 на главной — приоритет #3
- Нет canonical / schema — приоритет #4-5
- Картинки: 3.4MB GIF, 11/15 >200KB — оптимизация обязательна
- Em-dash (—) везде — заменить на запятые (AI writing tell)