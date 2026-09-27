# Сессия 2026-09-27: API-доступ Яндекс

## Что просили
Подключить API по выданным client_id/secret (OAuth, redirect verification_code).

## Что сделано
1. Секреты положены в корневой `.env` (+ `.env.example` без значений). В код и доки не вшиты.
2. `scripts/export/yandex_oauth.py`: `auth-url` (проверен, URL строится), `exchange <код>`, `test` (Метрика counters + Вебмастер user, маски вместо токенов).
3. `scripts/export/metrica_api_export.py` дописан: источники, запросы, входы, цели, e-commerce → `data/exports/metrica/<дата>/`. Без токена exit 2.
4. `scripts/export/yw_api_export.py` переписан: убраны неверные эндпоинты, host автоопределяется (ищет cifra), 8 запросов → `data/exports/yandex_webmaster/<дата>/`. Без токена exit 2.
5. Спека `005-yandex-api` (spec/tasks), `specs/README` обновлён.

## Обмен и первые выгрузки (2026-09-27, продолжение)
- Код принят, токен в `.env` (~180 дней). `test`: Метрика OK, Вебмастер OK.
- На аккаунте 2 сайта в ВМ (rentasib.ru без подтверждения + cifra verified) и 4 счётчика Метрики (dzen, maps ×3). Скрипт сначала взял чужой host — исправлено матчингом по punycode + verified.
- API-нюансы: popular требует `order_by` (подошёл TOTAL_CLICKS) и limit ≤ 500.
- Прогон: Метрика 5/5, Вебмастер 8/8, всё в `data/exports/*/2026-09-27/`.
- Первые находки: SQI 220, searchable **708** (ручной CSV был выборкой!), excluded 477; в диагностике только дубли (PAGES + CONTENT_ATTRS), фаталов нет; sitemap читаются без ошибок, но **urls_count=0 везде**; автоцели звонков/почты активны; **e-commerce идёт с реальной выручкой** (напр. 2026-07-02: 4 покупки на 241 565 ₽).
- Дальше: разбор JSON в вики (цифры сводок обновить), затем CRO/ROI по автоцелям и заказам.

## Разбор в вики (2026-09-27, вечер)
- Нюансы API зафиксированы в скрипте: indexing/events только без дат, popular через TOTAL_CLICKS/limit 500, query-history пустые — не тянем.
- Вики: `webmaster_analytics/12_API_Live.md` + правки INDEX (тоталы 708/477, SQI 220); `metrika_analytics/06_Ecommerce_Goals.md` + правка INDEX; CLIENT_REPORT (тотал в поиске, e-commerce строка, дубли атрибутов).
- Ключевое: ручной CSV был выборкой; sitemap пустые (0 URL); 5xx падают до сих пор (30 в 2026); e-commerce 59 покупок / 257 000 ₽; 12 автоцелей; топ входов с отказами 6–13%.
- Спека 005 почти закрыта: остался регулярный перепрогон.

## 2026-09-27, продолжение
- Обвязка переведена на батник `yandex_setup.bat`: без аргументов печатает URL, с кодом делает exchange → test → оба экспорта. Проверен (exit 2 без кода).
- `yandex_oauth.py`: добавлен `redirect_uri` в обмен, в ошибках виден код ответа API.
- `.gitignore` создан (`.env`, токены, `data/exports/`).
- Email `izhcifra@yandex.ru` и ID 511593 сохранены в `.env` (назначение ID уточнить).
- Topvisor API проверен: ключ рабочий, баланс 1977.7 RUB (совпадает с INDEX).
