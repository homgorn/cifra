---
id: intro
title: Обзор проекта
description: Полная документация Cifra SEO pipeline на Docusaurus.
slug: /intro
---

# Cifra SEO Pipeline

Cifra — это pipeline для подготовки большого каталога медиа к публикации в WordPress:

- инвентаризация файлов;
- нормализация имен под SEO;
- классификация;
- генерация контента;
- экспорт CSV для WP All Import;
- строгая QA-валидация перед импортом.

## Что входит в проект

- `scripts/validate_portfolio_csv.py` — CLI-валидатор CSV;
- `templates/wp_portfolio_template.csv` — шаблон данных;
- `docs/*.md` — исходные markdown-документы;
- `website/` — полный docs-портал на Docusaurus.

## Быстрый старт docs-портала

```bash
cd website
npm install
npm run start
```

Для production-сборки:

```bash
npm run build
npm run serve
```

## Ключевые преимущества

- SEO-first структура данных;
- адаптивный frontend документации;
- сильная проверка схемы CSV и качества данных.
