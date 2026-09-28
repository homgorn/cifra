# MASTER PLAN: ЦИФРА18 SEO+GEO Promotion
## Комплексный план продвижения типографии «Цифра» (Ижевск)

**Документ:** Единая точка управления проектом  
**Версия:** 1.0  
**Дата:** 2026-09-10  
**Статус:** Phase 0: Foundation (аудит завершён) 
**Обновляется:** еженедельно (понедельник)  

---

## 🎯 Цели проекта (North Star Metrics)

| Метрика | Baseline | Target 3m | Target 6m | Target 12m | Ответственный |
|---|---|---|---|---|---|
| **Органический трафик** | TBD (нужен GSC/Метрика) | +50% | ×3 | ×5 | SEO Lead |
| **Небрендовые клики** | TBD | +100% | ×4 | ×8 | SEO Lead |
| **Заявки из органики** | TBD | +50% | ×3 | ×5 | SEO + CRO |
| **AI Visibility (brand mentions)** | 0 | Top-10 в нише | Top-3 | Top-1 | GEO Lead |
| **Страниц в индексе** | TBD | 90% | 95% | 98% | Tech SEO |
| **Core Web Vitals (mobile)** | TBD | Все зелёные | Все зелёные | Все зелёные | Dev |
| **Конверсия лид→сделка** | TBD | +20% | +50% | ×2 | Sales + CRO |

---

## 📦 Фазы проекта (Roadmap)

### Phase 0: Foundation (Недели 1-2) 🔴 **ТЕКУЩАЯ**
**Цель:** Исправить критические технические ошибки, сделать сайт «читаемым» для поисковиков и ИИ

| # | Задача | Скилл | Исполнитель | Дедлайн | Статус | DoD |
|---|---|---|---|---|---|---|
| 0.1 | Починить sitemap (23 URL → 404) | seo-technical | Bitrix Dev | День 2 | ⏳ | sitemap.xml → 200 OK, валидный XML |
| 0.2 | Добавить canonical на все страницы | seo-technical | Bitrix Dev | День 1 | ⏳ | View Source: canonical на каждой стр. |
| 0.3 | Убрать meta description = "Description" | seo-technical | Bitrix Dev | День 2 | ⏳ | Уникальные meta desc на главной, кат., товарах, новостях |
| 0.4 | Исправить H1: 1 на главной вместо 5 | seo-technical | Bitrix Dev | День 1 | ⏳ | 1 H1 с главным ключом, остальные → H2 |
| 0.5 | Развернуть JSON-LD: Org, LocalBusiness, Product, Article, BreadcrumbList | seo-schema-markup | Bitrix Dev | День 4 | ⏳ | Rich Results Test: 0 ошибок для 5 типов |
| 0.6 | Подключить GA4 + GSC + Яндекс.Вебмастер + Bing + IndexNow | seo-technical / analytics | SEO Lead | День 3 | ⏳ | Данные текут, верификация пройдена |
| 0.7 | Получить доступы: Метрика, Топвизор, Битрикс, CRM | н/д | Владелец | День 1 | ⏳ | Все доступы получены |
| 0.8 | Запустить baseline мониторинга (drift, rankings, tech health) | monitoring_setup | SEO Lead | День 5 | ⏳ | Baseline captured, alerts working |
| 0.9 | Повторный seo-geo-audit после фиксов | seo-geo-audit | SEO Lead | День 7 | ⏳ | 0 Blocking findings |

**Блокеры:** Нужен доступ к Битрикс админке + разработчик (1-2 дня работы)

---

### Phase 1: Keywords + Architecture + On-Page (Недели 3-6)
**Цель:** Построить семантическое ядро, создать money pages, настроить внутреннюю перелинковку

| # | Задача | Скилл | Исполнитель | Дедлайн | Зависимости |
|---|---|---|---|---|---|
| 1.1 | Семантическое ядро: Ижевск + Удмуртия (клустеры, интент, PAA) | seo-keyword-research | SEO Lead | Неделя 3 | Phase 0 done |
| 1.2 | Карта ключей → URL (keyword mapping) + каннибализация | seo-keyword-research | SEO Lead | Неделя 3 | 1.1 |
| 1.3 | Buyer prompt panel для GEO (50-100 промптов) | seo-keyword-research | SEO Lead | Неделя 3 | 1.1 |
| 1.4 | Создать 20+ локальных лендингов (Услуга + Город) | seo-content-service-page | Content + Dev | Недели 3-5 | 1.2 |
| 1.5 | Оптимизация топ-50 товарок (PDP) | seo-content-product-page | Content | Недели 3-6 | 1.2 |
| 1.6 | Оптимизация PLP (категорий): SEO-блок, фасеты, пагинация | seo-content-collection-page | Content + Dev | Недели 4-5 | 1.2 |
| 1.7 | Кластер сравнений: X vs Y, Alternatives, Best-for | seo-content-comparison-page | Content | Недели 4-6 | 1.2 |
| 1.8 | Внутренняя перелинковка: money pages, silos, anchors | seo-internal-linking | SEO + Dev | Неделя 5 | 1.4-1.7 |
| 1.9 | Local SEO: Яндекс.Карты, GBP, LocalBusiness schema, отзывы | seo-local | SEO Lead | Неделя 4 | 0.5 |
| 1.10 | Schema валидация всех типов страниц | seo-schema-markup | Dev | Неделя 5 | 0.5 |

