# Инструкции для разработчика (Bitrix) — Phase 0 Fixes
## ЦИФРА18: Типография «Цифра» — Ижевск

**Проект:** `/Users/user/Projects/цифра 2025/2026/scripts/dev-fixes/bitrix_phase0_fixes.md`  
**Цель:** Исправить 5 Blocking findings за 1-2 дня силами 1 разработчика Bitrix  
**Шаблон:** `/local/templates/cifra_new/`  
**CMS:** 1С-Битрикс 23.300 (UTF-8, SITE_ID=s1)

---

## 🔴 B1: Sitemap — все 23 URLs возвращают 404

### Проблема
В `robots.txt` прописаны:
```
sitemap: https://xn--18-6kc5a3bxam.xn--p1ai/shop/sitemap.xml
sitemap: https://xn--18-6kc5a3bxam.xn--p1ai/shop/sitemapindex.xml
... и 21 файл sitemap-hot-*.xml
```
Все возвращают HTTP 404.

### Причина
В Битриксе генерация sitemap настроена на папку `/shop/`, но либо:
1. Агент генерации не запускается (настройки → Инструменты → Агенты)
2. Путь в настройках SEO не совпадает с реальным
3. Нет прав на запись в папку

### Решение (пошагово)

#### 1. Проверка настроек SEO
```
Админка → Настройки → Настройки продукта → Настройки модулей → SEO
Вкладка "Карта сайта":
- [x] Включить генерацию карты сайта
- Путь к файлу карты сайта: /sitemap.xml (НЕ /shop/sitemap.xml!)
- Имя файла индекса: sitemapindex.xml
- Макс. ссылок в файле: 50000
- Макс. размер файла: 50MB
```

#### 2. Настройка агента генерации
```
Админка → Настройки → Инструменты → Агенты
Найти: `CSitemap::Generate();`
- Активен: Да
- Интервал: 86400 (раз в сутки) или 3600 (раз в час для активного каталога)
- Дата следующего запуска: сегодня/сейчас
```

#### 3. Проверка прав на запись
Папка `/bitrix/sitemap/` или корень сайта должны быть writable для пользователя веб-сервера.

#### 4. Запуск вручную (для теста)
```php
// В консоли или через /bitrix/admin/cat_sitemap.php
require_once($_SERVER["DOCUMENT_ROOT"]."/bitrix/modules/main/include/prolog_admin_before.php");
if (CModule::IncludeModule("seo")) {
    CSitemap::Generate();
    echo "Sitemap generated!";
}
```

#### 5. Обновление robots.txt
После генерации — проверить реальные URLs и обновить robots.txt:
```
# УБРАТЬ старые /shop/ URLs
# ДОБАВИТЬ реальные:
Sitemap: https://xn--18-6kc5a3bxam.xn--p1ai/sitemap.xml
Sitemap: https://xn--18-6kc5a3bxam.xn--p1ai/sitemapindex.xml
# Если есть мобильная версия:
Sitemap: https://xn--18-6kc5a3bxam.xn--p1ai/sitemapmobileindex.xml
```

#### 6. Проверка в GSC/Яндекс.Вебмастер
Добавить новый sitemap.xml в панели вебмастеров.

---

## 🔴 B2: Canonical tags — отсутствуют на всех страницах

### Проблема
Нет тега `<link rel="canonical" href="...">` ни на одной странице.

### Решение: Добавить в `header.php` шаблона

**Файл:** `/local/templates/cifra_new/header.php`  
**Место:** внутри `<head>`, после `<title>` и meta тегов

```php
<?php
// Canonical URL для текущей страницы
$canonicalUrl = $APPLICATION->GetCurPageParam('', ['PAGEN_1', 'SORT', 'ORDER', 'set_filter', 'clear_cache'], true);
// Полный URL с протоколом и доменом
$canonicalFull = 'https://' . $_SERVER['HTTP_HOST'] . $canonicalUrl;
// Для главной — без лишних слешей
if ($canonicalFull === 'https://' . $_SERVER['HTTP_HOST'] . '/') {
    $canonicalFull = 'https://' . $_SERVER['HTTP_HOST'] . '/';
}
?>
<link rel="canonical" href="<?= htmlspecialcharsbx($canonicalFull) ?>">
```

