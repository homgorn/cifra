# INDEX: Topvisor

Обновлено: 2026-09-14. Источник: API v2 Топвизора, проект cifra pozition (32490624).

## Файлы
| Путь | Что внутри |
|---|---|
| `README.md` | Структура, правила денег, команды |
| `INDEX.md` | Этот индекс |
| `endpoints.md` | Все методы API v2 с пометками free/price/PAID |
| `scripts/tv.py` | Клиент: баланс, проекты, ключи, конкуренты, оценка цены, защита трат |
| `scripts/sync.py` | Полный синк в SQLite и MD |
| `db/topvisor.db` | База: projects(1), searchers(1), keywords(154), positions(154), tops_snapshots(1), competitors(2), balance_snapshots, api_log |
| `exports/projects.md` | Проект cifra pozition, Яндекс Россия |
| `exports/keywords.md` | 154 ключа одной группой |
| `exports/positions.md` | Срез 28.08: топ-10 11, средняя 83.9, видимость 5% |
| `exports/competitors.md` | press18.ru, artis18.com |
| `exports/balance.md` | История баланса, сейчас 1977.7 RUB |

## Связи с проектом
- Отчетный сайт: `reports/cifra18-audit/` (страницы конкурентов, регионов, методология)
- База знаний: `brain/wiki/knowledge_graph/` (сущности competitors, locations)
- Аудиты: `audit/AUDIT_REPORT.md`, `brain/wiki/audits/`
- Туду: маркетинговые задачи и ожидание Метрики/Вебмастера/Топвизора

## Следующие шаги (бесплатно)
1. Разобрать 154 ключа по группам под 88 услуг (группы уже есть в API, чтение бесплатно)
2. Сверить топ-10 ключей с money pages сайта
3. Добавить press18.ru и artis18.com в граф конкурентов
4. Запустить новую проверку позиций только после подтверждения цены через `price positions`
