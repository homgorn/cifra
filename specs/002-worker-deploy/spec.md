# 002. Сборка и деплой Cloudflare Worker — spec

Статус: **ready** — сборка и валидация зелёные, деплой ждёт API-токен.

## Цель

Одна команда доводит сайт до продакшена: сборка воркера → валидация → заливка
в Cloudflare Worker `cifra18-audit-report`.

## Скоуп

- `build_report_worker.py`: относительные пути, автороуты всех страниц
  (`/x`, `/x.html`, `/pages/x.html`), проверка лимита 1 MiB.
- `validate_worker.py`: парсинг ROUTES/ASSETS, эмуляция роутинга (включая 404),
  проверка `<title>`, веса.
- `deploy_worker.py`: build → validate → PUT в Cloudflare API.
  Токен и account только из окружения (`CLOUDFLARE_API_TOKEN`,
  `CLOUDFLARE_ACCOUNT_ID`), в репозитории секретов нет.

## Вне скоупа

- Cloudflare Pages (деплоились раньше, текущий путь — Worker).
- Кастомный домен (после деплоя, в дашборде).

## Критерии приёмки

- [x] Сборка: 27 файлов, 70 роутов, 60.3% лимита
- [x] `validate_worker.py` PASSED (88 URL)
- [ ] `deploy_worker.py` с токеном → success, прод-URL отвечает 200