### Альтернатива: через компонент `main.seo` (если включен)
В настройках компонента `bitrix:main.seo` на страницах — включить "Добавлять canonical".

### Важно для пагинации
На страницах каталога с `?PAGEN_1=N`:
```php
// В component_epilog или result_modifier каталога
if (isset($_REQUEST['PAGEN_1']) && intval($_REQUEST['PAGEN_1']) > 1) {
    // Canonical на первую страницу категории БЕЗ пагинации
    $canonicalUrl = $APPLICATION->GetCurPageParam('', ['PAGEN_1'], true);
} else {
    $canonicalUrl = $APPLICATION->GetCurPageParam('', ['PAGEN_1', 'SORT', 'ORDER'], true);
}
```

---

## 🔴 B3: Meta Description = "Description" (placeholder)

### Проблема
На главной и в блоге: `<meta name="description" content="Description">`

### Причина
В настройках компонентов/страниц не заполнено поле "Описание страницы" (meta description).

### Решение по типам страниц:

#### 1. Главная страница (`/index.php` или `/`)
```php
// В /index.php или в настройках главной страницы (режим правки → Свойства страницы)
$APPLICATION->SetPageProperty("description", "Типография «Цифра» в Ижевске: цифровая и широкоформатная печать, сувенирная продукция, мерч, стенды. Калькулятор цен онлайн. Сроки от 1 часа. Доставка по РФ.");
```

#### 2. Разделы каталога (Компонент `bitrix:catalog.section`)
В настройках компонента (`.parameters.php` или через админку):
```
Поле "Установить описание страницы" (meta description):
- Источник: Свойство раздела "Описание" (UF_DESCRIPTION)
- Или: Автоматически из первого абзаца описания раздела
- Шаблон: "[Название раздела] в Ижевске: цены, калькулятор, заказать онлайн. [Краткое описание 120-160 символов]"
```

#### 3. Детальные страницы товаров/услуг (`bitrix:catalog.element`)
```
Настройка компонента:
- Meta description: Свойство товара "Описание" (PREVIEW_TEXT) или DETAIL_TEXT (первые 160 симв.)
- Шаблон: "Купить [Название] в Ижевске от [Цена] руб. [Краткая спецпредложение]. Калькулятор, доставка, примеры работ."
```

#### 4. Новости/Блог (`bitrix:news.list` + `bitrix:news.detail`)
**Список (`news.list`):**
```php
$APPLICATION->SetPageProperty("description", "Новости и статьи типографии «Цифра»: технологии печати, советы по подготовке макетов, кейсы, новые материалы. Блог для бизнеса и дизайнеров.");
```

**Детальная (`news.detail`):**
В настройках инфоблока "Новости" → Поле "Описание для поисковиков" (или PREVIEW_TEXT):
```
Автоматически: первые 160 символов PREVIEW_TEXT статьи
Ручной контроль: заполнить поле "Meta Description" в админке у каждой статьи
```

#### 5. Универсальный фолбэк (в `header.php` или `footer.php`)
```php
<?php
// Если description не задан — генерируем из title + h1
if (!$APPLICATION->GetPageProperty("description")) {
    $title = $APPLICATION->GetTitle();
    $h1 = $APPLICATION->GetProperty("h1") ?: $title;
    $fallback = mb_substr(strip_tags($h1 . ". " . $title), 0, 155) . "...";
    $APPLICATION->SetPageProperty("description", $fallback);
}
?>
<meta name="description" content="<?= htmlspecialcharsbx($APPLICATION->GetPageProperty("description")) ?>">
```

---

## 🔴 B4: 5 H1 на главной странице

### Проблема
HTML главной:
```html
<h2>Сервис</h2>
<h1>Сервис</h1>           <!-- Дубликат -->
<h2>Качество и скорость</h2>
<h1>Качество и скорость</h1>  <!-- Дубликат -->
<h1>89% положительных отзывов</h1>
<h1>Новости</h1>
<h1>Продукция</h1>
```

