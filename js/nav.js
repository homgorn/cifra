/*
  Поведение интерфейса: полоса прогресса, подсветка раздела, кнопка «Наверх»,
  фильтр длинных таблиц, якорные ссылки у заголовков.

  Принцип: движение появляется только там, где отвечает на действие человека.
  Никакого украшения ради украшения. prefers-reduced-motion отключает переходы.
*/
(function () {
  'use strict';

  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* 1. Полоса прогресса чтения: показывает, где читатель, отвечает на скролл */
  function progress() {
    var bar = document.createElement('div');
    bar.className = 'read-progress';
    bar.setAttribute('aria-hidden', 'true');
    document.body.appendChild(bar);
    var toTop = document.createElement('button');
    toTop.className = 'to-top';
    toTop.type = 'button';
    toTop.setAttribute('aria-label', 'Наверх');
    toTop.textContent = '↑';
    toTop.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: reduce ? 'auto' : 'smooth' });
    });
    document.body.appendChild(toTop);

    var ticking = false;
    function onScroll() {
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(function () {
        var h = document.documentElement.scrollHeight - window.innerHeight;
        var pct = h > 0 ? Math.min(100, (window.scrollY / h) * 100) : 0;
        bar.style.width = pct.toFixed(2) + '%';
        toTop.classList.toggle('show', window.scrollY > 600);
        ticking = false;
      });
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* 2. Подсветка текущего раздела в боковом меню */
  function spy() {
    var links = document.querySelectorAll('.sidebar-link[href^="#"]');
    if (!links.length) return;
    var map = {};
    var targets = [];
    links.forEach(function (a) {
      var id = a.getAttribute('href').slice(1);
      var el = document.getElementById(id);
      if (!el) return;
      map[id] = a;
      targets.push(el);
    });
    if (!targets.length) return;
    var ticking = false;
    function update() {
      var line = window.scrollY + (window.innerHeight * 0.3);
      var cur = targets[0];
      targets.forEach(function (t) { if (t.offsetTop <= line) cur = t; });
      links.forEach(function (a) { a.classList.remove('current'); });
      if (map[cur.id]) map[cur.id].classList.add('current');
      ticking = false;
    }
    window.addEventListener('scroll', function () {
      if (!ticking) { ticking = true; window.requestAnimationFrame(update); }
    }, { passive: true });
    update();
  }

  /* 3. Якорные ссылки у заголовков: можно поделиться конкретным разделом */
  function anchors() {
    var heads = document.querySelectorAll('main h2[id], main h3[id]');
    if (!heads.length) return;
    Array.prototype.forEach.call(heads, function (h) {
      if (h.querySelector('.section-anchor')) return;
      var a = document.createElement('a');
      a.className = 'section-anchor';
      a.href = '#' + h.id;
      a.textContent = '#';
      a.setAttribute('aria-label', 'Ссылка на раздел');
      a.addEventListener('click', function (ev) {
        ev.preventDefault();
        var url = window.location.href.split('#')[0] + '#' + h.id;
        if (window.history && history.replaceState) history.replaceState(null, '', '#' + h.id);
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(url).then(function () {
            a.textContent = 'скопировано';
            a.classList.add('copied');
            window.setTimeout(function () {
              a.textContent = '#';
              a.classList.remove('copied');
            }, 1600);
          }, function () { window.location.hash = h.id; });
        } else {
          window.location.hash = h.id;
        }
      });
      h.appendChild(a);
    });
  }

  /* 4. Фильтр по длинным таблицам: в ядре 492 запроса, искать нужно руками */
  function filters() {
    var tables = document.querySelectorAll('.table-wrapper table');
    if (!tables.length) return;
    Array.prototype.forEach.call(tables, function (table) {
      var rows = table.tBodies[0] ? table.tBodies[0].rows : [];
      if (rows.length < 15) return;              // короткие таблицы не трогаем
      var label = table.closest('.table-wrapper').previousElementSibling;
      var hint = 'Поиск по таблице';
      if (label && label.classList.contains('card-subtitle')) hint = label.textContent.slice(0, 60);
      var tools = document.createElement('div');
      tools.className = 'table-tools';
      var input = document.createElement('input');
      input.type = 'search';
      input.className = 'table-filter';
      input.placeholder = hint;
      input.setAttribute('aria-label', 'Фильтр строк таблицы');
      var count = document.createElement('span');
      count.className = 'table-count';
      count.textContent = rows.length + ' строк';
      tools.appendChild(input);
      tools.appendChild(count);
      table.parentNode.parentNode.insertBefore(tools, table.parentNode);
      input.addEventListener('input', function () {
        var q = input.value.trim().toLowerCase();
        var shown = 0;
        Array.prototype.forEach.call(rows, function (r) {
          var hit = !q || r.textContent.toLowerCase().indexOf(q) > -1;
          r.classList.toggle('row-hidden', !hit);
          if (hit) shown++;
        });
        count.textContent = shown + ' из ' + rows.length;
      });
    });
  }

  function init() {
    progress();
    spy();
    anchors();
    filters();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
