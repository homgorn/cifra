#!/usr/bin/env node
/**
 * render-wp.js — альтернативный рендер того же config.json в разметку
 * Gutenberg-блоков для импорта в WordPress (Astra + Spectra) через WP All Import.
 *
 * ПОЧЕМУ ТАК (решение по умолчанию, см. обсуждение в чате):
 *   Квиз — это приложение с состоянием (4 шага, условная логика), а не
 *   табличные данные. У Spectra нет публичной спецификации блоков, под которую
 *   можно безопасно генерировать wp:uagb/* комментарии не угадывая — фабриковать
 *   их означало бы код, который either не импортируется, либо импортируется и
 *   не работает. Поэтому:
 *     - Статичные секции (1,2,3,4,5,7,8,9) → ЯДРОВЫЕ блоки WP (core/*) —
 *       это стабильный, документированный формат, Astra и Spectra его не ломают,
 *       и редактируется потом в WP как обычно.
 *     - Квиз (блок 6) → один core/html блок с самодостаточным HTML/CSS/JS
 *       внутри (тот же движок, что в templates/script.template.js) — НЕ
 *       редактируется визуально в WP, но гарантированно работает после импорта.
 *   Если нужна полная редактируемость квиза средствами Spectra — это отдельная
 *   задача, требующая либо документации по их блокам, либо ручного тестового
 *   импорта на вашей стороне, чтобы понять фактический формат.
 *
 * core/image с голым <img src="..."> (без id медиатеки) — осознанно: это именно
 * то, что умеет подхватывать WP All Import (сканирует wp:image на img src и
 * перекачивает картинку в медиатеку при импорте) — подтверждено документацией
 * плагина, не предположение из воздуха.
 *
 * Использование:
 *   node render-wp.js config.json dist-wp/
 * Результат: dist-wp/content.html — вставить как содержимое страницы/поста
 * при импорте (WP All Import позволяет маппить XML/CSV-поле на post_content).
 */

const fs = require('fs');
const path = require('path');

function fail(msg) { console.error('ERROR:', msg); process.exit(1); }

const configPath = process.argv[2];
if (!configPath) fail('Usage: node render-wp.js <config.json> [outDir=dist-wp]');
const outDir = process.argv[3] || 'dist-wp';

let config;
try {
  config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
} catch (e) {
  fail(`не удалось прочитать/распарсить ${configPath}: ${e.message}`);
}

