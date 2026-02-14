# WP All Import CSV Schema (portfolio)

Ниже базовая схема колонок, чтобы импортировать в WordPress и не потерять SEO/таксономии.

## Обязательные
- `post_type` — например `portfolio`.
- `post_status` — `publish`/`draft`.
- `post_title`
- `post_name` — SEO slug, уникальный.
- `post_content` — HTML описание.
- `tax_category` — основная таксономия.
- `tax_post_tag` — теги через запятую.

## Изображения
- `featured_image_primary_url` — основной URL изображения.
- `featured_image_backup_url` — резервный URL.
- `file_path_local` — относительный путь в локальном каталоге.
- `media_filename` — фактическое имя файла.

## SEO
- `seo_title_ru`
- `seo_description_ru`
- `seo_focus_keyword_ru`
- `image_alt_ru`
- `image_caption_ru`
- `schema_type` — например `Product`/`CreativeWork`.
- `schema_jsonld` — опционально, если хотите готовый JSON-LD в колонке.

## AI/аудит
- `raw_vision_en` — исходное распознавание модели (EN).
- `ai_description_ru` — переработанный текст на русском.
- `ai_model`
- `ai_confidence`
- `dominant_color`
- `material_guess`
- `logo_method_guess`
- `exif_datetime_original`
- `pipeline_status`
- `pipeline_error`

## Атрибуты фильтров
Рекомендуется префикс `attr_`:
- `attr_color`
- `attr_material`
- `attr_branding_method`
- `attr_product_type`

Это удобно маппить в атрибуты/таксономии в интерфейсе WP All Import.
