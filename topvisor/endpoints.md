# Topvisor API v2: каталог эндпоинтов

База: `POST https://api.topvisor.com/v2/json/<метод>`
Заголовки: `Authorization: bearer KEY`, `User-Id: ID`, `Content-Type: application/json`.

Условные знаки цены:
- `[free]` чтение, денег не снимает
- `[price]` бесплатная оценка стоимости перед запуском
- `[PAID]` снимает деньги, скрипт `tv.py` блокирует без `--confirm-spend`

Источник: официальный OpenAPI репозиторий topvisor/topvisor-openapi, методы проверены вызовами 14.09.2026.

## Bank_2 (баланс)
| Метод | Цена | Назначение |
|---|---|---|
| `get/bank_2/info` | [free] | Баланс общий/личный/бонус, тариф, подписка |
| `get/bank_2/history` | [free] | История списаний |
| `get/bank_2/history.summary` | [free] | Сводка по списаниям |

## Projects_2 (проекты)
| Метод | Цена | Назначение |
|---|---|---|
| `get/projects_2/projects` | [free] | Список проектов, регионы, сводка топов |
| `add/projects_2/projects` | [free] | Создать проект (сами проверки платные) |
| `add/projects_2/projects.copy` | [free] | Копия проекта |
| `del/projects_2/projects` | [free] | Удалить |
| `edit/projects_2/projects.name` | [free] | Переименовать |
| `edit/projects_2/projects.on` | [free] | Вкл/выкл |
| `edit/projects_2/projects.sort` | [free] | Порядок |
| `edit/projects_2/projects.move` | [free] | Переместить в папку |
| `edit/projects_2/projects.tags` | [free] | Теги |
| `edit/projects_2/projects.favorite` | [free] | Избранное |
| `get/projects_2/competitors` | [free] | Конкуренты проекта |
| `add/projects_2/competitors` | [free] | Добавить конкурента |
| `del/projects_2/competitors` | [free] | Удалить конкурента |
| `edit/projects_2/competitors.*` | [free] | Правки конкурентов (name, on, move, brand) |
| `edit/projects_2/brand` | [free] | Брендовые настройки |
| `get/projects_2/tasks` | [free] | Задачи проекта |
| `add/projects_2/analytics` | [free] | Подключить аналитику |
| `add/projects_2/tasks.indexing` | [PAID] | Проверка индексации |
| `get/projects_2/tasks.indexing.price` | [price] | Цена проверки индексации |
| `add/projects_2/tasks.keywords.collect` | [PAID] | Сбор ключей |
| `get/projects_2/tasks.keywords.collect.price` | [price] | Цена сбора ключей |
| `add/projects_2/tasks.relevants` | [PAID] | Проверка релевантности |
| `get/projects_2/tasks.relevants.price` | [price] | Цена проверки релевантности |
| `add/projects_2/tasks.volumes` | [PAID] | Сбор частотности |
| `get/projects_2/tasks.volumes.price` | [price] | Цена сбора частотности |

