---
id: test-data-upload
title: Тестовые данные и загрузка
description: Как безопасно добавлять тестовые изображения в репозиторий.
slug: /test-data-upload
---

# Тестовые данные и загрузка

## Рекомендации

- хранить в репозитории только sample-данные;
- ограничивать размер набора и отдельных файлов;
- всегда коммитить manifest с причинами пропусков.

## Подготовка sample набора

```bash
python3 scripts/prepare_test_dataset.py \
  --source-root "/path/to/photo-root" \
  --output-dir sample_data \
  --max-mb 50 \
  --max-file-mb 8 \
  --max-per-folder 10
```

## Сортировка «россыпью»

```bash
python3 scripts/sort_loose_media.py \
  --source-dir "/path/to/loose_files" \
  --media-root media \
  --dry-run
```
