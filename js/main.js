/* Cifra18 audit report interactions */
(function () {
  // Mobile menu
  var btn = document.getElementById('menuBtn');
  var nav = document.getElementById('mainNav');
  if (btn && nav) {
    btn.addEventListener('click', function () {
      nav.classList.toggle('open');
    });
  }

  // Dropdown (Еще) toggle for touch devices
  var dropBtns = document.querySelectorAll('.nav-drop-btn');
  dropBtns.forEach(function (b) {
    b.addEventListener('click', function (e) {
      var dd = b.closest('.nav-dropdown');
      var was = dd.classList.contains('open');
      document.querySelectorAll('.nav-dropdown.open').forEach(function (d) {
        d.classList.remove('open');
      });
      if (!was) dd.classList.add('open');
      e.stopPropagation();
    });
  });
  document.addEventListener('click', function () {
    document.querySelectorAll('.nav-dropdown.open').forEach(function (d) {
      d.classList.remove('open');
    });
  });

  // Active sidebar link by scroll
  var sections = document.querySelectorAll('[data-section]');
  var sideLinks = document.querySelectorAll('.sidebar-link');
  if (sections.length && sideLinks.length && 'IntersectionObserver' in window) {
    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          sideLinks.forEach(function (l) {
            l.classList.toggle('active', l.getAttribute('href') === '#' + e.target.id);
          });
        }
      });
    }, { rootMargin: '-20% 0px -70% 0px' });
    sections.forEach(function (s) { obs.observe(s); });
  }

  // Animated counters
  var counters = document.querySelectorAll('[data-count]');
  if (counters.length && 'IntersectionObserver' in window) {
    var cObs = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var el = entry.target;
        cObs.unobserve(el);
        var target = parseInt(el.getAttribute('data-count'), 10) || 0;
        var start = null;
        var dur = 900;
        function step(ts) {
          if (!start) start = ts;
          var p = Math.min((ts - start) / dur, 1);
          var eased = 1 - Math.pow(1 - p, 3);
          el.textContent = Math.round(target * eased);
          if (p < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
      });
    }, { threshold: 0.5 });
    counters.forEach(function (c) { cObs.observe(c); });
  }

  // Charts
  if (typeof Chart === 'undefined') return;
  Chart.defaults.font.family = "'IBM Plex Sans', system-ui, sans-serif";
  Chart.defaults.font.size = 12;
  Chart.defaults.color = '#8b9bb3';
  Chart.defaults.borderColor = 'rgba(42,58,79,0.6)';

  var accent = '#00d4aa';
  var accentDim = 'rgba(0,212,170,0.25)';
  var warn = '#f5c542';
  var danger = '#ff6b6b';
  var info = '#4da3ff';
  var muted = '#2a3a4f';

  function mk(id, cfg) {
    var el = document.getElementById(id);
    if (!el) return null;
    return new Chart(el.getContext('2d'), cfg);
  }

  // Index: health radar style bar
  mk('healthChart', {
    type: 'bar',
    data: {
      labels: ['Техника', 'Скорость', 'Контент', 'Локалка', 'GEO', 'Конверсия'],
      datasets: [{
        data: [35, 45, 55, 30, 15, 40],
        backgroundColor: [danger, warn, warn, danger, danger, warn],
        borderRadius: 6,
        borderSkipped: false
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: function (c) { return c.raw + ' из 100'; } } } },
      scales: { x: { min: 0, max: 100, grid: { color: 'rgba(42,58,79,0.4)' } }, y: { grid: { display: false } } }
    }
  });

  // Index: loss donut
  mk('lossChart', {
    type: 'doughnut',
    data: {
      labels: ['Индексация', 'Сниппеты', 'Скорость', 'Нет калькулятора'],
      datasets: [{ data: [30, 25, 20, 25], backgroundColor: [danger, warn, info, accent], borderWidth: 2, borderColor: '#0a0e14' }]
    },
    options: { responsive: true, maintainAspectRatio: false, cutout: '62%', plugins: { legend: { position: 'bottom', labels: { boxWidth: 12, padding: 14 } } } }
  });

  // Technical: issue severity
  mk('severityChart', {
    type: 'bar',
    data: {
      labels: ['Блокеры', 'Важные', 'Улучшения'],
      datasets: [{ data: [5, 12, 9], backgroundColor: [danger, warn, info], borderRadius: 8 }]
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, grid: { color: 'rgba(42,58,79,0.4)' } }, x: { grid: { display: false } } } }
  });

  // Technical: image weight
  mk('imageChart', {
    type: 'bar',
    data: {
      labels: ['GIF hero', 'Баннер 1', 'Баннер 2', 'Каталог 1', 'Каталог 2', 'Остальные 10'],
      datasets: [{ label: 'КБ', data: [3400, 680, 540, 420, 310, 180], backgroundColor: [danger, warn, warn, warn, info, muted], borderRadius: 6 }]
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { grid: { color: 'rgba(42,58,79,0.4)' } }, x: { grid: { display: false }, ticks: { maxRotation: 30 } } } }
  });

  // Content: services by category
  mk('servicesChart', {
    type: 'bar',
    data: {
      labels: ['Полиграфия', 'Мерч', 'Широкоформат', 'Стенды', 'Интерьер', 'Инженерка'],
      datasets: [{ data: [26, 26, 10, 15, 6, 5], backgroundColor: [accent, info, warn, '#9b8cff', '#ff9d6b', muted], borderRadius: 6 }]
    },
    options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { grid: { color: 'rgba(42,58,79,0.4)' } }, y: { grid: { display: false } } } }
  });

  // Content: text length
  mk('contentLenChart', {
    type: 'line',
    data: {
      labels: ['Визитки', 'Листовки', 'Баннеры', 'Кружки', 'Футболки', 'Роллапы', 'Чертежи', 'Холст'],
      datasets: [
        { label: 'Сейчас, знаков', data: [800, 600, 500, 700, 650, 400, 300, 450], borderColor: danger, backgroundColor: 'rgba(255,107,107,0.12)', fill: true, tension: 0.4 },
        { label: 'Нужно, знаков', data: [4500, 4000, 3800, 3500, 3500, 3000, 2800, 3200], borderColor: accent, backgroundColor: accentDim, fill: true, tension: 0.4 }
      ]
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } }, scales: { y: { grid: { color: 'rgba(42,58,79,0.4)' } }, x: { grid: { display: false } } } }
  });

  // Competitors: threat
  mk('threatChart', {
    type: 'bar',
    data: {
      labels: ['Printio', 'RuPrint', 'Контур-Фото', 'Printful', 'Vaston', 'SMART', 'Авито', 'Профи.ру'],
      datasets: [{ data: [95, 80, 75, 65, 50, 45, 40, 30], backgroundColor: [danger, danger, warn, warn, info, info, muted, muted], borderRadius: 6 }]
    },
    options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { callbacks: { label: function (c) { return 'Угроза: ' + c.raw + ' из 100'; } } } }, scales: { x: { min: 0, max: 100, grid: { color: 'rgba(42,58,79,0.4)' } }, y: { grid: { display: false } } } }
  });

  // Competitors: radar
  mk('compareRadar', {
    type: 'radar',
    data: {
      labels: ['Каталог', 'Онлайн оплата', 'Калькулятор', 'СДЭК по РФ', 'Отзывы', 'Скорость'],
      datasets: [
        { label: 'Цифра18', data: [80, 40, 20, 85, 55, 80], borderColor: accent, backgroundColor: accentDim, pointBackgroundColor: accent },
        { label: 'Контур-Фото', data: [50, 10, 5, 15, 95, 85], borderColor: warn, backgroundColor: 'rgba(245,197,66,0.15)', pointBackgroundColor: warn },
        { label: 'Printio', data: [95, 95, 90, 90, 80, 60], borderColor: info, backgroundColor: 'rgba(77,163,255,0.12)', pointBackgroundColor: info }
      ]
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } }, scales: { r: { min: 0, max: 100, grid: { color: 'rgba(42,58,79,0.6)' }, angleLines: { color: 'rgba(42,58,79,0.6)' }, pointLabels: { color: '#8b9bb3' }, ticks: { display: false } } } }
  });

  // Local: cities
  mk('citiesChart', {
    type: 'bar',
    data: {
      labels: ['Ижевск', 'Воткинск', 'Глазов', 'Сарапул', 'Можега', 'Москва', 'Казань', 'Пермь', 'Екб', 'СПб'],
      datasets: [
        { label: 'Население, тыс', data: [640, 90, 100, 100, 50, 13000, 1300, 1000, 1500, 5600], backgroundColor: accent, borderRadius: 6, yAxisID: 'y' },
        { label: 'Дней СДЭК', data: [0, 1, 1, 1, 1, 1, 3, 2, 2, 2], backgroundColor: warn, borderRadius: 6, yAxisID: 'y1' }
      ]
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } }, scales: { y: { type: 'logarithmic', grid: { color: 'rgba(42,58,79,0.4)' } }, y1: { position: 'right', min: 0, max: 5, grid: { display: false } }, x: { grid: { display: false }, ticks: { maxRotation: 35 } } } }
  });

  // GEO: visibility
  mk('geoChart', {
    type: 'line',
    data: {
      labels: ['Сейчас', '1 мес', '3 мес', '6 мес', '9 мес', '12 мес'],
      datasets: [
        { label: 'Упоминания в AI, %', data: [2, 8, 22, 45, 65, 80], borderColor: accent, backgroundColor: accentDim, fill: true, tension: 0.4 },
        { label: 'Конкуренты (среднее), %', data: [35, 36, 38, 40, 42, 44], borderColor: muted, borderDash: [6, 4], tension: 0.4 }
      ]
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } }, scales: { y: { min: 0, max: 100, grid: { color: 'rgba(42,58,79,0.4)' } }, x: { grid: { display: false } } } }
  });

  // Knowledge: entities
  mk('kgChart', {
    type: 'doughnut',
    data: {
      labels: ['Услуги', 'Материалы', 'Локации', 'Конкуренты', 'Отрасли', 'Оборудование', 'Остальное'],
      datasets: [{ data: [88, 18, 22, 17, 13, 11, 70], backgroundColor: [accent, info, warn, danger, '#9b8cff', '#ff9d6b', muted], borderWidth: 2, borderColor: '#0a0e14' }]
    },
    options: { responsive: true, maintainAspectRatio: false, cutout: '58%', plugins: { legend: { position: 'bottom', labels: { boxWidth: 12, padding: 12 } } } }
  });

  // Knowledge: triplets
  mk('tripletChart', {
    type: 'bar',
    data: {
      labels: ['hasService', 'hasPrintMethod', 'hasMaterial', 'competesWith', 'hasEquipment', 'hasSdekPVZ'],
      datasets: [{ data: [83, 77, 15, 17, 10, 20], backgroundColor: [accent, info, warn, danger, '#9b8cff', muted], borderRadius: 6 }]
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { grid: { color: 'rgba(42,58,79,0.4)' } }, x: { grid: { display: false }, ticks: { maxRotation: 25 } } } }
  });

  // Prices: competitor comparison (midpoints, RUB)
  mk('priceChart', {
    type: 'bar',
    data: {
      labels: ['Визитки 100 шт', 'Листовки А5 1000 шт', 'Баннер 3х6 м'],
      datasets: [
        { label: 'Цифра18', data: [350, 3000, 4250], backgroundColor: accent, borderRadius: 6 },
        { label: 'Контур-Фото', data: [425, 3750, 0], backgroundColor: warn, borderRadius: 6 },
        { label: 'RuPrint', data: [500, 4250, 5000], backgroundColor: info, borderRadius: 6 },
        { label: 'Printio', data: [1000, 0, 0], backgroundColor: muted, borderRadius: 6 }
      ]
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' }, tooltip: { callbacks: { label: function (c) { return c.dataset.label + ': ' + (c.raw ? c.raw + ' руб' : 'не делают'); } } } }, scales: { y: { grid: { color: 'rgba(42,58,79,0.4)' } }, x: { grid: { display: false } } } }
  });

  // Season: quarterly revenue share
  mk('seasonChart', {
    type: 'bar',
    data: {
      labels: ['Q1 (НГ, 8 Марта, 23 Фев)', 'Q2 (выпускные, свадьбы)', 'Q3 (1 Сентября, выставки)', 'Q4 (НГ, корп. подарки)'],
      datasets: [{ label: 'Доля годовой выручки, %', data: [25, 20, 25, 30], backgroundColor: [info, accent, warn, danger], borderRadius: 8 }]
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { min: 0, max: 35, grid: { color: 'rgba(42,58,79,0.4)' } }, x: { grid: { display: false }, ticks: { maxRotation: 20 } } } }
  });

  // Marketing: budget donut (thousands RUB, 6 months)
  mk('budgetChart', {
    type: 'doughnut',
    data: {
      labels: ['SEO и контент', 'СДЭК интеграция', 'Поддомен и контент', 'SMM', 'Директ', 'Email и CRM', 'PR', 'Инструменты', 'Резерв'],
      datasets: [{ data: [750, 220, 350, 240, 260, 70, 100, 60, 309], backgroundColor: [accent, info, warn, danger, '#9b8cff', '#ff9d6b', '#5ad1e6', muted, '#3a4a5f'], borderWidth: 2, borderColor: '#0a0e14' }]
    },
    options: { responsive: true, maintainAspectRatio: false, cutout: '58%', plugins: { legend: { position: 'bottom', labels: { boxWidth: 12, padding: 10 } }, tooltip: { callbacks: { label: function (c) { return c.label + ': ' + c.raw + 'К'; } } } } }
  });

  // Marketing: merch share forecast
  mk('merchKpiChart', {
    type: 'line',
    data: {
      labels: ['Сейчас', '3 мес', '6 мес', '12 мес'],
      datasets: [
        { label: 'Доля мерча, %', data: [7, 15, 20, 35], borderColor: accent, backgroundColor: accentDim, fill: true, tension: 0.4, yAxisID: 'y' },
        { label: 'Средний чек, руб', data: [1500, 2500, 3000, 4500], borderColor: warn, backgroundColor: 'rgba(245,197,66,0.1)', fill: false, tension: 0.4, yAxisID: 'y1' }
      ]
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } }, scales: { y: { min: 0, max: 40, grid: { color: 'rgba(42,58,79,0.4)' } }, y1: { position: 'right', min: 0, max: 5000, grid: { display: false } }, x: { grid: { display: false } } } }
  });

  // Roadmap: traffic forecast
  mk('forecastChart', {
    type: 'line',
    data: {
      labels: ['Старт', '1 мес', '2 мес', '3 мес', '6 мес', '9 мес', '12 мес'],
      datasets: [
        { label: 'Органика, визиты', data: [100, 115, 140, 180, 300, 420, 500], borderColor: accent, backgroundColor: accentDim, fill: true, tension: 0.4 },
        { label: 'Заявки', data: [100, 110, 130, 170, 300, 400, 500], borderColor: warn, backgroundColor: 'rgba(245,197,66,0.12)', fill: true, tension: 0.4 }
      ]
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' }, tooltip: { callbacks: { label: function (c) { return c.dataset.label + ': x' + (c.raw / 100).toFixed(2); } } } }, scales: { y: { grid: { color: 'rgba(42,58,79,0.4)' } }, x: { grid: { display: false } } } }
  });

  // Webmaster section (wm-* pages). All numbers come from js/wm-data.js.
  var W = (typeof WM !== 'undefined') ? WM : null;
  function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
  var palette = [accent, info, warn, danger, '#9b8cff', '#ff9d6b'];
  if (W) {
    // wm-overview: statuses donut
    (function () {
      var order = ['SEARCHABLE', 'DUPLICATE', 'PARSE_ERROR', 'REDIRECT_NOTSEARCHABLE', 'OTHER', 'BAD_QUALITY', 'HTTP_ERROR'];
      var names = { SEARCHABLE: 'В поиске', DUPLICATE: 'Дубли', PARSE_ERROR: 'Ошибки парсинга', REDIRECT_NOTSEARCHABLE: 'Редиректы', OTHER: 'Нет данных', BAD_QUALITY: 'Низкое качество', HTTP_ERROR: 'Ошибки сервера' };
      var colors = { SEARCHABLE: accent, DUPLICATE: warn, PARSE_ERROR: danger, REDIRECT_NOTSEARCHABLE: info, OTHER: muted, BAD_QUALITY: '#9b8cff', HTTP_ERROR: '#ff9d6b' };
      mk('wmStatusDonut', {
        type: 'doughnut',
        data: { labels: order.map(function (k) { return names[k]; }), datasets: [{ data: order.map(function (k) { return W.statuses[k] || 0; }), backgroundColor: order.map(function (k) { return colors[k]; }), borderWidth: 2, borderColor: '#0a0e14' }] },
        options: { responsive: true, maintainAspectRatio: false, cutout: '58%', plugins: { legend: { position: 'bottom', labels: { boxWidth: 12, padding: 12 } } } }
      });
    })();

    // wm-overview: TOP share bars
    mk('wmTopShareBar', {
      type: 'bar',
      data: {
        labels: ['ТОП-1', 'ТОП-3', 'ТОП-10', 'ТОП-20'],
        datasets: [{ data: [W.queryTops.top1, W.queryTops.top3, W.queryTops.top10, W.meta.totalQueries - W.queryBins['20+']], backgroundColor: [accent, info, warn, muted], borderRadius: 8 }]
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, grid: { color: 'rgba(42,58,79,0.4)' } }, x: { grid: { display: false } } } }
    });

    // wm-indexing: sections known vs searchable
    (function () {
      var short = { '/catalog': 'Каталог', '/shop': '/shop/', '/poligrafiya': 'Полиграфия', '/suvenirnaya-produktsiya': 'Сувенирка', '/news': 'Новости', '/pechat-na-kruzhkakh': 'Кружки', '/pechat-na-ruchkakh': 'Ручки', '/kalendari': 'Календари' };
      var labels = W.sectionsTop.map(function (s) { return short[s.section] || s.section; });
      mk('wmSectionBar', {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [
            { label: 'Известно роботу', data: W.sectionsTop.map(function (s) { return s.indexed; }), backgroundColor: info, borderRadius: 6 },
            { label: 'В поиске', data: W.sectionsTop.map(function (s) { return s.searchable; }), backgroundColor: accent, borderRadius: 6 }
          ]
        },
        options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } }, scales: { x: { grid: { color: 'rgba(42,58,79,0.4)' } }, y: { grid: { display: false } } } }
      });
      mk('wmRateBar', {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [{ data: W.sectionsTop.map(function (s) { return s.rate; }), backgroundColor: danger, borderRadius: 6 }]
        },
        options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { callbacks: { label: function (c) { return c.raw + '% в поиске (норма от 60%)'; } } } }, scales: { x: { min: 0, max: 10, grid: { color: 'rgba(42,58,79,0.4)' } }, y: { grid: { display: false } } } }
      });
    })();

    // wm-duplicates: patterns
    mk('wmDupPatternsBar', {
      type: 'bar',
      data: {
        labels: ['Числовые .html', 'detail.php', '/shop/', 'Прочие'],
        datasets: [{ data: [W.dupPatterns.numericHtml, W.dupPatterns.detailPhp, W.dupPatterns.shop, W.dupPatterns.other], backgroundColor: [danger, warn, warn, muted], borderRadius: 8 }]
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, grid: { color: 'rgba(42,58,79,0.4)' } }, x: { grid: { display: false } } } }
    });

    // wm-errors: parse patterns + exclusions
    mk('wmParsePatternsBar', {
      type: 'bar',
      data: {
        labels: ['/shop/', 'Числовые .html', 'detail.php'],
        datasets: [{ data: [W.parsePatterns.shop, W.parsePatterns.numericHtml, W.parsePatterns.detailPhp], backgroundColor: [danger, warn, info], borderRadius: 8 }]
      },
      options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { grid: { color: 'rgba(42,58,79,0.4)' } }, y: { grid: { display: false } } } }
    });
    mk('wmErrorBar', {
      type: 'bar',
      data: {
        labels: ['PARSE_ERROR', 'OTHER', 'BAD_QUALITY', 'HTTP_ERROR'],
        datasets: [{ data: [W.statuses.PARSE_ERROR, W.statuses.OTHER, W.statuses.BAD_QUALITY, W.statuses.HTTP_ERROR], backgroundColor: [danger, muted, warn, info], borderRadius: 8 }]
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, grid: { color: 'rgba(42,58,79,0.4)' } }, x: { grid: { display: false } } } }
    });

    // wm-redirects: structure donut
    mk('wmRedirectDonut', {
      type: 'doughnut',
      data: {
        labels: ['В поиске', 'Редиректы', 'Остальные исключения'],
        datasets: [{ data: [W.statuses.SEARCHABLE, W.statuses.REDIRECT_NOTSEARCHABLE, W.meta.totalPages - W.statuses.SEARCHABLE - W.statuses.REDIRECT_NOTSEARCHABLE], backgroundColor: [accent, info, muted], borderWidth: 2, borderColor: '#0a0e14' }]
      },
      options: { responsive: true, maintainAspectRatio: false, cutout: '62%', plugins: { legend: { position: 'bottom', labels: { boxWidth: 12, padding: 14 } } } }
    });

    // wm-queries: position histogram
    mk('wmPosHist', {
      type: 'bar',
      data: {
        labels: ['1', '1-3', '3-5', '5-10', '10-20', '20+'],
        datasets: [{ data: [W.queryBins['1'], W.queryBins['1-3'], W.queryBins['3-5'], W.queryBins['5-10'], W.queryBins['10-20'], W.queryBins['20+']], backgroundColor: [accent, accent, info, warn, warn, danger], borderRadius: 8 }]
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { callbacks: { label: function (c) { return c.raw + ' запросов'; } } } }, scales: { y: { grid: { color: 'rgba(42,58,79,0.4)' } }, x: { grid: { display: false } } } }
    });

    // wm-queries: money queries position trend
    mk('wmMoneyTrend', {
      type: 'line',
      data: {
        labels: W.trendDays,
        datasets: W.trend.map(function (t, i) {
          return { label: t.q, data: t.series, borderColor: palette[i % palette.length], backgroundColor: 'transparent', fill: false, tension: 0.3, spanGaps: true };
        })
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { boxWidth: 12, padding: 10 } } }, scales: { y: { reverse: true, min: 1, grid: { color: 'rgba(42,58,79,0.4)' } }, x: { grid: { display: false } } } }
    });

    // wm-queries: total shows per day
    mk('wmShowsBar', {
      type: 'bar',
      data: {
        labels: W.trendDays,
        datasets: [{ label: 'Показы', data: W.showsDaily, backgroundColor: accent, borderRadius: 6 }]
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { grid: { color: 'rgba(42,58,79,0.4)' } }, x: { grid: { display: false } } } }
    });

    // wm-queries: money table
    (function () {
      var tb = document.getElementById('wmMoneyBody');
      if (!tb) return;
      tb.innerHTML = W.money.map(function (m) {
        return '<tr><td><strong>' + esc(m.q) + '</strong></td><td>' + m.avg + '</td><td>' + m.shows + '</td><td>' + m.clicks + '</td><td>' + m.ctr + '%</td></tr>';
      }).join('');
    })();

    // wm-clusters: queries per cluster + pages of that section in search
    mk('wmClusterBar', {
      type: 'bar',
      data: {
        labels: W.clusters.map(function (c) { return c.name; }),
        datasets: [{ data: W.clusters.map(function (c) { return c.queries; }), backgroundColor: [accent, info, warn, '#9b8cff', '#ff9d6b', danger, muted, '#5ad1e6'], borderRadius: 6 }]
      },
      options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { callbacks: { label: function (c) { return c.raw + ' запросов'; } } } }, scales: { x: { grid: { color: 'rgba(42,58,79,0.4)' } }, y: { grid: { display: false } } } }
    });
    // Второй график показывает реальные страницы раздела в поиске, а не
    // вычисленное покрытие. Прежняя доля «% запросов с целевой страницей»
    // всегда была 100%: цель назначалась по кластеру автоматически, и
    // метрика измеряла работу классификатора, а не состояние сайта.
    mk('wmCoverageBar', {
      type: 'bar',
      data: {
        labels: W.clusters.map(function (c) { return c.name; }),
        datasets: [{ data: W.clusters.map(function (c) { return c.pages; }), backgroundColor: W.clusters.map(function (c) { return c.pages === 0 ? danger : (c.pages < c.queries / 8 ? warn : accent); }), borderRadius: 6 }]
      },
      options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { callbacks: { label: function (c) { return c.raw === 0 ? 'страниц в поиске нет' : c.raw + ' страниц в поиске'; } } } }, scales: { x: { beginAtZero: true, grid: { color: 'rgba(42,58,79,0.4)' }, ticks: { precision: 0 } }, y: { grid: { display: false } } } }
    });

    // wm-clusters: table
    (function () {
      var tb = document.getElementById('wmClusterBody');
      if (!tb) return;
      tb.innerHTML = W.clusters.map(function (c) {
        var status, badge;
        if (!c.target) { status = 'нужна страница'; badge = 'badge-danger'; }
        else if (c.pages === 0) { status = 'в поиске нет'; badge = 'badge-danger'; }
        else if (c.pages < c.queries / 8) { status = 'тонко'; badge = 'badge-warning'; }
        else { status = 'нормально'; badge = 'badge-success'; }
        return '<tr><td><strong>' + esc(c.name) + '</strong></td><td>' + c.queries + '</td><td>' + c.avg + '</td><td>' + c.top10 + '%</td><td>' + c.pages + '</td><td><span class="badge ' + badge + '">' + status + '</span></td></tr>';
      }).join('');
    })();

    // wm-gaps: positions of gaps + priority donut + table
    (function () {
      var withPos = W.gaps.filter(function (g) { return g.pos > 0; });
      mk('wmGapPosBar', {
        type: 'bar',
        data: {
          labels: withPos.map(function (g) { return g.query; }),
          datasets: [{ data: withPos.map(function (g) { return g.pos; }), backgroundColor: withPos.map(function (g) { return g.impact === 'High' && g.effort === 'Low' ? accent : warn; }), borderRadius: 6 }]
        },
        options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { callbacks: { label: function (c) { return 'позиция ' + c.raw; } } } }, scales: { x: { grid: { color: 'rgba(42,58,79,0.4)' } }, y: { grid: { display: false } } } }
      });
      var crit = W.gaps.filter(function (g) { return g.impact === 'High'; }).length;
      mk('wmGapPriorityDonut', {
        type: 'doughnut',
        data: { labels: ['Высокий эффект', 'Средний эффект'], datasets: [{ data: [crit, W.gaps.length - crit], backgroundColor: [danger, warn], borderWidth: 2, borderColor: '#0a0e14' }] },
        options: { responsive: true, maintainAspectRatio: false, cutout: '62%', plugins: { legend: { position: 'bottom', labels: { boxWidth: 12, padding: 14 } } } }
      });
      var tb = document.getElementById('wmGapsBody');
      if (tb) {
        tb.innerHTML = W.gaps.map(function (g, i) {
          var pos = g.pos > 0 ? g.pos : '<span class="badge badge-info">новая</span>';
          return '<tr><td><code>' + (i + 1) + '</code></td><td><strong>' + esc(g.query) + '</strong></td><td>' + pos + '</td><td>' + esc(g.kind) + '</td><td><code>' + esc(g.url) + '</code></td></tr>';
        }).join('');
      }
    })();

    // wm-links: status donut + broken targets
    mk('wmLinkStatusDonut', {
      type: 'doughnut',
      data: {
        labels: ['301', '404', '502', '500'],
        datasets: [{ data: [W.linkStatus['301'] || 0, W.linkStatus['404'] || 0, W.linkStatus['502'] || 0, W.linkStatus['500'] || 0], backgroundColor: [info, danger, warn, muted], borderWidth: 2, borderColor: '#0a0e14' }]
      },
      options: { responsive: true, maintainAspectRatio: false, cutout: '62%', plugins: { legend: { position: 'bottom', labels: { boxWidth: 12, padding: 14 } } } }
    });
    (function () {
      var labels = W.brokenTargets.map(function (t) {
        var u = t.url.replace(/\/$/, '');
        if (u === '') return 'Главная';
        var parts = u.split('/');
        return parts[parts.length - 1].slice(0, 30);
      });
      mk('wmBrokenTargetsBar', {
        type: 'bar',
        data: { labels: labels, datasets: [{ data: W.brokenTargets.map(function (t) { return t.count; }), backgroundColor: danger, borderRadius: 6 }] },
        options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { callbacks: { label: function (c) { return c.raw + ' битых ссылок'; } } } }, scales: { x: { grid: { color: 'rgba(42,58,79,0.4)' } }, y: { grid: { display: false } } } }
      });
      var tb = document.getElementById('wmBrokenTargetsBody');
      if (tb) {
        tb.innerHTML = W.brokenTargets.map(function (t) {
          var full = 'https://xn--18-6kc5a3bxam.xn--p1ai' + t.url;
          return '<tr><td><a href="' + full + '">' + esc(t.url) + '</a></td><td><span class="badge badge-danger">' + t.count + '</span></td></tr>';
        }).join('');
      }
    })();

    // wm-plan: ICE bars + table + forecast
    (function () {
      var short = ['Карта сайта', 'Canonical', 'Закрыть /shop/', 'Тире', 'Подкатегории', 'JSON-LD', 'Локальные', 'Title и meta', 'Метрика', 'IndexNow'];
      var refs = [['wm-indexing.html', 'Индексация'], ['wm-duplicates.html', 'Дубли'], ['wm-errors.html', 'Ошибки'], ['technical.html', 'Техника'], ['wm-gaps.html', 'Пробелы'], ['technical.html', 'Техника'], ['wm-gaps.html', 'Пробелы'], ['wm-overview.html', 'Сводка'], ['wm-queries.html', 'Запросы'], ['wm-indexing.html', 'Индексация']];
      mk('wmIceBar', {
        type: 'bar',
        data: { labels: short, datasets: [{ data: W.ice.map(function (a) { return a.score; }), backgroundColor: W.ice.map(function (a) { return a.score >= 8 ? accent : (a.score >= 7 ? warn : info); }), borderRadius: 6 }] },
        options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { callbacks: { label: function (c) { return 'ICE ' + c.raw; } } } }, scales: { x: { min: 6, max: 10, grid: { color: 'rgba(42,58,79,0.4)' } }, y: { grid: { display: false } } } }
      });
      var tb = document.getElementById('wmIceBody');
      if (tb) {
        tb.innerHTML = W.ice.map(function (a, i) {
          return '<tr><td><code>' + (i + 1) + '</code></td><td><strong>' + esc(a.action) + '</strong></td><td>' + a.score + '</td><td><a href="' + refs[i][0] + '">' + refs[i][1] + '</a></td></tr>';
        }).join('');
      }
    })();
    mk('wmForecastLine', {
      type: 'line',
      data: {
        labels: W.forecast.labels,
        datasets: [{ label: 'Страниц в поиске', data: W.forecast.searchable, borderColor: accent, backgroundColor: accentDim, fill: true, tension: 0.4 }]
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } }, scales: { y: { grid: { color: 'rgba(42,58,79,0.4)' } }, x: { grid: { display: false } } } }
    });
  }

  // Homepage live data (index.html). All numbers come from js/site-data.js.
  var S = (typeof SITE !== 'undefined') ? SITE : null;
  function setText(id, txt) {
    var el = document.getElementById(id);
    if (el) el.textContent = txt;
  }
  function fmtNum(n) {
    return String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
  }
  if (S) {
    setText('siteGenerated', 'API • ' + S.generated);
    setText('kpiSearchable', fmtNum(S.searchable));
    if (S.insearchFirst && S.insearchLast) {
      var d = S.insearchLast.v - S.insearchFirst.v;
      setText('kpiSearchableDelta', '+' + d + ' за год • API Вебмастера');
    }
    setText('kpiSqi', fmtNum(S.sqi));
    setText('kpiRevenue', fmtNum(S.revenue) + ' ₽');
    setText('kpiOrders', fmtNum(S.purchases) + ' покупок из dataLayer');
    setText('kpiTop10', fmtNum(W && W.queryTops ? W.queryTops.top10 : 390));
    setText('popularWeek', 'API Вебмастера, ' + S.popularWeek + ' • топ-10 из ' + S.popularCount);
    (function () {
      var ol = document.getElementById('homePopular');
      if (ol) {
        ol.innerHTML = S.popularTop10.map(function (q) {
          return '<li>' + esc(q) + '</li>';
        }).join('');
      }
    })();

    mk('homeSearchLine', {
      type: 'line',
      data: {
        labels: S.insearchMonthly.map(function (p) { return p.m.slice(2); }),
        datasets: [{ label: 'Страниц в поиске', data: S.insearchMonthly.map(function (p) { return p.v; }), borderColor: accent, backgroundColor: accentDim, fill: true, tension: 0.4 }]
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { grid: { color: 'rgba(42,58,79,0.4)' } }, x: { grid: { display: false } } } }
    });

    (function () {
      var order = ['SEARCHABLE', 'DUPLICATE', 'PARSE_ERROR', 'REDIRECT_NOTSEARCHABLE', 'OTHER', 'BAD_QUALITY', 'HTTP_ERROR'];
      var names = { SEARCHABLE: 'В поиске', DUPLICATE: 'Дубли', PARSE_ERROR: 'Ошибки парсинга', REDIRECT_NOTSEARCHABLE: 'Редиректы', OTHER: 'Нет данных', BAD_QUALITY: 'Низкое качество', HTTP_ERROR: 'Ошибки сервера' };
      var colors = { SEARCHABLE: accent, DUPLICATE: warn, PARSE_ERROR: danger, REDIRECT_NOTSEARCHABLE: info, OTHER: muted, BAD_QUALITY: '#9b8cff', HTTP_ERROR: '#ff9d6b' };
      mk('homeStatusDonut', {
        type: 'doughnut',
        data: { labels: order.map(function (k) { return names[k]; }), datasets: [{ data: order.map(function (k) { return S.statuses[k] || 0; }), backgroundColor: order.map(function (k) { return colors[k]; }), borderWidth: 2, borderColor: '#0a0e14' }] },
        options: { responsive: true, maintainAspectRatio: false, cutout: '58%', plugins: { legend: { position: 'bottom', labels: { boxWidth: 12, padding: 12 } } } }
      });
    })();

    mk('homeMoneyBar', {
      type: 'bar',
      data: {
        labels: S.revenueTop5.map(function (r) { return r.d.slice(5); }),
        datasets: [{ data: S.revenueTop5.map(function (r) { return r.v; }), backgroundColor: [accent, info, warn, danger, muted], borderRadius: 6 }]
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { callbacks: { label: function (c) { return c.raw + ' ₽'; } } } }, scales: { y: { grid: { color: 'rgba(42,58,79,0.4)' } }, x: { grid: { display: false } } } }
    });

    mk('homeSourcesDonut', {
      type: 'doughnut',
      data: {
        labels: S.sourcesYear.map(function (s) { return s.s; }),
        datasets: [{ data: S.sourcesYear.map(function (s) { return s.v; }), backgroundColor: [accent, info, warn, danger, '#9b8cff', '#ff9d6b', muted, '#5ad1e6'], borderWidth: 2, borderColor: '#0a0e14' }]
      },
      options: { responsive: true, maintainAspectRatio: false, cutout: '62%', plugins: { legend: { position: 'bottom', labels: { boxWidth: 12, padding: 14 } } } }
    });
  }

  // Dashboards: data from js/dash-data.js, built by scripts/export/build_dashboard_data.py
  var D = (typeof DASH !== 'undefined') ? DASH : null;
  if (D) {
    var T = D.tech, S = D.site, M = D.money, MP = D.maps;
    var dLabels = function (arr) { return arr.map(function (x) { return x.m.slice(2); }); };
    var dValues = function (arr, k) { return arr.map(function (x) { return k ? x[k] : x.v; }); };
    var kvBars = function (arr, top, colorList) {
      var sl = arr.slice(0, top);
      var colors = colorList || [accent, info, warn, danger, '#9b8cff', '#ff9d6b', muted, '#5ad1e6'];
      return {
        labels: sl.map(function (x) { return x.k; }),
        data: sl.map(function (x) { return x.v; }),
        colors: sl.map(function (x, i) { return colors[i % colors.length]; })
      };
    };

    (function () {
      var qb = document.getElementById('wmClusterQueriesBody');
      if (qb && W.queryClusters) {
        var order = {};
        W.clusters.forEach(function (c, i) { order[c.name] = i; });
        var rows = W.queryClusters.slice().sort(function (a, b) {
          var ka = order[a.c] === undefined ? 99 : order[a.c];
          var kb = order[b.c] === undefined ? 99 : order[b.c];
          if (ka !== kb) return ka - kb;
          return (a.p || 99) - (b.p || 99);
        });
        qb.innerHTML = rows.slice(0, 120).map(function (r) {
          return '<tr><td>' + esc(r.q) + '</td><td>' + esc(r.c) + '</td><td>' + r.p +
            '</td><td>' + (r.u ? '<code>' + esc(r.u) + '</code>' : '<span class="text-muted">нужна страница</span>') + '</td></tr>';
        }).join('');
      }
    })();

    // --- Видимость
    setText('kpiSqi', fmtNum(T.sqi));
    // План на 3 месяца: мёртвые разделы против рабочего каталога
    setText('kpiDead', fmtNum(T.dead || 0));
    (function () {
      var rows = T.indexing || [];
      var cat = null;
      rows.forEach(function (r) { if (r.k === 'Каталог') cat = r; });
      setText('kpiCatalog', cat ? cat.p + '%' : '-');
      var err = 0;
      rows.forEach(function (r) { err += r.e || 0; });
      setText('kpiErrors', fmtNum(err));
      setText('kpiQuota', fmtNum(T.recrawlDaily));
    })();
    if (T.sqiFirst) {
      setText('kpiSqiGrowth', '+' + (T.sqi - T.sqiFirst.v) + ' с ' + T.sqiFirst.m.slice(0, 4));
    }
    setText('kpiSearchable', fmtNum(T.searchable));
    setText('kpiRecrawl', fmtNum(T.recrawlDaily));
    mk('dashSqiLine', {
      type: 'line',
      data: {
        labels: T.sqiSeries.map(function (x) { return x.m; }),
        datasets: [{ label: 'SQI', data: dValues(T.sqiSeries), borderColor: accent, backgroundColor: accentDim, fill: true, tension: 0.3, pointRadius: 0 }]
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { min: 0, max: 300, grid: { color: 'rgba(42,58,79,0.4)' } }, x: { grid: { display: false }, ticks: { maxTicksLimit: 10 } } } }
    });
    (function () {
      var sl = T.sections.slice().sort(function (a, b) { return b.i - a.i; });
      mk('dashSectionBar', {
        type: 'bar',
        data: {
          labels: sl.map(function (x) { return x.p; }),
          datasets: [
            { label: 'Проиндексировано', data: sl.map(function (x) { return x.i; }), backgroundColor: info, borderRadius: 4 },
            { label: 'В поиске', data: sl.map(function (x) { return x.s; }), backgroundColor: accent, borderRadius: 4 }
          ]
        },
        options: { responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: { legend: { position: 'bottom' } }, scales: { x: { grid: { color: 'rgba(42,58,79,0.4)' } }, y: { grid: { display: false }, ticks: { autoSkip: false } } } }
      });
      var tb = document.getElementById('dashSectionBody');
      if (tb) {
        tb.innerHTML = sl.map(function (x) {
          var pct = x.i ? Math.round(x.s / x.i * 100) : 0;
          return '<tr><td><code>' + esc(x.p) + '</code></td><td>' + fmtNum(x.i) + '</td><td>' + fmtNum(x.s) +
            '</td><td>' + pct + '%</td></tr>';
        }).join('');
      }
    })();
    (function () {
      var codes = {};
      T.http.forEach(function (h) { codes[h.code] = (codes[h.code] || 0) + 1; });
      var ks = Object.keys(codes).sort();
      mk('dashHttpBar', {
        type: 'doughnut',
        data: { labels: ks.map(function (k) { return 'HTTP ' + k; }), datasets: [{ data: ks.map(function (k) { return codes[k]; }), backgroundColor: [danger, warn, info, accent, muted, '#9b8cff'], borderWidth: 2, borderColor: '#0a0e14' }] },
        options: { responsive: true, maintainAspectRatio: false, cutout: '58%', plugins: { legend: { position: 'bottom' } } }
      });
      var tb = document.getElementById('dashImportantBody');
      if (tb) {
        tb.innerHTML = T.important.map(function (u) {
          return '<tr><td><code>' + esc(u.url) + '</code></td><td>' + u.code + '</td><td>' + esc(u.status) +
            '</td><td>' + esc(u.access) + '</td><td>' + esc(u.chg) + '</td></tr>';
        }).join('');
      }
      var eb = document.getElementById('dashEventBody');
      if (eb) {
        eb.innerHTML = T.events.map(function (e) {
          return '<tr><td>' + esc(e.d) + '</td><td>' + esc(e.e) + '</td><td><code>' + esc(e.u) + '</code></td></tr>';
        }).join('');
      }
      var sb = document.getElementById('dashSerpBody');
      if (sb) {
        if (!T.serp || !T.serp.length) {
          sb.innerHTML = '<tr><td colspan="6" class="text-muted">Выгрузка ещё считается на стороне Вебмастера, запустите refresh_all.bat</td></tr>';
        } else {
          sb.innerHTML = T.serp.map(function (r) {
            return '<tr><td>' + esc(r.q) + '</td><td>' + fmtNum(r.i) + '</td><td>' + fmtNum(r.c) +
              '</td><td>' + r.ctr + '%</td><td>' + r.p + '</td><td><code>' + esc(r.u) + '</code></td></tr>';
          }).join('');
        }
      }
    })();

    // --- Аудитория
    setText('kpiVisits', fmtNum(S.visitsTotal));
    setText('kpiUsers', fmtNum(S.usersTotal));
    var lastBounce = S.bounce.length ? S.bounce[S.bounce.length - 1].v : 0;
    setText('kpiBounce', lastBounce + '%');
    setText('kpiBots', S.bots.share + '%');
    mk('dashSiteLine', {
      type: 'line',
      data: {
        labels: dLabels(S.monthly),
        datasets: [
          { label: 'Визиты', data: dValues(S.monthly), borderColor: accent, backgroundColor: accentDim, fill: true, tension: 0.35, pointRadius: 0 },
          { label: 'Посетители', data: dValues(S.monthlyUsers), borderColor: info, backgroundColor: 'transparent', fill: false, tension: 0.35, pointRadius: 0 }
        ]
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } }, scales: { y: { grid: { color: 'rgba(42,58,79,0.4)' } }, x: { grid: { display: false }, ticks: { maxTicksLimit: 12 } } } }
    });
    mk('dashBounceLine', {
      type: 'line',
      data: {
        labels: dLabels(S.bounce),
        datasets: [{ label: 'Отказы, %', data: dValues(S.bounce), borderColor: warn, backgroundColor: 'transparent', fill: false, tension: 0.3, pointRadius: 0 }]
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { grid: { color: 'rgba(42,58,79,0.4)' } }, x: { grid: { display: false }, ticks: { maxTicksLimit: 12 } } } }
    });
    (function () {
      var d = kvBars(S.devices, 4);
      mk('dashDevicesDonut', {
        type: 'doughnut',
        data: { labels: d.labels, datasets: [{ data: d.data, backgroundColor: d.colors, borderWidth: 2, borderColor: '#0a0e14' }] },
        options: { responsive: true, maintainAspectRatio: false, cutout: '60%', plugins: { legend: { position: 'bottom' } } }
      });
      var b = kvBars(S.browsers, 8);
      mk('dashBrowsersBar', {
        type: 'bar',
        data: { labels: b.labels, datasets: [{ label: 'Визиты', data: b.data, backgroundColor: b.colors, borderRadius: 4 }] },
        options: { responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: { legend: { display: false } }, scales: { x: { grid: { color: 'rgba(42,58,79,0.4)' } }, y: { grid: { display: false } } } }
      });
      var c = kvBars(S.cities, 12);
      mk('dashCitiesBar', {
        type: 'bar',
        data: { labels: c.labels, datasets: [{ label: 'Визиты', data: c.data, backgroundColor: accent, borderRadius: 4 }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { grid: { color: 'rgba(42,58,79,0.4)' } }, x: { grid: { display: false }, ticks: { maxRotation: 60, minRotation: 45 } } } }
      });
      var g = kvBars(S.gender, 3);
      mk('dashGenderDonut', {
        type: 'doughnut',
        data: { labels: g.labels.map(function (k) { return k === 'male' ? 'Мужчины' : (k === 'female' ? 'Женщины' : k); }), datasets: [{ data: g.data, backgroundColor: [info, '#9b8cff', muted], borderWidth: 2, borderColor: '#0a0e14' }] },
        options: { responsive: true, maintainAspectRatio: false, cutout: '60%', plugins: { legend: { position: 'bottom' } } }
      });
      var ag = kvBars(S.age, 8);
      mk('dashAgeBar', {
        type: 'bar',
        data: { labels: ag.labels.map(function (k) { return k + ' лет'; }), datasets: [{ label: 'Визиты', data: ag.data, backgroundColor: warn, borderRadius: 4 }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { grid: { color: 'rgba(42,58,79,0.4)' } }, x: { grid: { display: false } } } }
      });
      var it = kvBars(S.interests, 10);
      mk('dashInterestBar', {
        type: 'bar',
        data: { labels: it.labels, datasets: [{ label: 'Визиты', data: it.data, backgroundColor: info, borderRadius: 4 }] },
        options: { responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: { legend: { display: false } }, scales: { x: { grid: { color: 'rgba(42,58,79,0.4)' } }, y: { grid: { display: false } } } }
      });
      (function () {
        var series = S.sources || [];
        var months = [];
        series.forEach(function (s) {
          s.data.forEach(function (p) { if (months.indexOf(p.m) < 0) months.push(p.m); });
        });
        months.sort();
        var pal = [accent, info, warn, '#9b8cff', danger];
        mk('dashSourceLine', {
          type: 'line',
          data: {
            labels: months.map(function (m) { return m.slice(2); }),
            datasets: series.map(function (s, i) {
              var bym = {};
              s.data.forEach(function (p) { bym[p.m] = p.v; });
              return {
                label: s.name,
                data: months.map(function (m) { return bym[m] || 0; }),
                borderColor: pal[i % pal.length],
                backgroundColor: 'transparent',
                fill: false,
                tension: 0.3,
                pointRadius: 0
              };
            })
          },
          options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } }, scales: { y: { grid: { color: 'rgba(42,58,79,0.4)' } }, x: { grid: { display: false }, ticks: { maxTicksLimit: 12 } } } }
        });
      })();
      var refs = kvBars(S.referers, 20);
      mk('dashRefsBar', {
        type: 'bar',
        data: { labels: refs.labels, datasets: [{ label: 'Визиты', data: refs.data, backgroundColor: '#9b8cff', borderRadius: 4 }] },
        options: { responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: { legend: { display: false } }, scales: { x: { grid: { color: 'rgba(42,58,79,0.4)' } }, y: { grid: { display: false }, ticks: { autoSkip: false, font: { size: 10 } } } } }
      });
    })();

    // --- Деньги
    setText('kpiRevenue', fmtNum(M.revenue) + ' ₽');
    setText('kpiPurchases', fmtNum(M.purchases));
    setText('kpiGoals', fmtNum(M.goalsActive));
    setText('kpiAvg', M.purchases ? fmtNum(Math.round(M.revenue / M.purchases)) + ' ₽' : 'нет данных');
    mk('dashRevLine', {
      type: 'bar',
      data: {
        labels: M.revByMonth.map(function (x) { return x.m; }),
        datasets: [{ label: 'Выручка, ₽', data: M.revByMonth.map(function (x) { return x.v; }), backgroundColor: accent, borderRadius: 4 }]
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { callbacks: { label: function (c) { return fmtNum(c.raw) + ' ₽'; } } } }, scales: { y: { grid: { color: 'rgba(42,58,79,0.4)' } }, x: { grid: { display: false } } } }
    });
    (function () {
      var t = M.topDays;
      mk('dashRevDayBar', {
        type: 'bar',
        data: { labels: t.map(function (x) { return x.d.slice(5); }), datasets: [{ label: 'Выручка, ₽', data: t.map(function (x) { return x.v; }), backgroundColor: [accent, info, warn, danger, muted, '#9b8cff', '#ff9d6b', '#5ad1e6'], borderRadius: 4 }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { callbacks: { label: function (c) { return fmtNum(c.raw) + ' ₽, заказов ' + (t[c.dataIndex].p); } } } }, scales: { y: { grid: { color: 'rgba(42,58,79,0.4)' } }, x: { grid: { display: false } } } }
      });
      var gb = document.getElementById('dashGoalBody');
      if (gb) {
        gb.innerHTML = M.goals.map(function (g) {
          return '<tr><td>' + esc(g.n) + '</td><td>' + esc(g.t) + '</td><td>' + esc(g.s) + '</td></tr>';
        }).join('');
      }
      var lp = kvBars(S.landing, 15);
      mk('dashLandingBar', {
        type: 'bar',
        data: { labels: lp.labels, datasets: [{ label: 'Визиты', data: lp.data, backgroundColor: info, borderRadius: 4 }] },
        options: { responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: { legend: { display: false } }, scales: { x: { grid: { color: 'rgba(42,58,79,0.4)' } }, y: { grid: { display: false }, ticks: { font: { size: 10 } } } } }
      });
      var ph = kvBars(S.phrases, 20);
      mk('dashPhraseBar', {
        type: 'bar',
        data: { labels: ph.labels, datasets: [{ label: 'Визиты', data: ph.data, backgroundColor: warn, borderRadius: 4 }] },
        options: { responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: { legend: { display: false } }, scales: { x: { grid: { color: 'rgba(42,58,79,0.4)' } }, y: { grid: { display: false }, ticks: { font: { size: 10 } } } } }
      });
    })();

    // --- Карточка в Яндекс Картах
    setText('kpiMapViews', fmtNum(MP.viewsTotal));
    setText('kpiMapCalls', fmtNum(MP.goals.calls || 0));
    setText('kpiMapRoutes', fmtNum(MP.goals.routes || 0));
    setText('kpiMapSite', fmtNum(MP.goals.site || 0));
    mk('dashMapsLine', {
      type: 'line',
      data: {
        labels: dLabels(MP.monthly),
        datasets: [{ label: 'Просмотры карточки', data: dValues(MP.monthly), borderColor: info, backgroundColor: 'rgba(77,163,255,0.15)', fill: true, tension: 0.35, pointRadius: 0 }]
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { grid: { color: 'rgba(42,58,79,0.4)' } }, x: { grid: { display: false }, ticks: { maxTicksLimit: 12 } } } }
    });
    (function () {
      var a = kvBars(MP.actions, 12);
      mk('dashMapsActionBar', {
        type: 'bar',
        data: { labels: a.labels, datasets: [{ label: 'События', data: a.data, backgroundColor: a.colors, borderRadius: 4 }] },
        options: { responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: { legend: { display: false } }, scales: { x: { grid: { color: 'rgba(42,58,79,0.4)' } }, y: { grid: { display: false }, ticks: { font: { size: 10 } } } } }
      });
      var e = kvBars(MP.entries, 12);
      mk('dashMapsEntryBar', {
        type: 'bar',
        data: { labels: e.labels, datasets: [{ label: 'Просмотры', data: e.data, backgroundColor: accent, borderRadius: 4 }] },
        options: { responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: { legend: { display: false } }, scales: { x: { grid: { color: 'rgba(42,58,79,0.4)' } }, y: { grid: { display: false }, ticks: { font: { size: 10 } } } } }
      });
      var s = kvBars(MP.search, 12);
      mk('dashMapsSearchBar', {
        type: 'bar',
        data: { labels: s.labels, datasets: [{ label: 'Просмотры', data: s.data, backgroundColor: '#9b8cff', borderRadius: 4 }] },
        options: { responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: { legend: { display: false } }, scales: { x: { grid: { color: 'rgba(42,58,79,0.4)' } }, y: { grid: { display: false }, ticks: { font: { size: 10 } } } } }
      });
      var so = kvBars(MP.sources, 8);
      mk('dashMapsSourceDonut', {
        type: 'doughnut',
        data: { labels: so.labels, datasets: [{ data: so.data, backgroundColor: so.colors, borderWidth: 2, borderColor: '#0a0e14' }] },
        options: { responsive: true, maintainAspectRatio: false, cutout: '60%', plugins: { legend: { position: 'bottom' } } }
      });
    })();
  }

  // Interactive checklists (quick wins) with localStorage
  var interactiveLists = document.querySelectorAll('.checklist.interactive');
  interactiveLists.forEach(function (list) {
    var key = 'cifra18-check-' + (list.getAttribute('data-key') || 'default');
    var saved = {};
    try { saved = JSON.parse(localStorage.getItem(key) || '{}'); } catch (e) { saved = {}; }
    var items = list.querySelectorAll('li');
    items.forEach(function (li, idx) {
      var box = li.querySelector('.checkbox');
      if (!box) return;
      li.style.cursor = 'pointer';
      if (saved[idx]) { box.classList.add('done'); box.textContent = '✓'; }
      li.addEventListener('click', function () {
        var on = box.classList.toggle('done');
        box.textContent = on ? '✓' : (box.getAttribute('data-num') || '');
        saved[idx] = on ? 1 : 0;
        try { localStorage.setItem(key, JSON.stringify(saved)); } catch (e) {}
        updateProgress(list, key);
      });
    });
    updateProgress(list, key);
  });

  function updateProgress(list, key) {
    var bar = document.querySelector('[data-progress-for="' + list.getAttribute('data-key') + '"]');
    if (!bar) return;
    var boxes = list.querySelectorAll('.checkbox');
    var done = list.querySelectorAll('.checkbox.done').length;
    var pct = boxes.length ? Math.round((done / boxes.length) * 100) : 0;
    bar.style.width = pct + '%';
    var label = document.querySelector('[data-progress-label="' + list.getAttribute('data-key') + '"]');
    if (label) label.textContent = done + ' из ' + boxes.length + ' (' + pct + '%)';
  }
})();
