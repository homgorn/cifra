# Технические фиксы по данным Яндекс.Вебмастера

**Источник:** Анализ 717 страниц (PARSE_ERROR 251, DUPLICATE 128, REDIRECT 89, HTTP_ERROR 13)  
**Связь с аудитом:** Дополняет `scripts/dev-fixes/bitrix_phase0_fixes.md` данными Вебмастера  
**Приоритет:** По критичности для индексации и ранжирования  

---

## 🔴 КРИТИЧНЫЕ (Блокируют индексацию)

### 1. Sitemap: все 19 URL возвращают 404, проверено 2026-09-28
**Данные Вебмастера:** `/shop/` раздел, 388 индексировано, 0 загружено, 24 в поиске. Робот не может получить sitemap.
**Фикс:** Включить генерацию sitemap в Bitrix, путь `/sitemap.xml` (не `/shop/`), обновить robots.txt
**Файлы:** `.settings.php`, `/bitrix/php_interface/init.php`, агент `CSitemap::Generate()`
**Дедлайн:** День 1

### 2. Canonical отсутствует на всех страницах
**Данные Вебмастера:** 128 DUPLICATE страниц: Яндекс не знает оригиналы. Параметрические URL (`detail.php?ID=`), слеши, UTM.
**Фикс:** Глобальный `rel=canonical` в `header.php` + `Clean-param` в robots.txt
```php
// header.php
$canonicalUrl = $APPLICATION->GetCurPageParam('', ['PAGEN_1', 'SORT', 'ORDER', 'set_filter', 'clear_cache'], true);
$canonicalFull = 'https://' . $_SERVER['HTTP_HOST'] . $canonicalUrl;
?>
<link rel="canonical" href="<?= htmlspecialcharsbx($canonicalFull) ?>">
```
**robots.txt:**
```
Clean-param: PAGEN_1 /catalog/
Clean-param: SORT /catalog/
Clean-param: ORDER /catalog/
Clean-param: ID /catalog/detail.php
Clean-param: utm_source /catalog/
Clean-param: utm_medium /catalog/
Clean-param: utm_campaign /catalog/
```
**Дедлайн:** День 1

### 3. PARSE_ERROR: 251 страница (35%)
**Паттерны:**
- `/shop/110177348`, 1 URL (но 19 строк Sitemap под /shop/)
- `/123456789.html`, ~200 URL (старые ID товаров, битриксовый мусор)
- `/catalog/detail.php?ID=XXX`, ~30 URL (старый каталог, параметрические)
- `/1229-2/`, «Сайт заблокирован хостинг-провайдером»

**Фиксы по приоритету:**
| Приоритет | Паттерн | Действие | Где |
|---|---|---|---|
| 1 | `/shop/*` | Заблокировать в robots.txt, убрать из sitemap | robots.txt, SEO настройки |
| 2 | `/*.html` (цифровые ID) | 410 Gone или 301 на SEF URL | .htaccess / urlrewrite.php |
| 3 | `/catalog/detail.php?ID=` | 301 на SEF URL товара | urlrewrite.php, component_epilog |
| 4 | `/1229-2/` | Исправить хостинг/доступ, запросить переобход | Хостинг, Вебмастер |

**Дедлайн:** Неделя 1

### 4. HTTP_ERROR: 13 страниц (404/5xx)
**Пример:** `/brendirovanie-avtomobilej-pishite-https-vk-com-cifraprint18-zvonite-79658423241/` → 404
**Фикс:** 
- 404 страницы → 410 Gone если удалены навсегда
- Настроить полезную 404 страницу с поиском/меню/контактами
- Проверить логи сервера на 5xx ошибки
**Дедлайн:** Неделя 1

---

## 🟠 ВЫСОКИЕ (Снижают качество индекса)

### 5. REDIRECT_NOTSEARCHABLE: 89 страниц
**Проблема:** Цепочки редиректов (A→B→C), редиректы на нерелевантные страницы, потеря веса.
**Примеры из events.csv:**
```
/catalog/poligrafiya/kalendari/kvartalnyy-kalendar-premium-prozrachnyy-plastik-s-1-rekl-polem/
  → REDIRECT to /catalog/poligrafiya/kalendari/kvartalnyy-kalendar-premium-1-rekl-pole-s-figurnoy-rezkoy/

/catalog/poligrafiya/paketnoe-laminirovanie/
  → REDIRECT to /catalog/poligrafiya/laminirovanie/paketnoe-laminirovanie/

/catalog/detail.php?ID=1243
  → REDIRECT to /catalog/
```

