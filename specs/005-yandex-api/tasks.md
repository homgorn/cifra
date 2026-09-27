# 005. API-доступ Яндекс — tasks

- [x] `.env` + `.env.example` (секреты только локально)
- [x] `yandex_oauth.py`: auth-url / exchange / test
- [x] `metrica_api_export.py` дописан (5 экспортов)
- [x] `yw_api_export.py` переписан (8 запросов, авто-host)
- [x] Проверка без токена: оба exit 2, без падений
- [x] Батник `yandex_setup.bat` (URL / exchange+test+экспорты), проверен
- [x] Topvisor API проверен (баланс 1977.7 RUB)
- [x] Код получен, exchange OK (токен в .env, ~180 дней)
- [x] `test`: Метрика OK (4 счётчика), Вебмастер OK (user 913707959)
- [x] Исправлены host-матчинг (punycode) и limit/order_by; прогон 5+8 с 0 ошибок
- [x] Разбор JSON в вики: `12_API_Live.md`, `06_Ecommerce_Goals.md`, INDEX обеих вики, CLIENT_REPORT
- [ ] Еженедельный перепрогон экспортов (руками или по расписанию)