**Критерий перехода в Phase 2:** Топ-20 ключей в топ-20, 0 технических ошибок, схема валидна

---

### Phase 2: Content Scale + WP Subdomain (Месяц 2-3)
**Цель:** Запустить контент-фабрику, перенести блог на WP, программатик SEO

| # | Задача | Скилл | Исполнитель | Дедлайн | Зависимости |
|---|---|---|---|---|---|
| 2.1 | Настроить WP поддомен (blog.cifra18.рф) | wp_subdomain_strategy | WP Dev | Неделя 7 | Phase 1 started |
| 2.2 | Миграция 290 статей на WP + 301 редиректы | content_optimization_290 | SEO + WP Dev | Неделя 8 | 2.1 |
| 2.3 | GEO-аудит перенесенных статей + фиксы | geo-visibility | SEO Lead | Неделя 8 | 2.2 |
| 2.4 | Программатик: Materials (50), Glossary (100) | seo-programmatic | Content + WP Dev | Неделя 9 | 2.1 |
| 2.5 | Программатик: Service City (50), Comparisons (30) | seo-programmatic | Content + WP Dev | Неделя 10 | 2.1 |
| 2.6 | Переработка оставшихся 100+ статей (батчами по 20) | content_optimization_290 | Content | Недели 9-12 | 2.2 |
| 2.7 | Контент-план: 2 статьи/неделю + 1 программатик батч/месяц | content-decomposer / content-calendar | Content Lead | Неделя 8+ | 2.1 |
| 2.8 | SMM запуск: Дзен, ВК, Shorts/Клипы | smm_plan | SMM Manager | Неделя 8+ | 2.1 |

**Критерий перехода в Phase 3:** 50+ статей в месяц, WP стабилен, программатик 200+ страниц

---

### Phase 3: Authority + GEO + Conversion (Месяц 3-4)
**Цель:** Линкбилдинг, AI visibility, CRO, email-воронки

| # | Задача | Скилл | Исполнитель | Дедлайн |
|---|---|---|---|---|
| 3.1 | Backlink audit + токсичные ссылки | seo-backlinks | SEO Lead | Неделя 11 |
| 3.2 | Link building: каталоги, 2ГИС, Zoon, Авито Услуги, партнеры | seo-backlinks / directory-submissions | SEO + Outreach | Недели 11-14 |
| 3.3 | PR: кейсы в локальных СМИ, экспертные комментарии | public-relations | PR / SEO | Недели 11-16 |
| 3.4 | GEO optimization: citability score, llms.txt, entity consistency | geo-visibility / seo-llms-txt | GEO Lead | Недели 11-12 |
| 3.5 | AI traffic measurement baseline (GA4 AI channel) | geo-tracking | Analytics | Неделя 11 |
| 3.6 | CRO: тесты форм заявки, калькуляторов, CTA | cro / ab-testing | CRO + Dev | Недели 12-14 |
| 3.7 | Email-дрип кампании (welcome, расчёт, кейсы, отзывы) | emails / newsletter-writer | Marketing | Неделя 12 |
| 3.8 | Реферальная программа для B2B | viral-mechanic / referrals | Marketing | Неделя 13 |
| 3.9 | Offer packaging: калькуляторы, гарантии, скидки по объему | offers / pricing | Sales + Marketing | Неделя 12 |

---

### Phase 4: Scale & Automate (Месяц 4-6)
**Цель:** Автоматизация, масштабирование, entrant барьеры

| # | Задача | Скилл | Дедлайн |
|---|---|---|---|
| 4.1 | Авто-аудит и алертинг (drift, rankings, GEO, tech) | monitoring_setup | Неделя 14 |
| 4.2 | Программатик расширение: все города Удмуртии, все услуги | seo-programmatic | Месяц 5 |
| 4.3 | Контент-хаб: видео-курсы, чек-листы, калькуляторы как лид-магниты | free-tools / lead-magnets | Месяц 5 |
| 4.4 | Платный трафик (Яндекс.Директ, ВК Таргет) под SEO лендинги | ads | Месяц 5 |
| 4.5 | Атрибуция: multi-touch, self-reported | attribution | Месяц 5 |
| 4.6 | Финмодель SEO: ROI, CAC, LTV по каналам | financial-modeler | Месяц 4 |
| 4.7 | Quarterly business review + план следующего квартала | project-manager / marketing-plan | Конец месяца 3, 6, 9, 12 |