**Фикс:**
1. Аудит всех редиректов (Screaming Frog / Netpeak Spider)
2. Убрать цепочки: прямой 301 на финальный URL
3. Редиректы с `detail.php` на SEF: карта соответствия ID → SEF URL
4. Редиректы дублирующих категорий: объединить структуру, оставить одну
**Дедлайн:** Неделя 2

### 6. Шаблонные title/meta на SEARCHABLE страницах
**Данные:** ~40 страниц с `title="Каталог"`, `meta="Description"`
**Примеры:**
```
/catalog/detail.php?ID=124 → title="Каталог", meta="Description"
/catalog/detail.php?ID=1255 → title="Каталог", meta="Description"
/catalog/detail.php?ID=415 → title="Каталог", meta="Description"
/catalog/ → title="Каталог", meta="Description"
/news/ → title="Новости", meta="Description"
```

**Фикс:** В настройках компонентов `bitrix:catalog.section`, `bitrix:catalog.element`, `bitrix:news.list`:
- `meta description` = уникальный из описания раздела/товара (PREVIEW_TEXT)
- `title` = `[Название] в Ижевске: цены, заказать онлайн | Типография Цифра`
**Дедлайн:** Неделя 1 (параллельно с canonical)

### 7. BAD_QUALITY / LOW_DEMAND: 22 страницы
**Причина:** Тонкий контент, дубликаты, отсутствие E-E-A-T.
**Кандидаты (по patterns):**
- Страницы товаров без описания (только фото + цена)
- Категории с 1-2 товарами
- Статьи блога 2021 года без обновления

**Фикс:**
1. Выделить 22 URL из полного экспорта
2. Аудит: объём текста, уникальность, фото/видео, отзывы, FAQ
3. Добавить: уникальное описание 300+ слов, фото производства, видео, FAQ, таблицы
3. Запросить переобход в Вебмастере (приоритетные 20/день)
**Дедлайн:** Неделя 2-3

---

## 🟡 СРЕДНИЕ (Улучшают качество)

### 8. OTHER: 72 страницы (нет актуальных данных)
**Причина:** Робот давно не обходил, низкий приоритет, новые страницы.
**Фикс:**
1. Проверить внутренние ссылки на эти страницы
2. Добавить в sitemap с актуальным `lastmod`
3. Запросить переобход приоритетных (коммерческие разделы)
**Дедлайн:** Неделя 2-3

### 9. Отсутствие JSON-LD Schema
**Данные:** 0 страниц с Schema (по аудиту). Вебмастер не показывает структурированные данные.
**Фикс:** Развернуть шаблоны (см. `bitrix_phase0_fixes.md`):
- Organization + LocalBusiness: header.php / footer.php
- BreadcrumbList: компонент навигации
- Product + Offer + AggregateRating: catalog.element template
- Article: news.detail template
- ItemList / CollectionPage: catalog.section template
**Дедлайн:** Неделя 1-2

### 10. Изображения: нет lazyload, width/height, WebP
**Данные аудита:** 11/15 >200KB, 3.4MB GIF, 13 пустых alt
**Фикс:** В настройках Bitrix (Инфоблоки → Настройки → Обработка изображений):
- Формат: WebP (AVIF если поддерживается)
- Качество: 80
- Max размер: 200KB
- Lazyload: включить для below-fold
- width/height: прописать в компонентах
**Дедлайн:** Неделя 2

### 11. em-dash (: ) везде вместо запятых
**Данные аудита:** em-dash на главной (3), визитки (2), новости (19)
**Фикс:** Глобальная замена в шаблонах, компонентах, инфоблоках:
```php
// В result_modifier.php или init.php
$text = str_replace('-', ', ', $text);
$text = str_replace(' - ', ', ', $text);
```
**Дедлайн:** Неделя 1 (Quick Win)

---

## 📋 План исполнения (Спринты)

