# Exports Index — ЦИФРА18

**Last updated:** 2026-09-10

---

## 📁 Структура экспортов

```
data/exports/
├── metrica/                    # Яндекс.Метрика
│   ├── YYYY-MM-DD/
│   │   ├── sources_summary.csv
│   │   ├── search_queries.csv
│   │   ├── goals_conversions.csv
│   │   ├── ecommerce_transactions.csv
│   │   ├── landing_pages_organic.csv
│   │   ├── geography_organic.csv
│   │   ├── devices_organic.csv
│   │   └── url_params.csv
│   └── latest/ -> symlink
│
├── topvisor/                   # Топвизор
│   ├── YYYY-MM-DD/
│   │   ├── positions_all.csv
│   │   ├── keywords_groups.csv
│   │   ├── competitors_overview.csv
│   │   ├── visibility_traffic.csv
│   │   ├── serp_features.csv
│   │   ├── landing_pages.csv
│   │   ├── position_history_top200.csv
│   │   └── local_pack.csv
│   └── latest/ -> symlink
│
├── bitrix/                     # Битрикс каталог/статьи
│   ├── YYYY-MM-DD/
│   │   ├── catalog_full.csv        # 300+ услуг: ID, название, URL, категория, цена, свойства
│   │   ├── catalog_categories.csv  # Иерархия категорий
│   │   ├── catalog_properties.csv  # Свойства товаров (материал, формат, цвет и т.д.)
│   │   ├── articles_290.csv        # 290 статей: URL, заголовок, контент, дата, автор, теги
│   │   ├── articles_categories.csv # Категории новостей
│   │   └── seo_templates.csv       # Шаблоны meta title/description/H1 по типам страниц
│   └── latest/ -> symlink
│
├── gsc/                        # Google Search Console (когда появится доступ)
│   ├── YYYY-MM-DD/
│   │   ├── search_analytics.csv
│   │   ├── coverage.csv
│   │   ├── sitemaps.csv
│   │   └── core_web_vitals.csv
│   └── latest/ -> symlink
│
├── yandex_webmaster/           # Яндекс.Вебмастер
│   ├── YYYY-MM-DD/
│   │   ├── search_queries.csv
│   │   ├── indexing.csv
│   │   ├── ixs_history.csv
│   │   └── turbo_pages.csv
│   └── latest/ -> symlink
│
└── crm/                        # CRM / Битрикс24 (лиды, сделки)
    ├── YYYY-MM-DD/
    │   ├── leads.csv
    │   ├── deals.csv
    │   ├── utm_attribution.csv
    │   └── roi_by_channel.csv
    └── latest/ -> symlink
```

---

## 📋 Планы выгрузок (планы в brain/wiki/exports/)

| Источник | План | Статус |
|---|---|---|
| Яндекс.Метрика | `brain/wiki/exports/metrica_plan.md` | ⏳ Готов, ждёт доступ |
| Топвизор | `brain/wiki/exports/topvisor_plan.md` | ⏳ Готов, ждёт доступ |
| Битрикс каталог | `brain/wiki/exports/bitrix_catalog.md` | ⏳ План |
| CRM | — | ⏳ План |

---

## 🔧 Скрипты экспорта

| Скрипт | Источник | Назначение | Путь |
|---|---|---|---|
| `metrica_api_export.py` | Яндекс.Метрика API | Еженедельный pull основных отчётов | `scripts/export/` |
| `topvisor_api_export.py` | Топвизор API v2 | Ежедневный pull позиций | `scripts/export/` |
| `bitrix_catalog_export.py` | Битрикс (SQL/REST) | Экспорт каталога, статей, SEO шаблонов | `scripts/export/` |
| `gsc_api_export.py` | Google Search Console API | Еженедельный pull (когда доступ) | `scripts/export/` |
| `yw_api_export.py` | Яндекс.Вебмастер API | Еженедельный pull | `scripts/export/` |
| `crm_export.py` | Битрикс24 / amoCRM | Еженедельный pull лидов/сделок | `scripts/export/` |

---

## 📊 Форматы данных