---

## 👥 Команда и роли (RACI)

| Роль | Имя | Контакт | Ответственность (R) | Участие (A/C/I) |
|---|---|---|---|---|
| **Project Owner** | Владелец / Директор | н/д | Бюджет, приоритеты, доступы | A: все |
| **SEO Lead** | н/д | н/д | Стратегия, аудиты, ключи, техническое SEO, GEO | R: Phase 0-4 |
| **Bitrix Developer** | н/д | н/д | Phase 0 fixes, каталог, калькуляторы, API | R: 0.1-0.5, 1.4-1.6, 1.8, 1.10 |
| **WP Developer** | н/д | н/д | Поддомен, миграция, программатик шаблоны | R: 2.1-2.5 |
| **Content Lead / Copywriter** | н/д | н/д | Статьи, товарки, кейсы, брифы, редактирование | R: 1.4-1.7, 2.2-2.7 |
| **SMM Manager** | н/д | н/д | Дзен, ВК, Shorts/Клипы, комьюнити | R: 2.8 |
| **CRO Specialist** | н/д | н/д | Тесты, воронки, формы, email-воронки | R: 3.6-3.8 |
| **Analytics / Data** | н/д | н/д | GA4, Метрика, Топвизор API, дашборды | R: 0.6, 3.5, 4.5 |
| **Outreach / PR** | н/д | н/д | Линкбилдинг, PR, партнерства | R: 3.1-3.3 |
| **Sales / CRM** | н/д | н/д | Лиды, сделки, ROI, рефералка | C: 3.6-3.8, I: все |

---

## 💰 Бюджет (оценка на 6 месяцев)

| Статья | Месяц 1 | Месяц 2 | Месяц 3 | Месяц 4-6 | Итого 6м |
|---|---|---|---|---|---|
| **SEO Lead (0.5-1 FTE)** | 80-120к | 80-120к | 80-120к | 80-120к | 480-720к |
| **Bitrix Dev (фиксы + поддержка)** | 40-60к | 20-30к | 10-20к | 10-20к | 80-130к |
| **WP Dev (поддомен + программатик)** | н/д | 60-80к | 40-60к | 20-30к | 120-170к |
| **Content (копирайтер + редактор)** | 30-50к | 60-80к | 80-100к | 80-100к | 250-330к |
| **SMM Manager (0.5 FTE)** | н/д | 25-35к | 25-35к | 25-35к | 75-105к |
| **CRO / Email / Ads** | н/д | 10-20к | 30-50к | 50-80к | 90-150к |
| **Tools (Топвизор, Ahrefs/Serpstat, плагины WP, хостинг)** | 10-15к | 10-15к | 10-15к | 10-15к | 40-60к |
| **PR / Outreach / Линкбилдинг** | н/д | 10-20к | 20-30к | 30-50к | 60-100к |
| **Резерв (15%)** | 24-35к | 35-50к | 40-60к | 45-70к | 144-215к |
| **ИТОГО / мес** | **184-290к** | **310-450к** | **335-510к** | **350-540к** | **1.3-1.8М руб** |

*Можно оптимизировать: внутренние сотрудники вместо аутсорса, поэтапный старт*

---

## 📋 Делтеверы (Artifacts) по фазам

| Фаза | Артефакт | Путь в Brain Wiki |
|---|---|---|
| **Phase 0** | Tech Fixes Report | `audits/phase0_fixes_report.md` |
| | Baseline Monitoring | `data/baseline/`, `audits/monitoring/drift_baseline.md` |
| **Phase 1** | Keyword Map (CSV/XLSX) | `research/keywords/keyword_map_YYYY-MM-DD.xlsx` |
| | Intent Map | `entities/intent_map.md` |
| | Money Pages Specs | `research/content-gaps/money_pages_specs.md` |
| | Internal Linking Map | `research/content-gaps/internal_linking_map.md` |
| **Phase 2** | WP Subdomain Launch Report | `audits/wp_launch_report.md` |
| | Content Audit 290 Results | `audits/content_audit_290_YYYY-MM-DD.md` |
| | Programmatic Templates | `scripts/content/programmatic_templates/` |
| | Content Calendar Q2 | `research/content-gaps/content_calendar_Q2.xlsx` |
| **Phase 3** | Backlink Profile Report | `audits/backlink_audit_YYYY-MM-DD.md` |
| | GEO Baseline Report | `audits/geo_baseline.md` |
| | CRO Test Results | `audits/cro_tests_YYYY-MM-DD.md` |
| | Email Sequences | `prompts/content/email_sequences/` |
| **Phase 4** | Monthly SEO Reports | `audits/monthly_YYYY-MM.md` |
| | Quarterly Business Review | `audits/qbr_Q{1-4}_2026.md` |
| | Financial Model | `research/financial_model_YYYY-MM-DD.xlsx` |

