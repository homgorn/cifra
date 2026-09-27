# Цифра18 — SEO + GEO аудит и продвижение

Аудит типографии «Цифра» (Ижевск, цифра18.рф): техника, контент, конкуренты,
Вебмастер, Метрика, GEO. Цель: x3–5 органики за 6–12 месяцев.

## Быстрый старт

```bat
rem Отчётный сайт локально (22 страницы, офлайн-графики)
cd reports\cifra18-audit
python -m http.server 8000
rem → http://localhost:8000/
```

```bash
# Проверки (всё должно быть зелёным)
python scripts/export/validate_report.py   # сайт: 40 графиков, 28 URL
python scripts/export/validate_worker.py   # воркер Cloudflare
node scripts/export/smoke_wm_js.js         # smoke графиков и таблиц
```

## Структура

| Папка | Что внутри |
|---|---|
| `reports/cifra18-audit/` | Отчётный сайт (22 html, Chart.js локально, данные из `js/*-data.js`) |
| `brain/wiki/` | Вики: `webmaster_analytics/`, `metrika_analytics/`, сессии, база знаний |
| `scripts/export/` | Конвейеры: парсинг, сборки данных, валидации, деплой |
| `specs/` | SDD-спеки (spec → plan → tasks), см. `specs/README.md` |
| `webmaster/`, `metrika/` | Сырые выгрузки из кабинетов (не трогать руками) |
| `topvisor/` | Позиции и ключи (API, `scripts/tv.py`) |
| `CLIENT_REPORT.md` | Отчёт для клиента |

## Секреты

Только в локальном `.env` (см. `.env.example`), в git не попадает.
Для API нужен `YANDEX_OAUTH_TOKEN` — получение: `yandex_setup.bat`
(без аргументов печатает ссылку авторизации).

## Деплой сайта

```bat
rem GitHub Pages (нужен remote origin + доступ на запись)
deploy_github_pages.bat
```

## SDD

Никакой код без спеки (`specs/`), никакой деплой без зелёной валидации.