### CSV стандарты
- **Encoding:** UTF-8
- **Delimiter:** `,` (comma)
- **Quote:** `"` (double quote)
- **Date format:** ISO 8601 (`YYYY-MM-DD` или `YYYY-MM-DDTHH:MM:SS`)
- **Null:** пустое поле (не `NULL`, не `null`)

### Обязательные поля по типам

#### `catalog_full.csv`
| Поле | Тип | Описание |
|---|---|---|
| `id` | int | ID элемента в Битриксе |
| `iblock_id` | int | ID инфоблока |
| `name` | string | Название услуги/товара |
| `detail_page_url` | string | Полный URL |
| `section_path` | string | Путь категорий: `Полиграфия > Визитки > Крафт` |
| `section_ids` | string | ID разделов через `,` |
| `price` | float | Базовая цена |
| `currency` | string | `RUB` |
| `properties` | JSON | Все свойства: материал, формат, цвет, тираж и т.д. |
| `preview_text` | string | Краткое описание |
| `detail_text` | string | Полное описание |
| `images` | JSON | Массив фото: URL, alt |
| `seo_title` | string | Meta title |
| `seo_description` | string | Meta description |
| `seo_h1` | string | H1 |
| `canonical_url` | string | Canonical (если задан) |
| `active` | bool | Активен/неактивен |
| `date_create` | datetime | Дата создания |
| `date_modify` | datetime | Дата изменения |

#### `articles_290.csv`
| Поле | Тип | Описание |
|---|---|---|
| `id` | int | ID элемента |
| `name` | string | Заголовок |
| `detail_page_url` | string | URL |
| `preview_text` | string | Анонс |
| `detail_text` | string | Полный текст (HTML) |
| `date_create` | datetime | Дата публикации |
| `author` | string | Автор |
| `tags` | string | Теги через `,` |
| `section` | string | Раздел новостей |
| `images` | JSON | Фото в статье |
| `seo_title` | string | Meta title |
| `seo_description` | string | Meta description |
| `seo_h1` | string | H1 |
| `canonical_url` | string | Canonical |

---

## 🔄 Автоматизация

### Cron / Systemd Timers
```bash
# Ежедневно 05:00 — Топвизор позиции
0 5 * * * /opt/cifra18/scripts/export/topvisor_api_export.py

# Ежедневно 06:00 — Метрика (если API позволяет)
0 6 * * * /opt/cifra18/scripts/export/metrica_api_export.py

# Еженедельно Понедельник 07:00 — Битрикс каталог (полный)
0 7 * * 1 /opt/cifra18/scripts/export/bitrix_catalog_export.py --full

# Ежедневно 03:00 — Битрикс каталог (инкремент)
0 3 * * * /opt/cifra18/scripts/export/bitrix_catalog_export.py --incremental
```

### Версионирование
- Каждый экспорт в папку `YYYY-MM-DD/`
- `latest/` — симлинк на последний успешный экспорт
- Хранить последние 90 дней, архивировать старые в S3/Cloudflare R2

---

## 🔗 Использование экспортов

| Потребитель | Источники | Назначение |
|---|---|---|
| `scripts/audit/full_catalog_audit.py` | `bitrix/catalog_full.csv` | Baseline URL списка |
| `scripts/audit/articles_audit.py` | `bitrix/articles_290.csv` | Baseline URL статей |
| `scripts/content/wp_import_prepare.py` | `bitrix/articles_290.csv` + `bitrix/catalog_full.csv` | Подготовка CSV для WP All Import |
| `scripts/content/programmatic_generators/` | `bitrix/catalog_full.csv` + `bitrix/catalog_properties.csv` | Данные для программатик страниц |
| `research/keywords/keyword_map_full.csv` | `topvisor/positions_all.csv` + `metrica/search_queries.csv` | Семантическое ядро |
| `brain/wiki/entities/services.md` | `bitrix/catalog_full.csv` + `bitrix/catalog_properties.md` | Каталог сущностей |
| Monitoring dashboards | Все | Графики трафика, позиций, конверсий |

---

*Экспорты — фундамент всех аналитических решений. Настроить в первую очередь после получения доступов.*