### Правильная структура
```html
<h1>Типография «Цифра» — цифровая и широкоформатная печать в Ижевске</h1>
  <h2>Сервис для вашего бизнеса</h2>
    <h3>Реализация эксклюзивных проектов</h3>
    <h3>Сроки «вчера»</h3>
    <h3>Индивидуальный подход</h3>
  <h2>Качество и скорость</h2>
  <h2>Отзывы клиентов (89% положительных)</h2>
  <h2>Новости и статьи</h2>
  <h2>Продукция: полиграфия, сувенирка, широкоформат</h2>
```

### Решение в файлах шаблона

**Файл:** `/local/templates/cifra_new/index.php` (или включаемые области)

#### Вариант А: Если блоки — это включаемые области (`include_component` или `include_area`)
1. Найти компоненты/области, выводящие H1
2. В параметрах компонента или в коде области: заменить `<h1>` на `<h2>`
3. Добавить один общий H1 в начале `index.php`:
```php
<h1>Типография «Цифра» — цифровая и широкоформатная печать в Ижевске</h1>
```

#### Вариант Б: Если это статичный HTML в `index.php`
Найти и заменить:
```php
// БЫЛО:
<h1>Сервис</h1>
<h1>Качество и скорость</h1>
<h1>89% положительных отзывов</h1>
<h1>Новости</h1>
<h1>Продукция</h1>

// СТАЛО:
<h1>Типография «Цифра» — цифровая и широкоформатная печать в Ижевске</h1>
<h2>Сервис для вашего бизнеса</h2>
<h2>Качество и скорость</h2>
<h2>89% положительных отзывов</h2>
<h2>Новости и статьи</h2>
<h2>Продукция</h2>
```

#### Вариант В: Если блоки — это компоненты `bitrix:news.list` / `bitrix:catalog.section.list`
В шаблонах компонентов (`.default/template.php`):
```php
// Заменить
<h1><?= $arItem['NAME'] ?></h1>
// На
<h2><?= $arItem['NAME'] ?></h2>
```

---

## 🔴 B5: JSON-LD Schema — отсутствует полностью

### Нужные типы схем (по приоритету)

| Страница | Тип Schema.org | Где добавить |
|---|---|---|
| Главная / О нас | `Organization` + `LocalBusiness` | `header.php` / `footer.php` / `about/index.php` |
| Категории каталога | `ItemList` + `CollectionPage` | `catalog.section` template |
| Товары/Услуги | `Product` + `Offer` + `AggregateRating` | `catalog.element` template |
| Новости/Статьи | `Article` / `BlogPosting` | `news.detail` template |
| Все страницы | `BreadcrumbList` | `header.php` или компонент навигации |
| Контакты | `ContactPage` | `contacts/index.php` |

### 1. Organization + LocalBusiness (в `header.php` или `footer.php`)

```php
<?php
$orgData = [
    "@context" => "https://schema.org",
    "@type" => ["Organization", "LocalBusiness"],
    "@id" => "https://xn--18-6kc5a3bxam.xn--p1ai/#organization",
    "name" => "Типография «Цифра»",
    "alternateName" => "Цифра18",
    "url" => "https://xn--18-6kc5a3bxam.xn--p1ai",
    "logo" => "https://xn--18-6kc5a3bxam.xn--p1ai/local/templates/cifra_new/img/svg/logo.svg",
    "description" => "Типография «Цифра» в Ижевске: цифровая и широкоформатная печать, сувенирная продукция, мерч, стенды, интерьерная печать. Собственное производство, сроки от 1 часа.",
    "telephone" => ["+7-965-842-32-41", "+7-3412-32-32-41"],
    "email" => "izhcifra@yandex.ru",
    "address" => [
        "@type" => "PostalAddress",
        "streetAddress" => "ул. 7-я Подлесная, д. 34",
        "addressLocality" => "Ижевск",
        "addressRegion" => "Удмуртская Республика",
        "postalCode" => "426069",
        "addressCountry" => "RU"
    ],
    "geo" => [
        "@type" => "GeoCoordinates",
        "latitude" => "56.8519",  // Уточнить реальные координаты!
        "longitude" => "53.2033"
    ],
    "openingHoursSpecification" => [
        "@type" => "OpeningHoursSpecification",
        "dayOfWeek" => ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "opens" => "09:00",
        "closes" => "18:00"
    ],
    "priceRange" => "₽₽",
    "currency" => "RUB",
    "paymentAccepted" => ["Cash", "CreditCard", "BankTransfer"],
    "sameAs" => [
        "https://vk.com/cifra18",           // Уточнить реальные!
        "https://t.me/cifra18",
        "https://youtube.com/@cifra18",
        "https://dzen.ru/cifra18"
    ]
];
?>
<script type="application/ld+json">
<?= json_encode($orgData, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT) ?>
</script>
```

