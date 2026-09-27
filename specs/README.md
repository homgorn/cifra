# SDD: разработка по спецификациям

Этот каталог — единый источник правды о том, **что** строится, **как** и **в каком статусе**.
Правило: никакой код без спеки, никакой деплой без зелёной валидации.

## Цикл

```
spec.md → plan.md → tasks.md → implement → validate → done
```

1. **spec.md** — что делаем и зачем: цель, скоуп, вне скоупа, требования, критерии приёмки.
2. **plan.md** — как делаем: архитектура/подход, чанки, файлы, риски.
3. **tasks.md** — чеклист задач со статусами (`[ ]` / `[x]`). Обновляется по ходу работы.
4. **implement** — скриптами там, где повторяемость важна (сборка данных, правки, деплой).
5. **validate** — гейты перед done: `validate_report.py`, `smoke_wm_js.js`, `validate_worker.py`.

## Спеки

| № | Спека | Статус |
|---|---|---|
| 001 | `001-webmaster-report/` — 10 страниц Вебмастера на сайте отчёта | done |
| 002 | `002-worker-deploy/` — сборка и деплой Cloudflare Worker | ready (ждёт токен) |
| 003 | `003-offline-vendor/` — офлайн-вендоринг Chart.js | done |
| 004 | `004-metrika-analytics/` — разбор выгрузок Метрики, вики, кросс с ВМ | done |
| 005 | `005-yandex-api/` — OAuth + рабочие экспорты API Метрики/Вебмастера | done (токен, 5+8 выгрузок, вики обновлены) |
| 006 | `006-homepage-mega/` — главная-витрина с живыми данными API | done |
| 007 | `007-datalens-dashboards/` — дашборды себе + витрина клиенту | done (заменён на 4 страницы дашбордов на JS) |
| 008 | `008-github/` — git, Pages, Actions-автообновление | done (Actions недоступен, деплой через gh-pages) |
| 009 | `009-metrica-counters/` — разделение счётчиков сайта и карточки, пересборка вики и отчёта | done |
| 010 | `010-serp-beta-export/` — годовые показы, клики и позиции через beta-инструмент Вебмастера | done |
| 011 | `011-verify-and-plan3m/` — проверка цифр, кластеризация запросов, план на 3 месяца, пакет Topvisor | done |

## Definition of Done (общий)

- [ ] `python scripts/export/validate_report.py` — PASSED
- [ ] `node scripts/export/smoke_wm_js.js` — SMOKE OK
- [ ] `python scripts/export/validate_worker.py` — PASSED (если менялись ассеты сайта)
- [ ] tasks.md спеки обновлён, сессия в `brain/wiki/sessions/` записана

## Связанные документы

- Сайт отчёта: `reports/cifra18-audit/` (вход `index.html`, 26 страниц)
- Аналитика: `brain/wiki/webmaster_analytics/` (12 MD + 22 CSV),
  `brain/wiki/metrika_analytics/` (8 MD + 10 CSV)
- Отчёт клиенту: `CLIENT_REPORT.md` и `CLIENT_REPORT.docx` (собирается скриптом)
- Данные, которых до сих пор нет: `research/data-needs-deep-research.md` (статусы)