function esc(str) {
  return String(str ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
function escAttr(str) {
  return esc(str).replace(/"/g, '&quot;');
}

// ---------- базовые core-блоки ----------
function heading(text, level) {
  const tag = `h${level}`;
  return `<!-- wp:heading {"level":${level}} -->\n<${tag} class="wp-block-heading">${esc(text)}</${tag}>\n<!-- /wp:heading -->`;
}
function paragraph(text) {
  return `<!-- wp:paragraph -->\n<p>${esc(text)}</p>\n<!-- /wp:paragraph -->`;
}
function image(src, alt) {
  return `<!-- wp:image {"sizeSlug":"large"} -->\n<figure class="wp-block-image size-large"><img src="${escAttr(src)}" alt="${escAttr(alt || '')}"/></figure>\n<!-- /wp:image -->`;
}
function buttons(items) {
  // items: [{text, url}]
  const inner = items.map((b) =>
    `  <!-- wp:button -->\n  <div class="wp-block-button"><a class="wp-block-button__link wp-element-button" href="${escAttr(b.url)}">${esc(b.text)}</a></div>\n  <!-- /wp:button -->`
  ).join('\n');
  return `<!-- wp:buttons -->\n<div class="wp-block-buttons">\n${inner}\n</div>\n<!-- /wp:buttons -->`;
}
function columns(columnBlocksArray) {
  // columnBlocksArray: array of arrays-of-block-strings, one per column
  const cols = columnBlocksArray.map((blocks) =>
    `  <!-- wp:column -->\n  <div class="wp-block-column">\n${blocks.map((b) => '  ' + b).join('\n\n')}\n  </div>\n  <!-- /wp:column -->`
  ).join('\n');
  return `<!-- wp:columns -->\n<div class="wp-block-columns">\n${cols}\n</div>\n<!-- /wp:columns -->`;
}
function group(innerBlocks, { bg } = {}) {
  const styleAttr = bg ? ` style="background-color:${escAttr(bg)}"` : '';
  const jsonAttr = bg ? `{"style":{"color":{"background":"${bg}"}},"layout":{"type":"constrained"}}` : '{"layout":{"type":"constrained"}}';
  return `<!-- wp:group ${jsonAttr} -->\n<div class="wp-block-group"${styleAttr}>\n${innerBlocks.join('\n\n')}\n</div>\n<!-- /wp:group -->`;
}
function rawHtml(html) {
  return `<!-- wp:html -->\n${html}\n<!-- /wp:html -->`;
}

// ---------- секции из config, те же данные что в render.js ----------
const blocks = [];

// 1. Hero
blocks.push(group([
  heading(config.business.name, 1),
  paragraph(config.hero?.lead || ''),
  buttons([
    { text: 'Пройти квиз и получить расчёт', url: '#quiz' },
    { text: 'Смотреть каталог', url: '#catalog' }
  ]),
  config.hero?.photo ? image(config.hero.photo, config.hero.photoAlt) : ''
].filter(Boolean)));

// 2. USP — колонки
if (config.usp?.length) {
  blocks.push(group(
    [columns(config.usp.map((u) => [heading(u.title, 3), paragraph(u.text)]))],
    { bg: '#000000' }
  ));
}

// 3. Методы — просто абзац-перечисление (нет core-блока "чипов")
if (config.methods?.length) {
  blocks.push(heading('Как мы работаем', 2));
  blocks.push(paragraph(config.methods.join(' · ')));
}

// 4. Каталог — по группам, товары колонками (картинка+название+специфика+метод/цена)
if (config.catalog?.groups?.length) {
  blocks.push(heading('Каталог', 2));
  config.catalog.groups.forEach((g) => {
    blocks.push(heading(g.title, 3));
    if (g.intro) blocks.push(paragraph(g.intro));
    const itemCols = g.items.map((item) => {
      const priceLine = item.priceFrom ? ` · ${item.priceFrom}` : '';
      return [
        item.img ? image(item.img, item.name) : '',
        heading(item.name, 4),
        paragraph(`${item.specs} · ${item.method}${priceLine}`)
      ].filter(Boolean);
    });
    // Колонки WP разумно читаются до 3-4 в ряд — режем по 3
    for (let i = 0; i < itemCols.length; i += 3) {
      blocks.push(columns(itemCols.slice(i, i + 3)));
    }
  });
}

// 5. Процесс
if (config.process?.length) {
  blocks.push(heading('Как проходит заказ', 2));
  blocks.push(columns(config.process.map((s, i) => [heading(`${i + 1}. ${s.title}`, 3), paragraph(s.text)])));
}

// 6. КВИЗ — core/html, самодостаточный (см. обоснование в шапке файла)
function buildQuizHtmlBlock(cfg) {
  const scriptTpl = fs.readFileSync(path.join(__dirname, 'templates', 'script.template.js'), 'utf8')
    .split('{{PHONE_DISPLAY}}').join(cfg.contact.phoneDisplay)
    .split('{{EMAIL}}').join(cfg.contact.email)
    .split('{{SITE_DOMAIN}}').join(cfg.site.domain);
  const catalogJs = `window.Catalog = ${JSON.stringify({
    CATALOG_GROUPS: cfg.catalog?.groups || [],
    QUIZ_COMMON_FIELDS: cfg.catalog?.quizCommonFields || { layoutOptions: [], deadlineOptions: [] }
  })};`;
  const cssTpl = fs.readFileSync(path.join(__dirname, 'templates', 'styles.template.css'), 'utf8');

  // Вырезаем из index.template.html именно секцию #quiz — не дублируем разметку руками
  const indexTpl = fs.readFileSync(path.join(__dirname, 'templates', 'index.template.html'), 'utf8');
  const quizSectionMatch = indexTpl.match(/<section class="quiz-section" id="quiz">[\s\S]*?<\/section>/);
  if (!quizSectionMatch) fail('не нашёл <section id="quiz"> в index.template.html — шаблоны разошлись');
  const quizSectionHtml = quizSectionMatch[0];

  return `<div class="lb-quiz-embed">
<style>${cssTpl}</style>
${quizSectionHtml}
<script>${catalogJs}</script>
<script>
(function(){
  // Демо/прод-переключатель: LEAD_ENDPOINT и QUIZ_ENDPOINT в движке — относительные
  // пути /api/lead и /api/quiz-lead. На WP-хостинге задеплойте backend (см.
  // backend/server.js блюпринта) на своём поддомене/пути и поправьте константы
  // в начале script.template.js на абсолютный URL ДО вставки сюда, либо
  // настройте проксирование /api/* на уровне веб-сервера WP-хостинга.
})();
</script>
<script>${scriptTpl}</script>
</div>`;
}
blocks.push(rawHtml(buildQuizHtmlBlock(config)));

// 7. Доверие
if (config.trustBadges?.length) {
  blocks.push(heading('Почему заказывают у нас', 2));
  blocks.push(columns(config.trustBadges.map((b) => [heading(b.value, 3), paragraph(b.label)])));
}

// 8. FAQ — raw HTML (details/summary), т.к. в ядре WP нет блока FAQ
if (config.faq?.length) {
  blocks.push(heading('Частые вопросы', 2));
  const faqHtml = config.faq.map((f) =>
    `<details style="margin-bottom:12px;"><summary style="font-weight:700;cursor:pointer;">${esc(f.q)}</summary><p>${esc(f.a)}</p></details>`
  ).join('\n');
  blocks.push(rawHtml(faqHtml));
}

// 9. Контакты — адрес/телефон/почта + карта (raw html для iframe) + кнопка маршрута + реквизиты
{
  const lines = [
    config.contact.address,
    config.contact.phoneDisplay,
    config.contact.email
  ].filter(Boolean).join(' · ');
  blocks.push(heading('Контакты', 2));
  blocks.push(paragraph(lines));
  if (config.contact.mapEmbedUrl) {
    blocks.push(rawHtml(`<iframe src="${escAttr(config.contact.mapEmbedUrl)}" style="width:100%;height:320px;border:0;border-radius:16px;" loading="lazy" title="Карта"></iframe>`));
  }
  if (config.contact.mapLat && config.contact.mapLon) {
    blocks.push(buttons([{ text: 'Проложить маршрут', url: `https://yandex.ru/maps/?rtext=~${config.contact.mapLat},${config.contact.mapLon}&rtt=auto` }]));
  }
  if (config.business.legalEntity) {
    const { fullName, inn, ogrn } = config.business.legalEntity;
    blocks.push(paragraph([fullName, inn && `ИНН ${inn}`, ogrn && `ОГРН(ИП) ${ogrn}`].filter(Boolean).join(', ')));
  }
}

fs.mkdirSync(outDir, { recursive: true });
const contentHtml = blocks.join('\n\n');
fs.writeFileSync(path.join(outDir, 'content.html'), contentHtml);

console.log(`OK: собрано в ${outDir}/content.html (Gutenberg-блоки, ${blocks.length} верхнеуровневых блоков)`);
console.log('Перед импортом десятков лендингов — протестируйте ОДИН вручную (создать черновик страницы → вкладка Код редактора → вставить содержимое content.html → переключиться на визуальный редактор): так увидите, как именно Astra/Spectra отрисуют core-блоки на вашей установке, прежде чем гнать пакетный импорт.');