## Keywords_2 (ключи)
| Метод | Цена | Назначение |
|---|---|---|
| `get/keywords_2/keywords` | [free] | Список ключей проекта |
| `add/keywords_2/keywords` | [free] | Добавить ключи (проверки по ним платные) |
| `del/keywords_2/keywords` | [free] | Удалить ключи |
| `edit/keywords_2/keywords.*` | [free] | Правки (move, rename, sort, tags, target, undel) |
| `add/keywords_2/keywords.import` | [free] | Импорт ключей файлом |
| `get/keywords_2/keywords.export` | [free] | Экспорт ключей |
| `get/keywords_2/groups` | [free] | Группы ключей |
| `add/keywords_2/groups` | [free] | Создать группу |
| `del/keywords_2/groups` | [free] | Удалить группу |
| `edit/keywords_2/groups.*` | [free] | Правки групп (move, on, rename, sort, undel) |
| `get/keywords_2/folders` | [free] | Папки |
| `add/keywords_2/folders` | [free] | Создать папку |
| `del/keywords_2/folders` | [free] | Удалить папку |
| `edit/keywords_2/folders.*` | [free] | Правки папок (move, rename, undel) |
| `edit/keywords_2/volumes.go` | [PAID] | Запуск сбора частотности |
| `get/keywords_2/volumes.price` | [price] | Цена сбора частотности |
| `edit/keywords_2/collect.go` | [PAID] | Запуск сбора подсказок/частот |
| `get/keywords_2/collect.price` | [price] | Цена сбора |
| `edit/keywords_2/claster.byrelevant` | [free] | Кластеризация по релевантным |
| `edit/keywords_2/claster.bytarget` | [free] | Кластеризация по целевым |
| `add/keywords_2/claster.task` | [PAID] | Задача кластеризации |
| `add/keywords_2/claster.taskchange` | [PAID] | Перекластеризация |
| `get/keywords_2/claster.price` | [price] | Цена кластеризации |
| `get/keywords_2/claster.percent` | [free] | Прогресс кластеризации |
| `get/keywords_2/claster.countpricereclaster` | [price] | Оценка цены |
| `get/keywords_2/magnet` | [free]* | Подбор слов (Магнит слов), *проверки платные |
| `get/keywords_2/magnet.export` | [free] | Экспорт подбора |
| `get/keywords_2/magnet.import` | [free] | Импорт в проект |
| `get/keywords_2/semantics.deduplicate` | [free] | Дедупликация семантики |

## Positions_2 (позиции)
| Метод | Цена | Назначение |
|---|---|---|
| `get/positions_2/history` | [free] | История позиций по датам |
| `get/positions_2/summary` | [free] | Сводка (топы, средняя, видимость) |
| `get/positions_2/summary.chart` | [free] | Данные для графика динамики |
| `edit/positions_2/checker.go` | [PAID] | Запустить проверку позиций |
| `get/positions_2/checker.price` | [price] | Цена проверки позиций |
| `edit/positions_2/relevant.checker.go` | [PAID] | Проверка релевантных страниц |
| `get/positions_2/relevant.checker.price` | [price] | Цена проверки релевантности |
| `edit/positions_2/settings` | [free] | Настройки проверок |
| `add/positions_2/searchers` | [free] | Добавить поисковик |
| `del/positions_2/searchers` | [free] | Удалить поисковик |
| `edit/positions_2/searchers.enabled` | [free] | Вкл/выкл поисковик |
| `edit/positions_2/searchers.sort` | [free] | Порядок |
| `add/positions_2/searchers.regions` | [free] | Добавить регион |
| `del/positions_2/searchers.regions` | [free] | Удалить регион |
| `edit/positions_2/searchers.regions` | [free] | Править регион |
| `edit/positions_2/searchers.regions.sort` | [free] | Порядок регионов |
| `get/positions_2/searchers.regions.export` | [free] | Экспорт регионов |
| `add/positions_2/searchers.regions.import` | [free] | Импорт регионов |

## Competitors_2, Snapshots_2 (конкуренты, выдачи)
| Метод | Цена | Назначение |
|---|---|---|
| `get/competitors_2/table` | [free] | Таблица конкурентов |
| `get/competitors_2/charts` | [free] | Графики по конкурентам |
| `get/competitors_2/orders` | [free] | Заказы/срезы |
| `get/competitors_2/orders.bykeyword.info` | [free] | Срез по ключу |
| `get/competitors_2/orders.byurl.info` | [free] | Срез по URL |
| `edit/competitors_2/orders.pay` | [PAID] | Оплата среза выдачи |
| `get/snapshots_2/history` | [free] | История сниппетов выдачи |
| `get/snapshots_2/competitors` | [free] | Сниппеты конкурентов |

