---
id: csv-validator
title: CSV Validator
description: Проверка схемы и качества CSV перед импортом в WP.
slug: /csv-validator
---

# CSV Validator

CLI-валидатор: `scripts/validate_portfolio_csv.py`.

## Что проверяется

- наличие обязательных колонок в header;
- malformed строки (extra/missing columns);
- дубли `post_name` (опционально strict);
- пустой `featured_image_primary_url` (опционально strict);
- пустые required ячейки (опционально strict).

## Коды возврата

- `0` — файл валиден в выбранном режиме;
- `1` — ошибка валидации (schema/data checks);
- `2` — CSV-файл не найден.

## Примеры запуска

Базовый режим:

```bash
python3 scripts/validate_portfolio_csv.py templates/wp_portfolio_template.csv
```

Строгий режим для CI:

```bash
python3 scripts/validate_portfolio_csv.py templates/wp_portfolio_template.csv \
  --fail-on-duplicate-slug \
  --fail-on-empty-primary-url \
  --fail-on-empty-required
```

Machine-readable вывод (для CI/автоматизации):

```bash
python3 scripts/validate_portfolio_csv.py templates/wp_portfolio_template.csv --json
```

## Что улучшено в последних ревизиях

- агрегирование нескольких ошибок за один запуск;
- `line:column` диагностика для пустых обязательных полей;
- JSON-режим вывода для интеграции в CI-пайплайны;
- расширенные CLI-регрессионные тесты для edge-cases.
