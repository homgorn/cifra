# Анализ страниц: Индексация, Статусы, Ошибки

**Источник:** `цифра18.рф_d4614eeeb7cd1a4c18473d6d.csv` (717 URL)
**Уточнение от 2026-09-27:** 717: это размер выгрузки из панели, а не счётчик
сайта. По API Вебмастера `summary` в поиске 708 страниц, исключено 477.
Числа ниже в разделах про статусы и ошибки посчитаны по выборке в 717 URL,
общие показатели индексации берутся из API. Расхождение объясняется тем, что
панель отдаёт список проверенных URL, а счётчик в поиске считает страницы,
которые действительно попали в выдачу.
**Дата экспорта:** 2026-09-20  

---

## 📊 Общая статистика

| Статус | Кол-во | % | Приоритет |
|---|---|---|---|
| **PARSE_ERROR** | 251 | 35.0% | 🔴 **КРИТИЧНО** |
| **SEARCHABLE** | 142 | 19.8% | 🟢 Цель |
| **DUPLICATE** | 128 | 17.9% | 🔴 **КРИТИЧНО** |
| **REDIRECT_NOTSEARCHABLE** | 89 | 12.4% | 🟠 ВЫСОКО |
| **OTHER** | 72 | 10.0% | 🟡 СРЕДНЕ |
| **BAD_QUALITY** | 22 | 3.1% | 🟠 ВЫСОКО |
| **HTTP_ERROR** | 13 | 1.8% | 🔴 **КРИТИЧНО** |
| **ИТОГО** | **717** | **100%** | |

### HTTP коды
| Код | Кол-во | Страницы |
|---|---|---|
| 200 | 601 | 83.8% |
| 301 | 100 | 13.9% |
| 404 | 13 | 1.8% |
| 302 | 3 | 0.4% |

---

## 🔴 PARSE_ERROR: 251 страница (35%)

**Это главная проблема.** Робот скачивает страницу (HTTP 200), но не может распарсить контент.

### Причины (по справке Яндекса):
- Битый/невалидный HTML
- Проблемы с кодировкой (UTF-8 vs Windows-1251)
- Тяжёлый JS-рендеринг (контент подгружается после загрузки)
- Блокировка CSS/JS в robots.txt
- Сервер отдаёт сжатый контент без правильных заголовков

### Топ примеры PARSE_ERROR:
```
https://xn--18-6kc5a3bxam.xn--p1ai/shop/110177348
https://xn--18-6kc5a3bxam.xn--p1ai/100720014.html
https://xn--18-6kc5a3bxam.xn--p1ai/101871888.html
... (200+ страниц с паттерном /123456789.html)
https://xn--18-6kc5a3bxam.xn--p1ai/catalog/detail.php?ID=1137
https://xn--18-6kc5a3bxam.xn--p1ai/catalog/detail.php?ID=1243
https://xn--18-6kc5a3bxam.xn--p1ai/catalog/detail.php?ID=417
https://xn--18-6kc5a3bxam.xn--p1ai/catalog/detail.php?ID=420
https://xn--18-6kc5a3bxam.xn--p1ai/catalog/detail.php?ID=426
https://xn--18-6kc5a3bxam.xn--p1ai/catalog/detail.php?ID=44
... (много detail.php?ID=)
```

### Паттерны PARSE_ERROR:
1. **`/shop/110177348`**: 1 страница (но в sitemap 23 файла /shop/)
2. **`/123456789.html`**: ~200 страниц (старые ID товаров? Битрикс генерация)
3. **`/catalog/detail.php?ID=XXX`**: ~30 страниц (параметрические URL старый каталог)
4. **`/1229-2/`**: «Сайт заблокирован хостинг-провайдером» (проблема хостинга)

### План фикса PARSE_ERROR:
| Приоритет | Действие | Файлы/Настройки |
|---|---|---|
| 1 | Удалить/заблокировать в robots.txt `/shop/` и `/123456789.html` | robots.txt, настройки SEO |
| 2 | Поставить canonical на `/catalog/detail.php?ID=` → SEF URL | header.php, component_epilog |
| 3 | Проверить валидность HTML на ключевых страницах | W3C Validator, Яндекс.Валидатор |
| 4 | Настроить server-side rendering для каталога | Bitrix: `component_epilog`, `result_modifier` |
| 5 | Запросить переобход исправленных страниц | Вебмастер → Переобход |

