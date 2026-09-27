# 002. Worker — plan

## Подход

Старый `build_report_worker.py` содержал захардкоженные Mac-пути и роуты только
10 legacy-страниц. Переписан с нуля: сканирование каталога, нормализация
слэшей (баг Windows: glob отдаёт `\`, роуты не собирались — поймано тестом).

## Артефакты

| Файл | Назначение |
|---|---|
| `scripts/export/build_report_worker.py` | Сборка `reports/cifra18-audit-worker.js` |
| `scripts/export/validate_worker.py` | Smoke-тест без деплоя |
| `scripts/export/deploy_worker.py` | Build → validate → PUT API |

## Деплой (когда будет токен)

```bat
set CLOUDFLARE_API_TOKEN=...
set CLOUDFLARE_ACCOUNT_ID=...
python scripts/export/deploy_worker.py
```

Токен: Dashboard → My Profile → API Tokens → шаблон Edit Cloudflare Workers.

## Риски

- Вес скрипта растёт с контентом: сейчас 60% лимита, следить при добавлении страниц.
- Без токена прод не обновляется — локальный воркер-файл при этом всегда свежий.
