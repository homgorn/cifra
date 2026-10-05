#!/usr/bin/env node
/**
 * render.js — собирает готовый лендинг в outDir из config.json + templates/.
 *
 * Использование:
 *   node render.js config.json [outDir=dist]
 *
 * ЧТО ДЕЛАЕТ:
 *   - index.html: подставляет скалярные {{PLACEHOLDER}} и рендерит повторяющиеся
 *     блоки (USP, методы, процесс, доверие, FAQ, каналы связи, hero-статы)
 *     в HTML-маркеры <!--MARKER-->
 *   - styles.css: копируется как есть (дизайн-система не завязана на бизнес)
 *   - script.js: подставляет только 3 бизнес-специфичных константы
 *   - catalog.js: генерируется из config.catalog через JSON.stringify —
 *     НЕ строковым темплейтингом, чтобы спецсимволы в названиях товаров
 *     (кавычки, амперсанды) не ломали JS
 *   - backend/server.js + package.json: копируются с подстановкой env-хинтов
 *
 * САМОКРИТИКА / ГРАНИЦЫ:
 *   - Экранирование в renderXxx() — минимальное (только & < >), этого хватает
 *     для HTML-текста, но НЕ для атрибутов с кавычками — если в config
 *     попадут двойные кавычки внутри title/text, атрибут может сломаться.
 *     Для продакшен-конфига с непроверенным вводом это нужно усилить.
 *   - Скрипт фейлится громко (throw), если обязательное поле конфига
 *     отсутствует — это сознательное решение: молча подставленная пустая
 *     строка в проде выглядит как баг, а не как явная ошибка конфига.
 */

const fs = require('fs');
const path = require('path');

function fail(msg) {
  console.error('ERROR:', msg);
  process.exit(1);
}

const configPath = process.argv[2];
if (!configPath) fail('Usage: node render.js <config.json> [outDir=dist]');

const outDir = process.argv[3] || 'dist';
let config;
try {
  config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
} catch (e) {
  fail(`не удалось прочитать/распарсить ${configPath}: ${e.message}`);
}

// ---- обязательные поля: явная ошибка лучше тихой пустой строки в проде ----
const REQUIRED_PATHS = [
  'business.name', 'site.domain', 'meta.title', 'meta.description',
  'contact.phoneDisplay', 'contact.phoneTel', 'contact.email', 'contact.address'
];
function getPath(obj, p) {
  return p.split('.').reduce((acc, key) => (acc && acc[key] !== undefined ? acc[key] : undefined), obj);
}
const missing = REQUIRED_PATHS.filter((p) => getPath(config, p) === undefined);
if (missing.length) fail(`в конфиге не хватает обязательных полей: ${missing.join(', ')}`);

