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
- отсутствие дублирующихся заголовков CSV;
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

Строгий режим для CI (коротко через `--strict-all`):

```bash
python3 scripts/validate_portfolio_csv.py templates/wp_portfolio_template.csv --strict-all
```

Эквивалентно ручному набору strict-флагов:

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

Запись JSON-отчета в файл (удобно для артефактов CI):

```bash
python3 scripts/validate_portfolio_csv.py templates/wp_portfolio_template.csv \
  --fail-on-duplicate-slug \
  --fail-on-empty-primary-url \
  --fail-on-empty-required \
  --report-path reports/validator-report.json
```

Тихий режим (без stdout, только exit code + optional report file):

```bash
python3 scripts/validate_portfolio_csv.py templates/wp_portfolio_template.csv \
  --fail-on-empty-required \
  --report-path reports/validator-report.json \
  --quiet
```

## Что улучшено в последних ревизиях

- агрегирование нескольких ошибок за один запуск;
- `line:column` диагностика для пустых обязательных полей;
- детект дублированных заголовков CSV до проверки строк;
- `--strict-all` как быстрый включатель всех строгих проверок;
- JSON-режим вывода, `--report-path` и `--quiet` для интеграции в CI-пайплайны;
- расширенные CLI-регрессионные тесты для edge-cases.


> Примечание: `--json` и `--quiet` взаимоисключающие флаги.