## Audit_2 (аудит сайта)
| Метод | Цена | Назначение |
|---|---|---|
| `get/audit_2/audit.summary` | [free] | Сводка аудита |
| `get/audit_2/audit.checks` | [free] | Проверки аудита |
| `get/audit_2/audit.links/js/css` | [free] | Ссылки, JS, CSS |
| `get/audit_2/audit.summarypage` | [free] | Сводка по странице |
| `edit/audit_2/audit.checker.go` | [PAID] | Запуск аудита |
| `get/audit_2/audit.checker.price` | [price] | Цена аудита |
| `get/audit_2/indexing` | [free] | Индексация страниц |
| `get/audit_2/indexing.summary` | [free] | Сводка индексации |
| `edit/audit_2/indexing.checker.go` | [PAID] | Проверка индексации |
| `get/audit_2/indexing.checker.price` | [price] | Цена проверки |
| `get/audit_2/watcher` | [free] | Наблюдатель изменений |
| `get/audit_2/watcher.summary` | [free] | Сводка изменений |
| `edit/audit_2/watcher.checker.go` | [PAID] | Запуск наблюдателя |
| `get/audit_2/watcher.checker.price` | [price] | Цена |
| `edit/audit_2/sitemap.checker.go` | [PAID] | Проверка sitemap |
| `get/audit_2/sitemap.checker.price` | [price] | Цена |
| `get/audit_2/counturls` | [free] | Подсчет URL |
| `edit/audit_2/settings` | [free] | Настройки аудита |

## AiTracker_2, Content_2, KeywordsAi_2 (AI и тексты)
| Метод | Цена | Назначение |
|---|---|---|
| `get/aitracker_2/summary` | [free] | Сводка AI-трекера |
| `get/aitracker_2/history` | [free] | История AI-трекера |
| `del/aitracker_2/history` | [free] | Очистить историю |
| `get/aitracker_2/settings` | [free] | Настройки |
| `edit/aitracker_2/settings` | [free] | Править настройки |
| `edit/aitracker_2/checker.go` | [PAID] | Запуск AI проверки |
| `get/aitracker_2/checker.price` | [price] | Цена AI проверки |
| `get/content_2/apometr.calendar` | [free] | Календарь апдейтов текстов |
| `get/content_2/apometr.history` | [free] | История текстов |
| `get/content_2/apometr.text.calendar` | [free] | Календарь по тексту |
| `get/content_2/apometr.updates` | [free] | Обновления |
| `get/keywordsai_2/groups` | [free] | Группы AI-ключей |
| `add/keywordsai_2/groups` | [free] | Создать группу |
| `del/keywordsai_2/groups` | [free] | Удалить группу |
| `get/keywordsai_2/keywords` | [free] | AI-ключи |
| `del/keywordsai_2/keywords` | [free] | Удалить |
| `add/keywordsai_2/keywords.import` | [free] | Импорт AI-ключей |

## System_2, Users_2, Bank/Payments (служебные)
| Метод | Цена | Назначение |
|---|---|---|
| `get/system_2/common.regions` | [free] | Справочник регионов ПС |
| `get/users_2/profile.avatar` | [free] | Аватар профиля |
| `edit/users_2/profile` | [free] | Профиль |
| `edit/users_2/profile.currency/lang/timezone` | [free] | Настройки профиля |
| `get/payments_2/companies` | [free] | Компании для счетов |
| `edit/payments_2/subscriptions` | [PAID] | Подписка (меняет оплату!) |
| `edit/payments_2/tariff.setnext` | [PAID] | Смена тарифа (меняет оплату!) |
| `get/tpvsr_2/stat` | [free] | Статистика |
| `edit/tpvsr_2/tags`, `edit/urls_2/tags` | [free] | Теги |

## Правило трат
Перед запуском любого `[PAID]` метода сначала вызываем парный `[price]`, показываем сумму владельцу и ждем подтверждения. Скрипт `tv.py` блокирует платные вызовы без `--confirm-spend`. Баланс печатается после каждого запуска.