### 2. BreadcrumbList (в компоненте навигации или `header.php`)

```php
<?php
// Получаем цепочку навигации
$navChain = $APPLICATION->GetNavChain();
$breadcrumbs = [];
$position = 1;
foreach ($navChain as $item) {
    $breadcrumbs[] = [
        "@type" => "ListItem",
        "position" => $position++,
        "name" => $item["TITLE"],
        "item" => "https://xn--18-6kc5a3bxam.xn--p1ai" . $item["LINK"]
    ];
}
// Добавляем текущую страницу (если не в цепочке)
$currentTitle = $APPLICATION->GetTitle();
$breadcrumbs[] = [
    "@type" => "ListItem",
    "position" => $position,
    "name" => $currentTitle,
    "item" => "https://xn--18-6kc5a3bxam.xn--p1ai" . $APPLICATION->GetCurPageParam()
];

$bcData = [
    "@context" => "https://schema.org",
    "@type" => "BreadcrumbList",
    "itemListElement" => $breadcrumbs
];
?>
<script type="application/ld+json">
<?= json_encode($bcData, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) ?>
</script>
```

### 3. Product Schema (в шаблоне `catalog.element` — `/local/templates/cifra_new/components/bitrix/catalog.element/.default/template.php`)

```php
<?php
// В result_modifier.php или прямо в template.php
$priceValue = $arResult['MIN_PRICE']['PRICE'] ?? 0;
$currency = $arResult['MIN_PRICE']['CURRENCY'] ?? 'RUB';
$availability = $arResult['CATALOG_QUANTITY'] > 0 
    ? "https://schema.org/InStock" 
    : "https://schema.org/OutOfStock";

$productData = [
    "@context" => "https://schema.org",
    "@type" => "Product",
    "@id" => "https://xn--18-6kc5a3bxam.xn--p1ai" . $arResult['DETAIL_PAGE_URL'] . "#product",
    "name" => $arResult['NAME'],
    "description" => strip_tags($arResult['PREVIEW_TEXT'] ?? $arResult['DETAIL_TEXT'] ?? ''),
    "image" => $arResult['DETAIL_PICTURE']['SRC'] ?? $arResult['PREVIEW_PICTURE']['SRC'] ?? [],
    "brand" => [
        "@type" => "Brand",
        "name" => "Цифра"
    ],
    "sku" => $arResult['PROPERTIES']['ARTNUMBER']['VALUE'] ?? $arResult['ID'],
    "offers" => [
        "@type" => "Offer",
        "@id" => "https://xn--18-6kc5a3bxam.xn--p1ai" . $arResult['DETAIL_PAGE_URL'] . "#offer",
        "price" => $priceValue,
        "priceCurrency" => $currency,
        "availability" => $availability,
        "seller" => [
            "@type" => "Organization",
            "name" => "Типография «Цифра»",
            "@id" => "https://xn--18-6kc5a3bxam.xn--p1ai/#organization"
        ],
        "priceValidUntil" => date('Y-m-d', strtotime('+1 year'))
    ],
    "aggregateRating" => [
        "@type" => "AggregateRating",
        "ratingValue" => "4.8",  // Уточнить из отзывов!
        "reviewCount" => "127",  // Уточнить!
        "bestRating" => "5",
        "worstRating" => "1"
    ]
];
// Добавить FAQ schema если есть FAQ на странице
if (!empty($arResult['PROPERTIES']['FAQ']['VALUE'])) {
    $productData['mainEntity'] = [
        "@type" => "Question",
        "name" => "Частые вопросы",
        "acceptedAnswer" => [
            "@type" => "Answer",
            "text" => "Ответы на популярные вопросы..."
        ]
    ];
}
?>
<script type="application/ld+json">
<?= json_encode($productData, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) ?>
</script>
```