---

## 🔴 DUPLICATE: 128 страниц (18%)

Страницы-дубликаты, которые Яндекс исключил из поиска в пользу оригиналов.

### Примеры с целями дублей (из events.csv):
```
/catalog/poligrafiya/kalendari/kvartalnyy-kalendar-premium-prozrachnyy-plastik-s-1-rekl-polem/
    → DUPLICATE of /catalog/poligrafiya/kalendari/kvartalnyy-kalendar-premium-1-rekl-pole-s-figurnoy-rezkoy/

/catalog/poligrafiya/paketnoe-laminirovanie/
    → DUPLICATE of /catalog/poligrafiya/laminirovanie/paketnoe-laminirovanie/

/catalog/poligrafiya/kraft-pakety-podarochnye/
    → DUPLICATE of /catalog/poligrafiya/pakety/kraft-pakety-podarochnye/

/catalog/suvenirnaya-produktsiya/pechat-na-samokleyashchikhsya-materialakh/figurnye-nakleyki-na-samokleyushcheysya-plenke-zerkalnoe-serebro/
    → DUPLICATE of /catalog/poligrafiya/figurnye-nakleyki-na-samokleyushcheysya-plenke-zerkalnoe-serebro/

/catalog/detail.php?ID=1243
    → DUPLICATE of /catalog/

/catalog/inzhenernaya-pechat/broshyurovka/pereplet-na-metallicheskuyu-pruzhinu-3-1/
    → DUPLICATE of /catalog/inzhenernaya-pechat/pereplet-na-metallicheskuyu-pruzhinu-3-1/
```

### Паттерны дублей:
1. **Два URL на один товар**: старый `/catalog/.../item/` и новый `/catalog/.../item2/`
2. **Категория дублирует подкатегорию**: `/paketnoe-laminirovanie/` vs `/laminirovanie/paketnoe-laminirovanie/`
3. **detail.php дублирует SEF**: параметрические URL vs ЧПУ
4. **Слеши в конце**: `/catalog/` vs `/catalog` (Bitrix часто генерирует оба)

### План фикса DUPLICATE:
| Приоритет | Действие |
|---|---|
| 1 | Глобальный `rel=canonical` в `header.php` на все страницы |
| 2 | Настроить `Clean-param` в robots.txt для `ID`, `PAGEN_1`, `SORT`, `ORDER` |
| 3 | 301 редиректы: `detail.php?ID=XXX` → SEF URL товара |
| 4 | Объединить дублирующие категории (оставить одну структуру) |
| 5 | Проверить `rel=canonical` на пагинации (на 1-ю страницу) |

---

## 🟠 REDIRECT_NOTSEARCHABLE: 89 страниц (12%)

Страницы делают редирект, в поиске только цель.

### Примеры:
```
/brendirovanie-avtomobilej-pishite-https-vk-com-cifraprint18-zvonite-79658423241/ → 404
/shop/... → (редиректы на основные страницы)
/detail.php?ID=XXX → (редиректы на SEF)
```

### Проблемы:
- Цепочки редиректов (A→B→C) теряют вес
- Редиректы на 404 страницы
- Редиректы с параметров на главные разделы (теряется релевантность)

### План:
1. Аудит всех 301/302 редиректов (Screaming Frog / Netpeak)
2. Убрать цепочки: прямой редирект на финальный URL
3. Редиректы на 404 → убрать или поставить 410 Gone

---

## 🟡 OTHER: 72 страницы (10%)

Нет актуальных данных у робота. Основные причины:
- Страницы недавно добавлены/изменены
- Робот не обходил давно
- Низкий приоритет обхода

### Действие:
- Запросить переобход через Вебмастер (приоритетные 20 URL/день)
- Проверить внутренние ссылки на эти страницы
- Добавить в sitemap с `lastmod`

---

## 🟠 BAD_QUALITY: 22 страницы (3%)

Алгоритм качества исключил из выдачи.

### Вероятные кандидаты (по patterns из events.csv):
- Страницы с title="Каталог", meta="Description"
- Тонкие страницы товаров без описания
- Страницы с дублирующимся контентом

