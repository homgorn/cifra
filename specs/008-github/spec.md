# 008. Git + GitHub: код, Pages, Actions — spec

Статус: **in progress** — локальный репозиторий готов, ждёт remote.

## Цель

Весь код в git, сайт на GitHub Pages, еженедельное автообновление данных
через Actions. Правило: батники только ASCII (кириллица без BOM ломает
парсинг cmd — проверено на `deploy_github_pages.bat`).

## Скоуп

- Локально: `git init`, `.gitignore` (секреты, `data/exports/`, `*.db`, `*.rar`,
  большой PDF), `.gitattributes`, ветка `main`, первый коммит (done).
- `README.md` — лицо репозитория (done).
- `deploy_github_pages.bat` — push main + subtree push сайта в `gh-pages` (done, проверен без remote).
- `.github/workflows/weekly-refresh.yml` — cron Пн 06:00 UTC + ручной запуск:
  экспорты API → пересборка данных → валидация → коммит → деплой Pages
  официальными экшенами (done, ждёт прогона в облаке).
- Секреты Actions: `YANDEX_OAUTH_TOKEN` (+ client id/secret), ротация ~180 дней.

## Вне скоупа

- Issues как трекер (спеки живут в `specs/`; перенос — по запросу).
- Приватность: репозиторий можно сделать private — Pages работает и на нём.

## Критерии приёмки

- [x] Коммит без секретов и без `data/exports/`, дерево чистое
- [x] Батник проверен (usage + exit 2)
- [ ] Remote добавлен, push main прошёл
- [ ] Pages включены, сайт открывается по `https://USER.github.io/REPO/`
- [ ] Первый прогон Actions зелёный