### 4. Article Schema (в шаблоне `news.detail`)

```php
<?php
$articleData = [
    "@context" => "https://schema.org",
    "@type" => "Article",  // или "BlogPosting"
    "@id" => "https://xn--18-6kc5a3bxam.xn--p1ai" . $arResult['DETAIL_PAGE_URL'] . "#article",
    "headline" => $arResult['NAME'],
    "description" => strip_tags($arResult['PREVIEW_TEXT'] ?? ''),
    "image" => $arResult['DETAIL_PICTURE']['SRC'] ?? [],
    "datePublished" => $arResult['ACTIVE_FROM'],  // Формат ISO 8601
    "dateModified" => $arResult['TIMESTAMP_X'] ?? $arResult['ACTIVE_FROM'],
    "author" => [
        "@type" => "Person",
        "name" => $arResult['PROPERTIES']['AUTHOR']['VALUE'] ?? "Типография «Цифра»"
    ],
    "publisher" => [
        "@type" => "Organization",
        "name" => "Типография «Цифра»",
        "@id" => "https://xn--18-6kc5a3bxam.xn--p1ai/#organization",
        "logo" => [
            "@type" => "ImageObject",
            "url" => "https://xn--18-6kc5a3bxam.xn--p1ai/local/templates/cifra_new/img/svg/logo.svg"
        ]
    ],
    "mainEntityOfPage" => [
        "@type" => "WebPage",
        "@id" => "https://xn--18-6kc5a3bxam.xn--p1ai" . $arResult['DETAIL_PAGE_URL']
    ]
];
?>
<script type="application/ld+json">
<?= json_encode($articleData, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) ?>
</script>
```

---

## ✅ Чек-лист приёмки (Definition of Done)

| Fix | Файл(ы) | Как проверить |
|---|---|---|
| **B1 Sitemap** | Настройки SEO, Агенты, `/bitrix/sitemap/` | `curl -I https://xn--18-6kc5a3bxam.xn--p1ai/sitemap.xml` → 200 OK, валидный XML |
| **B2 Canonical** | `header.php`, `catalog.section/component_epilog.php` | View Source → есть `<link rel="canonical" href="...">` на всех страницах |
| **B3 Meta Desc** | Настройки компонентов, `index.php`, `header.php` фолбэк | View Source → уникальный `meta name="description"` на главной, категориях, товарах, новостях |
| **B4 H1** | `index.php`, шаблоны компонентов | View Source → ровно 1 `<h1>` на каждой странице, на главной — с главным ключом |
| **B5 JSON-LD** | `header.php`, `footer.php`, шаблоны компонентов | Rich Results Test (Google) → 0 ошибок для Organization, Product, Article, BreadcrumbList |

---

## 🛠 Полезные команды для разработчика

```bash
# Проверка sitemap
curl -s "https://xn--18-6kc5a3bxam.xn--p1ai/sitemap.xml" | head -20

# Проверка canonical на странице
curl -s "https://xn--18-6kc5a3bxam.xn--p1ai/catalog/poligrafiya/vizitki/" | grep -i canonical

# Проверка JSON-LD
curl -s "https://xn--18-6kc5a3bxam.xn--p1ai/catalog/poligrafiya/vizitki/vizitki-na-krafte/" | grep -A 50 'application/ld+json'

# Валидация JSON-LD (локально)
# Сохранить HTML → https://validator.schema.org/ или https://search.google.com/test/rich-results
```

---

## 📝 Примечания

1. **Координаты geo** — уточнить точные координаты офиса/производства в Яндекс.Картах
2. **SameAs ссылки** — уточнить реальные соцсети (VK, Telegram, YouTube, Дзен)
3. **AggregateRating** — взять реальные данные из отзывов (на сайте 89% положительных, но нужно ratingValue и reviewCount)
4. **OpeningHours** — уточнить реальный график работы
5. **Тестирование** — после каждого фикса прогонять `seo_audit.py` скрипт для верификации

---

*Создано для разработчика Bitrix. Вопросы — в чат проекта.*