---

## ⚠️ Риски и митигация

| Риск | Вероятность | Влияние | Митигация |
|---|---|---|---|
| Нет доступа к GSC/GA4 (владелец не даёт) | Средняя | Высокое | Работать через Метрику + Топвизор + серверные логи; настроить IndexNow + Bing |
| Bitrix Dev недоступен / дорогой | Высокая | Критическое | Phase 0: минимальные правки (5 файлов); документация готова; можно нанять фрилансера на 2 дня |
| 290 статей: тонкий контент, много дублей | Высокая | Среднее | Жёсткий аудит → delete/merge/redirect; программатик заменяет тонкие страницы |
| WP поддомен тянет авторитет с основного | Низкая | Среднее | Жёсткая перелинковка, общий бренд, shared GA4, canonical где нужно |
| Конкуренты (федералы) непобедимы по высокочастотникам | Высокая | Среднее | Фокус на локальные + длинные хвосты + коммерческие + GEO (AI citations) |
| Сезонность (спад в январе/феврале) | 100% | Среднее | Планировать контент под сезоны (календари ноябрь, подарки декабрь) |
| Изменения алгоритмов (Core Update) | Средняя | Высокое | Diversified traffic (SEO + GEO + Direct + Referral + Social + Paid) |
| Команда не успевает (перегруз) | Высокая | Высокое | Автоматизация (скрипты, программатик), приоритизация ICE, saying no |

---

## 🔄 Процессы и ритуалы

| Ритуал | Частота | Участники | Артефакт |
|---|---|---|---|
| **Weekly Standup** | Понедельник 10:00 | Whole team | Обновлённый MASTER_PLAN.md, blockers |
| **SEO Review** | Среда 14:00 | SEO Lead + Dev | Drift report, rankings, tech health |
| **Content Review** | Пятница 11:00 | Content Lead + SEO | Брифы на неделю, QA готовых статей |
| **Monthly Business Review** | 1-е число месяца | Owner + SEO Lead + Sales | Monthly SEO Report + ROI |
| **Quarterly Business Review** | Конец квартала | Owner + All Leads | QBR + Next Quarter Plan |
| **Retro** | Раз в 2 недели | Whole team | Улучшения процесса → в skills/ |

---

## 📁 Brain Wiki: ключевые файлы для ежедневной работы

```
brain/wiki/
├── INDEX.md                    # ← НАЧИНАТЬ ОТСЮДА КАЖДУЮ СЕССИЮ
├── MASTER_PLAN.md              # ← Этот файл
├── skills/
│   ├── cifra18-seo.md          # Project skill
│   ├── wp_subdomain_strategy.md
│   ├── content_optimization_290.md
│   ├── smm_plan.md
│   └── monitoring_setup.md
├── audits/
│   ├── INDEX.md
│   ├── AUDIT_REPORT.md
│   ├── AUDIT_REPORT_EMAIL.md
│   ├── phase0_fixes.md
│   └── monitoring/
│       ├── INDEX.md
│       ├── weekly_YYYY-MM-DD.md
│       └── drift_report_YYYY-MM-DD.md
├── entities/
│   ├── INDEX.md
│   ├── services.md             # 300+ услуг (после экспорта)
│   ├── keywords.md             # Семантическое ядро
│   └── intent_map.md
├── research/
│   ├── keywords/
│   ├── competitors/
│   └── content-gaps/
├── exports/
│   ├── metrica_plan.md
│   ├── topvisor_plan.md
│   └── bitrix_catalog.md
└── scripts/
    ├── audit/
    ├── monitoring/
    ├── content/
    └── dev-fixes/
```

---

## 🚀 Следующие 3 действия (Immediate Next Steps)

1. **Владелец:** Дать доступы: Яндекс.Метрика, Топвизор, Битрикс админка, CRM (День 1)
2. **SEO Lead + Dev:** Запустить Phase 0 fixes параллельно (Дни 1-4): по инструкции `scripts/dev-fixes/bitrix_phase0_fixes.md`
3. **SEO Lead:** Запустить скрипты аудита каталога (300+) и статей (290) параллельно с фиксами (Дни 1-3)

---

## 📝 История изменений

| Дата | Версия | Изменения | Автор |
|---|---|---|---|
| 2026-09-10 | 1.0 | Создан на базе аудита seo-geo-audit | SEO Lead |

---

*Этот документ: единственный источник правды для проекта. Все изменения фиксируются здесь. При конфликте: приоритет у MASTER_PLAN.md.*