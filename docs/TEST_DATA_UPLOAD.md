# Тестовые папки в репозиторий: как правильно (и без ошибки "file is too large")

Коротко: **да, тестовые папки можно заливать**, но только сэмпл с лимитами.

## Почему ругается на JPEG
Ошибка GitHub:
- `The file is too large and cannot be uploaded` — означает, что отдельный файл превысил лимит веб-загрузки/репозитория.

Практический ориентир:
- hard limit GitHub Git: 100 MB на файл;
- лучше держать изображения сильно ниже (например 5–20 MB), чтобы не ловить проблемы на вебе и в CI.

## Рекомендованный путь для вас (Windows + VSCode)

1. Работайте кодом здесь/в VSCode.
2. На локальном Windows соберите маленький сэмпл скриптом.
3. Коммитьте и пушьте через VSCode Git **или** GitHub Desktop — оба подходят.

> GitHub Desktop ставить можно, но **не обязательно**. 
> Если в VSCode уже удобно с git — оставайтесь в VSCode.

---

## Автосборка test dataset (с защитой от больших файлов)
Используйте `scripts/prepare_test_dataset.py`:

```bash
python3 scripts/prepare_test_dataset.py \
  --source-root "/path/to/your/photo-root" \
  --output-dir sample_data \
  --max-mb 50 \
  --max-file-mb 8 \
  --max-per-folder 10
```

### Если хотите только конкретные категории
```bash
python3 scripts/prepare_test_dataset.py \
  --source-root "/path/to/your/photo-root" \
  --output-dir sample_data \
  --max-mb 50 \
  --max-file-mb 8 \
  --max-per-folder 15 \
  --include-folders "БЕЙДЖ" "ВИЗИТКИ" "РУЧКИ, БЛОКНОТЫ"
```

Скрипт:
- копирует изображения в `sample_data/` с сохранением структуры;
- ограничивает общий размер набора;
- пропускает слишком крупные одиночные файлы (`--max-file-mb`);
- пишет `sample_data/manifest.json` с причинами пропусков (`skipped_by_file_size` и примеры файлов).

---

## Что коммитить
- `sample_data/` (если реально нужен сэмпл в репо);
- `sample_data/manifest.json` обязательно.

## Что не коммитить
- Полный архив с прод-данными;
- Кэши моделей и временные файлы.

---

## Если снова ошибка на push
1. Проверьте самый большой файл в индексе.
2. Уменьшите `--max-file-mb` (например до 5).
3. Пересоберите `sample_data` и перезапишите коммит.
4. Если большой файл уже попал в историю, удалите его из истории перед push.