### План:
1. Выделить эти 22 URL из полного экспорта
2. Аудит контента: уникальность, объём, E-E-A-T
3. Добавить: уникальное описание, фото, видео, отзывы, FAQ, таблицы сравнения
4. Запросить переобход

---

## 🔴 HTTP_ERROR: 13 страниц

Ошибки сервера (5xx) или таймауты.

### Примеры:
```
/brendirovanie-avtomobilej-pishite-https-vk-com-cifraprint18-zvonite-79658423241/ → 404
```
(остальные 12 нужно выделить из полного списка)

### План:
1. Проверить логи сервера за последние 30 дней
2. Настроить мониторинг uptime (UptimeRobot / Яндекс.Метрика)
3. Исправить причины 5xx (PHP лимиты, БД, хостинг)
4. 404 страницы → 410 Gone или полезный 404 с поиском/меню

---

## ✅ SEARCHABLE: 142 страницы (19.8%)

Страницы в поиске. Но качество сниппетов требует проверки.

### Проблемы качества среди SEARCHABLE:
| Проблема | Кол-во | Пример |
|---|---|---|
| Title = "Каталог" | ~40 | `/catalog/detail.php?ID=124` |
| Meta Description = "Description" | ~40 | То же |
| Пустой title | ~5 | `/account/docs/verstka/nakladnaya_ooo.php` |
| Дубликаты title/meta | Много | Каталог разделы |

### Топ SEARCHABLE страницы (потенциальные деньги):
```
/ - Главная
/catalog/ - Каталог (но title="Каталог")
/catalog/interer/ - Интерьер (хороший title/desc)
/catalog/interer/fotooboi/ - Фотообои (коммерческий)
/catalog/interer/fotopostery... - Фотопостеры
/catalog/interer/kartiny-na-kholste/ - Картины на холсте
/catalog/inzhenernaya-pechat/ - Инженерная печать
/catalog/mobilnye-stendy/ - Мобильные стенды
/catalog/poligrafiya/ - Полиграфия
/catalog/suvenirnaya-produktsiya/ - Сувенирка
/news/ - Новости (title="Новости" - слабо)
/about/ - О нас (нет в списке, проверить)
```

### Коэффициент индексации по разделам (из structure.csv):
| Раздел | Индексировано | Загружено | В поиске | % в поиске |
|---|---|---|---|---|
| /catalog | 831 | 565 | 51 | **6.1%** ❌ |
| /poligrafiya | 342 | 223 | 21 | **6.1%** ❌ |
| /suvenirnaya-produktsiya | 340 | 256 | 21 | **6.2%** ❌ |
| /inzhenernaya-pechat | 28 | 24 | 2 | **7.1%** ❌ |
| /mobilnye-stendy | 16 | 13 | 1 | **6.3%** ❌ |
| /news | 142 | 140 | 9 | **6.3%** ❌ |
| /shop | 388 | 0 | 24 | **6.2%** ❌ (тех. мусор) |
| /detail.php | 28 | 11 | 2 | **7.1%** ❌ |
| **КОРЕНЬ /** | 0 | 741 | 100 | н/д |

**Вывод:** коэффициент **6-7%** по каталогу: катастрофически низко. Норма 60%+.

---

## 📋 Экспорты для работы

Файлы в `exports/`:
- `searchable_pages.csv`, 142 URL с title/meta для аудита сниппетов
- `duplicate_pages.csv`, 128 URL с целями для канонизации
- `parse_error_pages.csv`, 251 URL для технического аудита
- `redirect_pages.csv`, 89 URL для аудита редиректов
- `bad_quality_pages.csv`, 22 URL для контент-аудита
- `http_error_pages.csv`, 13 URL для проверки сервера
- `other_pages.csv`, 72 URL для запроса переобхода

---

## 🎯 Ключевые действия (Priority 1)

1. **Sitemap**: починить генерацию, убрать `/shop/` из robots.txt
2. **Canonical**: глобальный в header.php + Clean-param в robots.txt
3. **PARSE_ERROR**: заблокировать `/shop/`, `/*.html` (старые ID), починить `detail.php`
4. **DUPLICATE**: 301 редиректы старых URL на SEF, объединение категорий
5. **Template fixes**: уникальные title/meta для всех 142 searchable страниц
6. **Переобход**: запросить на 20 приоритетных URL в день

---

*Полный список URL в `exports/`. Для работы с Excel: импортируйте CSV.*