### Спринт 1 (Дни 1-3): Foundation Critical
- [ ] Sitemap генерация + robots.txt
- [ ] Canonical глобальный + Clean-param
- [ ] em-dash → запятые
- [ ] Заблокировать /shop/, /*.html в robots.txt
- [ ] 301 редиректы detail.php → SEF (карта ID→URL)

### Спринт 2 (Дни 4-7): Indexation Quality
- [ ] JSON-LD шаблоны (Org, LocalBusiness, Breadcrumb, Product, Article)
- [ ] Уникальные title/meta для 142 SEARCHABLE страниц
- [ ] Аудит и фикс 89 REDIRECT_NOTSEARCHABLE (убрать цепочки)
- [ ] Настроить переобход 20 приоритетных URL/день

### Спринт 3 (Неделя 2): Content Quality
- [ ] Исправить 22 BAD_QUALITY страницы (добавить контент)
- [ ] Оптимизация изображений (WebP, lazyload, width/height)
- [ ] Исправить 13 HTTP_ERROR (410/полезная 404)
- [ ] Запросить переобход исправленных страниц

### Спринт 4 (Неделя 3): Validation & Monitoring
- [ ] Rich Results Test на всех типах страниц
- [ ] Прогон seo_audit.py скрипта
- [ ] Настроить мониторинг индексации (вебмастер + скрипт)
- [ ] Настроить IndexNow API

---

## 🔧 Конкретные файлы Bitrix для правок

| Задача | Файл(ы) | Тип правки |
|---|---|---|
| Canonical | `/local/templates/cifra_new/header.php` | Добавить в `<head>` |
| Clean-param | `/robots.txt` | Добавить директивы |
| Sitemap | Настройки → SEO → Sitemap + Агент `CSitemap::Generate()` | Настройка в админке |
| Title/Meta | Компоненты: `catalog.section`, `catalog.element`, `news.list`, `news.detail` | Настройки компонентов |
| JSON-LD Org | `header.php` / `footer.php` | Вставить скрипт |
| JSON-LD Product | `/local/templates/cifra_new/components/bitrix/catalog.element/.default/template.php` | В `result_modifier.php` |
| JSON-LD Breadcrumb | Компонент навигации (`bitrix:breadcrumb`) | В `template.php` |
| JSON-LD Article | `/local/templates/cifra_new/components/bitrix/news.detail/.default/template.php` | В `result_modifier.php` |
| Image resize | Настройки инфоблоков → Обработка изображений | Админка |
| Lazyload | Компоненты каталога/новостей | `template.php` |
| em-dash replace | `init.php` / `result_modifier.php` | `str_replace` |
| 404 page | `/404.php` | Создать полезную 404 |

---

## ✅ Definition of Done (Приёмка)

| Фикс | Как проверить |
|---|---|
| Sitemap | `curl -I https://xn--18-6kc5a3bxam.xn--p1ai/sitemap.xml` → 200, валидный XML |
| Canonical | View Source на 10 случайных страницах → есть `<link rel="canonical">` |
| PARSE_ERROR | Вебмастер → Страницы в поиске → исключённые → PARSE_ERROR = 0 |
| DUPLICATE | Вебмастер → исключённые → DUPLICATE < 10 (только валидные) |
| JSON-LD | Rich Results Test (Google) → 0 ошибок для Org, Product, Article, Breadcrumb |
| Title/Meta | View Source → уникальные на всех 142 SEARCHABLE |
| Images | PageSpeed / Lighthouse → WebP, lazyload, width/height, <200KB |
| em-dash | `grep -r "—" /local/templates/cifra_new/` → 0 результатов |
| IndexNow | Проверка в Bing Webmaster Tools → URL submitted |

---

## 📊 Мониторинг после фиксов

```bash
# Ежедневно (скрипт)
python monitor_indexing.py --check-all

# Еженедельно
- Вебмастер: Страницы в поиске (SEARCHABLE target: 400+)
- Вебмастер: Исключённые (DUPLICATE target: <20, PARSE_ERROR: 0)
- Позиции: Мониторинг запросов (бренд ТОП-1, коммерческие ТОП-5)
- PageSpeed: 5 ключевых URL (Mobile > 70, Desktop > 90)
```

---

*Технические фиксы приоритизированы по данным Вебмастера. Выполнять последовательно: каждый фикс открывает доступ к следующему уровню оптимизации.*