function esc(str) {
  // Кавычки экранируются обязательно: значения из конфига попадают не только
  // в текст, но и в атрибуты (href, src, alt, title, value), и неэкранированная
  // " ломает атрибут. В текстовом узле сущности отображаются как сами кавычки.
  return String(str ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function readTemplate(...segments) {
  return fs.readFileSync(path.join(__dirname, 'templates', ...segments), 'utf8');
}

// ---------- рендер повторяющихся блоков ----------
function renderHeroStats(items) {
  return (items || []).map((s) => `          <li><b>${esc(s.value)}</b>${esc(s.label)}</li>`).join('\n');
}
function renderUspCards(items) {
  return (items || []).map((u) =>
    `      <div class="usp-card" data-reveal><h3>${esc(u.title)}</h3><p>${esc(u.text)}</p></div>`
  ).join('\n');
}
function renderMethodChips(methods) {
  return (methods || []).map((m) =>
    `        <span class="method-chip"><span class="dot"></span>${esc(m)}</span>`
  ).join('\n');
}
function renderProcessSteps(steps) {
  return (steps || []).map((s, i) => `        <div class="process-step">
          <span class="step-num">${i + 1}</span>
          <h3>${esc(s.title)}</h3>
          <p>${esc(s.text)}</p>
        </div>`).join('\n');
}
function renderTrustBadges(items) {
  return (items || []).map((b) =>
    `        <div><b>${esc(b.value)}</b><span>${esc(b.label)}</span></div>`
  ).join('\n');
}
function renderFaqItems(items) {
  return (items || []).map((f) => `        <details class="faq-item">
          <summary>${esc(f.q)}</summary>
          <p>${esc(f.a)}</p>
        </details>`).join('\n');
}
function renderContactChannels(channels) {
  if (!channels || !channels.length) {
    return '            <!-- config.contactChannels пуст — TODO: добавить реальные ссылки на мессенджеры -->';
  }
  return channels.map((c) =>
    `            <a class="channel-chip" href="${esc(c.url)}" target="_blank" rel="noopener">${esc(c.label)}</a>`
  ).join('\n');
}

// ---------- карта + кнопка «проехать» (блок 9) ----------
// config.contact.mapEmbedUrl — ссылка из Яндекс.Карт («Поделиться» → «Код для
// вставки» / конструктор карт с source=mapframe), вставляется как iframe src.
// config.contact.mapDirectionsUrl — если не задан явно, строится автоматически
// из mapLat/mapLon по схеме https://yandex.ru/maps/?rtext=~LAT,LON&rtt=auto
// (формат подтверждён документацией Яндекса: rtext принимает широту,долготу
// через запятую, тильда в начале = маршрут от текущего местоположения пользователя).
function buildDirectionsUrl(contact) {
  if (contact.mapDirectionsUrl) return contact.mapDirectionsUrl;
  if (contact.mapLat && contact.mapLon) {
    return `https://yandex.ru/maps/?rtext=~${contact.mapLat},${contact.mapLon}&rtt=auto`;
  }
  return null;
}
// ---------- карта: статичная картинка, не iframe ----------
// Раньше карта вставлялась iframe'ом со ссылкой на Яндекс.Карты, и она
// не показывалась: yandex.ru отдаёт 301 на yandex.com, а у него в
// заголовке X-Frame-Options: DENY. Браузер отказывается встраивать
// страницу во фрейм, и на месте карты оставалось пустое белое поле.
// Запрет стоит на стороне Яндекса, поэтому ссылкой его не обойти.
//
// Теперь используется статичная картинка, собранная из тайлов
// OpenStreetMap скриптом make_map.py при сборке. Плюсы: работает
// везде, не грузит сторонний iframe, не отправляет посетителя на
// чужой домен, работает без JavaScript. Кнопка маршрута по-прежнему
// ведёт на Яндекс.Карты, где карта интерактивная.
function renderMapEmbed(contact) {
  const directionsUrl = buildDirectionsUrl(contact);
  const directionsButton = directionsUrl
    ? `<a class="map-route-btn" href="${esc(directionsUrl)}" target="_blank" rel="noopener">Проложить маршрут</a>`
    : '';
  // Атрибуция обязательна по условиям использования тайлов OSM.
  const attribution = 'Данные карты: <a href="https://www.openstreetmap.org/copyright" '
    + 'target="_blank" rel="noopener">OpenStreetMap</a>, участники';

  if (contact.mapImage) {
    return `      <figure class="map-embed-wrap">
        <img src="${esc(contact.mapImage)}" alt="Карта: ${esc(contact.address)}" loading="lazy" width="768" height="512">
        <figcaption class="map-attr">${attribution}</figcaption>
      </figure>
      ${directionsButton}`;
  }

  // Запасной путь для лендинга без собранной картинки: ставим честную
  // заглушку с адресом и кнопкой маршрута, а не пустой iframe.
  return `      <div class="map-embed-wrap map-placeholder">
        <p>${esc(contact.address)}</p>
        ${directionsButton}
        <p class="map-attr">${attribution}</p>
      </div>
      <!-- TODO: собрать карту, python landings/_scrape/make_map.py --lat ... --lon ... --out assets/web/map.png --label "${esc(contact.businessName || 'Мы здесь')}", и вписать contact.mapImage в config.json -->`;
}

// ---------- реквизиты оператора ПДн в подвале ----------
// Без реквизитов страница юридически неполна, и молча прятать это нельзя.
// Но строка должна быть ЯВНЫМ ТОДО без знака em-dash: он запрещён в текстах
// для клиента, а подвал виден каждому. Формулировка совпадает с проверкой
// «TODO» в validate_landing.py, гейт 8, поэтому незаполненные реквизиты
// ловятся автоматически, а не только при чтении.
function renderLegalEntityLine(business) {
  if (!business.legalEntity) return 'Реквизиты не указаны в конфиге, TODO: запросить у заказчика';
  const { fullName, inn, ogrn } = business.legalEntity;
  const parts = [fullName, inn ? `ИНН ${inn}` : null, ogrn ? `ОГРН(ИП) ${ogrn}` : null].filter(Boolean);
  return esc(parts.join(', '));
}

// ---------- JSON-LD: LocalBusiness + FAQPage (SEO + ответы нейросетей) ----------
function buildJsonLdLocalBusiness(config) {
  const data = {
    '@context': 'https://schema.org',
    '@type': 'LocalBusiness',
    name: config.business.name,
    url: `https://${config.site.domain}`,
    telephone: config.contact.phoneTel,
    email: config.contact.email,
    address: { '@type': 'PostalAddress', streetAddress: config.contact.address }
  };
  if (config.contact.mapLat && config.contact.mapLon) {
    data.geo = { '@type': 'GeoCoordinates', latitude: config.contact.mapLat, longitude: config.contact.mapLon };
  }
  if (config.business.legalEntity?.fullName) {
    data.legalName = config.business.legalEntity.fullName;
  }
  return `<script type="application/ld+json">\n${JSON.stringify(data, null, 2)}\n</script>`;
}
function buildJsonLdFaqPage(faq) {
  if (!faq || !faq.length) return '<!-- config.faq пуст — FAQPage JSON-LD не сгенерирован -->';
  const data = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: faq.map((f) => ({
      '@type': 'Question',
      name: f.q,
      acceptedAnswer: { '@type': 'Answer', text: f.a }
    }))
  };
  return `<script type="application/ld+json">\n${JSON.stringify(data, null, 2)}\n</script>`;
}

function buildStaticMailto(cfg) {
  const subject = `Заявка с сайта ${cfg.site.domain} — ${cfg.business.name}`;
  const body = [
    'Здравствуйте!',
    '',
    `Пишу с сайта ${cfg.site.domain}.`,
    '',
    'Что хочу узнать/посчитать:',
    '— Товар/услуга: ',
    '— Количество/объём: ',
    '— Сроки: '
  ].join('\n');
  return `mailto:${cfg.contact.email}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}

// ---------- Абсолютные адреса для мета ----------
// Open Graph и canonical требуют абсолютного адреса, относительный не
// понимается ни одной площадкой. Сайт ещё не развёрнут, и путь будущей
// страницы неизвестен, поэтому он задаётся явно: config.site.basePath.
// Если поле не задано, страница считается лежащей в корне домена, и это
// написано в отчёте, а не угадано.
//
// Домен хранится в punycode, xn--18-6kc5a3bxam.xn--p1ai, и вставляется
// как есть: запись кириллицей в URL невалидна.
function absoluteUrl(path) {
  const domain = (config.site && config.site.domain) || '';
  const base = (config.site && config.site.basePath) || '';
  const slug = (config.landing && config.landing.slug) || '';
  const clean = String(path || '').replace(/^\/+/, '');
  // Каталог лежит рядом со страницей, то есть по тому же адресу, что и
  // canonical. Без slug картинка уезжала в корень домена, а страница
  // оставалась в папке, и og:image указывал бы в несуществующее место.
  return `https://${domain}${base}/${slug}/${clean}`;
}

// Канонический адрес самой страницы. slug берётся из landing, а не из
// имени папки, иначе при переносе папки адрес поменялся бы молча.
function canonicalUrl() {
  const slug = (config.landing && config.landing.slug) || '';
  const base = (config.site && config.site.basePath) || '';
  return `https://${(config.site && config.site.domain) || ''}${base}/${slug}/`;
}

// ---------- 1. index.html ----------
let html = readTemplate('index.template.html');

const scalarMap = {
  BUSINESS_NAME: esc(config.business.name),
  META_TITLE: esc(config.meta.title),
  META_DESCRIPTION: esc(config.meta.description),
  CANONICAL_URL: esc(canonicalUrl()),
  OG_IMAGE_URL: esc(absoluteUrl((config.hero && config.hero.photo) || 'assets/web/map.png')),
  PHONE_DISPLAY: esc(config.contact.phoneDisplay),
  PHONE_TEL: esc(config.contact.phoneTel),
  PHONE2_LINE: config.contact.phone2Display
    ? `<a href="tel:${esc(config.contact.phone2Tel)}">${esc(config.contact.phone2Display)}</a><br>`
    : '',
  EMAIL: esc(config.contact.email),
  EMAIL_MAILTO_STATIC: buildStaticMailto(config),
  ADDRESS: esc(config.contact.address),
  SITE_DOMAIN: esc(config.site.domain),
  HERO_EYEBROW: esc(config.hero?.eyebrow || ''),
  HERO_H1: config.hero?.h1 || '', // допускает <br> внутри — ответственность на конфиге
  HERO_LEAD: esc(config.hero?.lead || ''),
  HERO_PHOTO: esc(config.hero?.photo || ''),
  HERO_PHOTO_ALT: esc(config.hero?.photoAlt || ''),
  YMETRIKA_ID: esc(config.analytics?.yandexMetrikaId || '00000000'),
  LEGAL_ENTITY_LINE: renderLegalEntityLine(config.business)
};
for (const [key, value] of Object.entries(scalarMap)) {
  html = html.split(`{{${key}}}`).join(value);
}

const markerMap = {
  '<!--HERO_STATS-->': renderHeroStats(config.heroStats),
  '<!--USP_CARDS-->': renderUspCards(config.usp),
  '<!--METHOD_CHIPS-->': renderMethodChips(config.methods),
  '<!--PROCESS_STEPS-->': renderProcessSteps(config.process),
  '<!--TRUST_BADGES-->': renderTrustBadges(config.trustBadges),
  '<!--FAQ_ITEMS-->': renderFaqItems(config.faq),
  '<!--CONTACT_CHANNELS-->': renderContactChannels(config.contactChannels),
  '<!--MAP_EMBED-->': renderMapEmbed(config.contact),
  '<!--JSONLD_LOCALBUSINESS-->': buildJsonLdLocalBusiness(config),
  '<!--JSONLD_FAQPAGE-->': buildJsonLdFaqPage(config.faq)
};
for (const [marker, value] of Object.entries(markerMap)) {
  if (!html.includes(marker)) fail(`маркер ${marker} не найден в templates/index.template.html — шаблон и render.js рассинхронизированы`);
  html = html.replace(marker, value);
}

fs.mkdirSync(outDir, { recursive: true });

// Ассеты копируются рядом со страницей. Раньше рендер писал только
// index.html, styles.css и скрипты, и пути вида assets/web/... из конфига
// вели в пустоту: в собранном dist фотографий не было вообще, и страница
// показывала битые превью, хотя гейт их наличия проверял в исходной папке.
// Копия делается один раз и только если файл ещё не там: перезапуск
// рендера не должен заново читать десятки мегабайт картинок.
// Путь к папке лендинга. Слаг из конфига и имя папки на диске обязаны
// совпадать: слаг уходит в URL страницы и в SOURCE_DESCRIPTION лида. Если
// не совпали, ассеты молча не копировались: страница собиралась, а
// фотографии на ней оказывались битыми. Отсюда явное предупреждение,
// если папки нет.
function findLandingDir(slug) {
  if (!slug) return null;
  const p = path.join(__dirname, '..', slug);
  return fs.existsSync(path.join(p, 'assets', 'web')) ? p : null;
}

function copyAssets() {
  const landingDir = findLandingDir(config.landing?.slug || '');
  if (!landingDir) {
    console.warn(`WARN: папка лендинга для slug "${config.landing?.slug || ''}" не найдена, `
      + 'ассеты не скопированы. Фотографии на странице будут битыми.');
    return 0;
  }
  const assetsDir = path.join(landingDir, 'assets');
  // Копируется ТОЛЬКО web/, а не весь assets. Оригиналы весят 39 МБ, это
  // полноразмерные снимки с сайта заказчика, и в собранном лендинге им
  // не место: он грузит assets/web/. Копия оригиналов раздувала dist
  // с 1 МБ до 40 МБ, и это уехало бы на хостинг клиента.
  const src = path.join(assetsDir, 'web');
  const dst = path.join(outDir, 'assets', 'web');
  if (!fs.existsSync(src)) return 0;
  let copied = 0;
  const walk = (from, to) => {
    fs.mkdirSync(to, { recursive: true });
    for (const name of fs.readdirSync(from)) {
      const s = path.join(from, name);
      const d = path.join(to, name);
      if (fs.statSync(s).isDirectory()) {
        walk(s, d);
      } else if (!fs.existsSync(d)) {
        fs.copyFileSync(s, d);
        copied++;
      }
    }
  };
  walk(src, dst);
  return copied;
}

const assetsCopied = copyAssets();
fs.writeFileSync(path.join(outDir, 'index.html'), html);

// ---------- 1b. privacy.html (152-ФЗ) ----------
let privacyHtml = readTemplate('privacy.template.html');
const privacyScalarMap = {
  BUSINESS_NAME: esc(config.business.name),
  SITE_DOMAIN: esc(config.site.domain),
  LEGAL_ENTITY_LINE: renderLegalEntityLine(config.business),
  ADDRESS: esc(config.contact.address),
  EMAIL: esc(config.contact.email),
  PHONE_TEL: esc(config.contact.phoneTel),
  PHONE_DISPLAY: esc(config.contact.phoneDisplay),
  POLICY_DATE: config.business.legalEntity?.policyDate || new Date().toISOString().slice(0, 10)
};
for (const [key, value] of Object.entries(privacyScalarMap)) {
  privacyHtml = privacyHtml.split(`{{${key}}}`).join(value);
}
fs.writeFileSync(path.join(outDir, 'privacy.html'), privacyHtml);
if (!config.business.legalEntity) {
  console.warn('WARN: config.business.legalEntity не задан — на privacy.html будет "TODO" вместо реквизитов оператора ПДн. Без них страница юридически неполна.');
}

// ---------- 2. styles.css ----------
fs.copyFileSync(path.join(__dirname, 'templates', 'styles.template.css'), path.join(outDir, 'styles.css'));

// ---------- 3. script.js ----------
// Подставляются ВСЕ бизнес-специфичные константы шаблона. Список здесь и в
// script.template.js должен совпадать: константа, добавленная в шаблон без
// подстановки здесь, попадёт в dist как есть, вместе с плейсхолдером.
// Номер счётчика обязателен: '0' означает «счётчик не задан» и цели просто
// не отправятся. Молча подставить заглушку 12345678 нельзя — цели уйдут
// в чужой счётчик, и это выглядит как «аналитика работает».
const YMETRIKA_ID = String(config.analytics?.yandexMetrikaId || '0');
// Заглушки, которые встречаются в демо-конфигах. Подстановка теперь следует за
// конфигом, и это правильно, но вместе с тем config.example.json несёт в себе
// 12345678: рендер без ворнинга собрал бы страницу, отправляющую цели в
// чужой счётчик. Промах по счётчику не виден ни в HTML, ни в консоли без
// сверки, поэтому проверка явная.
if (/^(0+|1+)$/.test(YMETRIKA_ID) || YMETRIKA_ID === '12345678') {
  console.warn(`WARN: analytics.yandexMetrikaId = "${YMETRIKA_ID}" похож на заглушку. Цели reachGoal уйдут в этот счётчик. Укажите номер из .env (METRIKA_COUNTER_ID).`);
}
let script = readTemplate('script.template.js');
script = script
  .split('{{PHONE_DISPLAY}}').join(config.contact.phoneDisplay)
  .split('{{EMAIL}}').join(config.contact.email)
  .split('{{SITE_DOMAIN}}').join(config.site.domain)
  .split('{{YMETRIKA_ID}}').join(YMETRIKA_ID);
fs.writeFileSync(path.join(outDir, 'script.js'), script);

// ---------- 4. catalog.js (генерация, не текстовый темплейтинг) ----------
// Переключатель цен. По умолчанию цены ВЫКЛЮЧЕНЫ: showPrices должно быть
// явно true, иначе цена не попадает ни в витрину, ни в карточку квиза.
// Причина: цена в config.catalog может быть устаревшей или демонстрационной,
// а на странице она выглядит как оферта. Механика и проверки — reference/.
const SHOW_PRICES = config.catalog?.showPrices === true;
if (!SHOW_PRICES && JSON.stringify(config.catalog?.groups || []).includes('"priceFrom"')) {
  console.log('Цены: выключены (catalog.showPrices != true). Поле priceFrom вырезано из catalog.js.');
}

function stripPrices(groups) {
  return (groups || []).map((g) => ({
    ...g,
    items: (g.items || []).map((it) => {
      const { priceFrom, ...rest } = it;
      return rest;
    })
  }));
}

function buildCatalogGroups() {
  const groups = config.catalog?.groups || [];
  return SHOW_PRICES ? groups : stripPrices(groups);
}

if (!config.catalog || !config.catalog.groups || !config.catalog.groups.length) {
  console.warn('WARN: config.catalog пуст — квиз-секция на странице будет нерабочей (пустые списки). '
    + 'Для бизнеса без переменного каталога см. SKILL.md раздел "Границы применимости" — замените блок 6 на прайс-блок вручную.');
}
const catalogJs = `/* Автосгенерировано render.js из config.catalog — правьте config.json и перезапустите рендер, а не этот файл. */
const CATALOG_GROUPS = ${JSON.stringify(buildCatalogGroups(), null, 2)};
const QUIZ_COMMON_FIELDS = ${JSON.stringify(config.catalog?.quizCommonFields || { layoutOptions: [], deadlineOptions: [] }, null, 2)};

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { CATALOG_GROUPS, QUIZ_COMMON_FIELDS };
} else {
  window.Catalog = { CATALOG_GROUPS, QUIZ_COMMON_FIELDS };
}
`;
fs.writeFileSync(path.join(outDir, 'catalog.js'), catalogJs);

// ---------- 5. backend ----------
// Идентификатор лендинга подставляется в бэкенд, иначе все лиды с разных
// лендингов неразличимы: у каждого одинаковые TITLE и SOURCE_DESCRIPTION.
fs.mkdirSync(path.join(outDir, 'backend'), { recursive: true });
let server = readTemplate('backend', 'server.template.js');
server = server
  .split('{{DEFAULT_MAIL_TO}}').join(config.backend?.mailTo || config.contact.email)
  .split('{{BUSINESS_NAME}}').join(config.business.name)
  .split('{{LANDING_TITLE}}').join(config.landing?.title || 'лендинг');
fs.writeFileSync(path.join(outDir, 'backend', 'server.js'), server);
fs.copyFileSync(path.join(__dirname, 'templates', 'backend', 'package.json'), path.join(outDir, 'backend', 'package.json'));

console.log(`OK: собрано в ${outDir}/ (index.html, styles.css, script.js, catalog.js, backend/server.js, backend/package.json)`);
console.log(assetsCopied ? `Ассеты скопированы: ${assetsCopied}.` : 'Ассеты уже на месте.');
if (missing.length === 0) {
  console.log('Не забыть: node --check + curl-тесты backend перед сдачей (см. reference/fact-checking-checklist.md)');
}
