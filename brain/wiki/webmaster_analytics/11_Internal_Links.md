# Анализ внутренних ссылок (Internal Links)

**Источник:** `цифра18.рф_links_inside.tsv` (135 строк с заголовком, 134 ссылки, экспорт Яндекс.Вебмастер)  
**Период:** данные за август 2026  
**Колонки:** source_url, target_url, anchor, http_status, date_crawled, date_updated  

---

## 📊 Общая статистика

| Метрика | Значение |
|---|---|
| **Всего ссылок** | 135 |
| **Уникальных источников** | ~80 |
| **Уникальных целей** | ~60 |
| **Код 301 (редирект)** | 72 (53%) |
| **Код 404 (не найдено)** | 45 (33%) |
| **Код 502 (bad gateway)** | 9 (7%) |
| **Код 500 (server error)** | 8 (6%) |
| **Исходящие с картинок (upload/iblock)** | 104 (77%) |
| **Ссылки с /product/** | 4 |

---

## 🔴 Критические проблемы

### 1. 62 внутренние ссылки ведут на битые/проблемные страницы (404/500/502)

#### 404 — Страницы не найдены (45 ссылок):
| Источник (картинка/страница) | Целевой URL | Анкор |
|---|---|---|
| `/product/suvenirnaja-produkcija/` | `/news/magnitnye-zakladki...` | сувенирной продукции |
| `/catalog/suvenirnaya-produktsiya/shokolad-s-logotipom/` | `/catalog/suvenirnaya-produktsiya/` (500) | Шоколад с логотипом |
| `/catalog/suvenirnaya-produktsiya/igry-i-golovolomki/tetris-derevyannyy/` | `/catalog/suvenirnaya-produktsiya/igry-i-golovolomki/` (500) | Тетрис деревянный |
| `/catalog/suvenirnaya-produktsiya/sumka-shopper-bezhevaya-/` | `/catalog/suvenirnaya-produktsiya/` (404) | Сумка шоппер бежевая |
| `/catalog/suvenirnaya-produktsiya/pechat-na-kruzhkakh/belaya-kruzhka-330ml/` | `/catalog/suvenirnaya-produktsiya/pechat-na-kruzhkakh/belaya-kruzhka-330ml/` (404) | Белая кружка 330мл |
| `/catalog/suvenirnaya-produktsiya/pechat-na-kruzhkakh/belaya-kruzhka-tsvetnaya-ruchka-dno-330ml/` | тот же URL (404) | Белая кружка/цветная ручка |
| `/catalog/suvenirnaya-produktsiya/sumka-shopper/sumka-shopper-belaya-/` | тот же URL (404) | Сумка шоппер белая |
| `/catalog/suvenirnaya-produktsiya/tablichka-dlya-oplaty-s-qr-kodom/...` | тот же URL (404) | Табличка для оплаты с QR |
| `/catalog/poligrafiya/pechat-na-samokleyashchikhsya-materialakh/golograficheskie-nakleyki/` | тот же URL (404) | Сумка шоппер белая |
| `/catalog/interer/postery2/` | тот же URL (404) | Белая кружка/цветная ручка |
| `/catalog/poligrafiya/uf-pechat1/uf-pechat-do-a5-.../` | тот же URL (404) | Каталог |
| `/catalog/suvenirnaya-produktsiya/pechat-na-kruzhkakh/kruzhka-aurora-soft-tach/` | тот же URL (404) | Форма заказа |
| `/catalog/poligrafiya/beydzh-plastikovyy-54kh86mm/` | `/catalog/poligrafiya/` (502) | Бейдж пластиковый |
| `/catalog/reklama/shirokoformatnaya-pechat/pechat-na-posternoy-bumage8706/` | `/catalog/reklama/shirokoformatnaya-pechat/` (502) | Печать на постерной бумаге |

#### 500/502 — Ошибки сервера (17 ссылок):
- Главная страница `/` — 3 ссылки (500)
- `/catalog/suvenirnaya-produktsiya/` — 6 ссылок (500/502)
- `/catalog/poligrafiya/kalendari/` — 2 ссылки (500/502)
- `/catalog/poligrafiya/` — 3 ссылки (502)
- `/catalog/reklama/shirokoformatnaya-pechat/` — 1 ссылка (502)
- `/news/` — 2 ссылки (502)

---

## 🖼 Проблема: 77% ссылок идут С КАРТИНОК

**104 из 134 ссылок** — это картинки из `/upload/iblock/` и `/wp-content/`, которые ссылаются на страницы каталога.

### Примеры:
- Одна картинка календаря (`kvartalnyy_kalendar_premium_3_rekl_polya...`) ссылается на **14 РАЗНЫХ URL**:
  - `/catalog/poligrafiya/vysechnaya-produktsiya/` (опечатка в URL!)
  - `/catalog/poligrafiya/kvartalnyy-kalendar-premium-prozrachnyy-plastik/` (4 раза)
  - `/catalog/poligrafiya/listovki-tsifrovaya-pechat/pechat-listovok-a6/`
  - `/catalog/poligrafiya/kalendari/kvartalnyy-kalendar-premium-1-rekl-pole-s-figurnoy-rezkoy/`
  - `/catalog/poligrafiya/uf-pechat1/`
  - `/catalog/poligrafiya/kvartalnyy-kalendar-premium-3-rekl-polya-prozrachnyy-plastik/`
  - `/catalog/` (главная каталога)

### Последствия:
1. **Размывается вес** — одна картинка распределяет ссылки на 10+ URL
2. **Опечатки в URL** — `vysechnaya-produktsiya` вместо `suvenirnaya-produktsiya`
3. **Битые целевые страницы** — половина целей 404/500

---

## 🔗 Проблемные паттерны URL

### 1. Дублирующиеся категории (опечатки/вариации):
```
/catalog/poligrafiya/suvenirnaya-produktsiya/     ← ОПЕЧАТКА (нет в структуре)
/catalog/poligrafiya/vysechnaya-produktsiya/      ← ОПЕЧАТКА
/catalog/suvenirnaya-produktsiya/                 ← Правильный
/catalog/poligrafiya/suvenirnaya-produktsiya/     ← Не существует (404/500)
```

### 2. Устаревшие /product/ URL (4 шт.):
```
/product/suvenirnaja-produkcija/        → 404 на статью
/product/pechat-chertezhej/             → 301 на /catalog/inzhenernaya-pechat/
/product/uf-pechat/                     → 301 на /catalog/poligrafiya/beydzhi/
/product/cifrovaja-pechat/              → 301 на статью блога
```

### 3. wp-content/uploads (старый WordPress?):
```
/wp-content/uploads/2020/08/adresnaja-tablichka-izgotovlenie-izhevsk.jpg → 301 на статью
/wp-content/uploads/2019/08/pechat-na-chernyh-ruchkah...jpg → 301 на статью
```

---

## 🎯 Топ битых целевых страниц (приоритет фикса)

| Целевой URL | Входящих ссылок | Статус | Действие |
|---|---|---|---|
| `/catalog/suvenirnaya-produktsiya/` | 12 | 500/404 | **Критично** — раздел сувенирки |
| `/catalog/poligrafiya/kalendari/` | 4 | 500/502 | **Высоко** — сезонный раздел |
| `/catalog/suvenirnaya-produktsiya/pechat-na-kruzhkakh/belaya-kruzhka-330ml/` | 4 | 404 | **Высоко** — товар |
| `/catalog/suvenirnaya-produktsiya/sumka-shopper/sumka-shopper-belaya-/` | 3 | 404 | **Высоко** — товар |
| `/catalog/suvenirnaya-produktsiya/pechat-na-kruzhkakh/belaya-kruzhka-tsvetnaya-ruchka-dno-330ml/` | 3 | 404 | **Высоко** — товар |
| `/catalog/suvenirnaya-produktsiya/tablichka-dlya-oplaty-s-qr-kodom/...` | 4 | 404 | **Средне** — товар |
| `/catalog/poligrafiya/` | 3 | 502 | **Критично** — корень каталога |
| `/` (главная) | 3 | 500 | **Критично** — главная |
| `/news/` | 2 | 502 | **Высоко** — блог |

---

## 📋 План фиксов внутренних ссылок

### Спринт 1 (Дни 1-2): Критичные 404/500 целевые страницы
- [ ] Исправить `/catalog/suvenirnaya-produktsiya/` — вернуть 200 OK
- [ ] Исправить `/catalog/poligrafiya/kalendari/` — вернуть 200 OK
- [ ] Исправить `/catalog/poligrafiya/` — вернуть 200 OK
- [ ] Исправить главную `/` — вернуть 200 OK (хостинг?)
- [ ] Восстановить/перенаправить 7 битых товаров сувенирки

### Спринт 2 (Дни 3-4): Картинки-хотлинки
- [ ] Найти в шаблоне каталога/товара вывод `alt`/`title` с ссылками на картинках
- [ ] Убрать ссылки с картинок на несуществующие URL (опечатки)
- [ ] Настроить: картинка товара → ссылка на ТУ ЖЕ страницу товара (не на категории)

### Спринт 3 (День 5): Устаревшие URL
- [ ] 301 редиректы: `/product/*` → актуальные SEF URL
- [ ] Удалить/перенаправить `/catalog/poligrafiya/suvenirnaya-produktsiya/` (опечатка)
- [ ] Удалить/перенаправить `/catalog/poligrafiya/vysechnaya-produktsiya/` (опечатка)

### Спринт 4 (Неделя 2): Анкоры и качество
- [ ] Анкоры «Популярные услуги» (4 раза на главной) → убрать/заменить на релевантные
- [ ] Анкоры «ОК. Наши менеджеры...» (формы) — убрать с картинок
- [ ] Анкоры «Каталог» на картинках — заменить на название товара
- [ ] Проверить все `alt` у картинок (сейчас пустые или мусор)

---

## 📊 Экспорты

- `exports/internal_links_broken.csv` — 62 битых ссылки с источниками
- `exports/internal_links_by_status.csv` — группировка по статусам
- `exports/internal_links_image_hotlinks.csv` — 104 ссылки с картинок
- `exports/internal_links_typos.csv` — опечатки в URL

---

*Анализ на 2026-09-23. Данные Яндекс.Вебмастер «Внутренние ссылки».*