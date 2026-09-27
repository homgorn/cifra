# Сессия 2026-09-27: мега-главная, DataLens, хостинг

## Что просили
1. DataLens-спека. 2. Все важные отчёты на главную. 3. Бесплатный хостинг с API (Cloudflare из РФ не открывается).

## Что сделано
1. **Фантомная папка** `data/exports/metrika` (видна в листинге, недоступна): перенос выгрузок в `data/exports/metrika_api/`, свежий прогон 5/5 с тем же объёмом. `build_site_data.py` переключён.
2. **Мега-главная (спека 006, done):** `build_site_data.py` → `js/site-data.js` (708, SQI 220, 257 000 ₽, 59 заказов, топ-5 дней, топ-10 запросов, источники, статусы). Главная v2.0: 6 KPI, 4 графика, топ-10, ссылки. Smoke расширен (конфликт имён SITE исправлен), валидатор знает site-data.js. Итог: validate PASSED (40 canvas, 28 URL), worker PASSED (28 файлов, 71 роут, 61.3%).
3. **Спека 007 DataLens** (planned): 4 вкладки, формулы, регламент, публичная витрина клиенту.
4. **Хостинг:** рекомендован GitHub Pages (+ DataLens-ссылки как zero-hosting шаринг).

## Где лежит
- `reports/cifra18-audit/js/site-data.js`, `scripts/export/build_site_data.py`
- `specs/006-homepage-mega/`, `specs/007-datalens-dashboards/`
- `data/exports/metrika_api/2026-09-27/`

## Следующий шаг
- Выбор хостинга → скрипт деплоя по образцу `yandex_setup.bat`.
- Сборка DataLens по спеке 007.
