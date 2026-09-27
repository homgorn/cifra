/*
  Поиск по всему отчёту. 27 страниц, и найти нужную в списке не всегда удобно.
  Работает без сервера: индекс лежит в js/page-index.js, совпадение по названию,
  описанию и номеру страницы. Открывается кнопкой в шапке или клавишей «/».
*/
(function () {
  'use strict';

  var IDX = (typeof PAGES !== 'undefined') ? PAGES : [];
  if (!IDX.length) return;

  function here() {
    var p = window.location.pathname;
    return p.substring(p.lastIndexOf('/') + 1);
  }

  function rel(slug) {
    if (here() === 'index.html') return slug;
    return '../' + slug;
  }

  function norm(s) {
    return (s || '').toLowerCase().replace(/ё/g, 'е');
  }

  function score(item, q) {
    var t = norm(item.t), d = norm(item.d), s = norm(item.s);
    if (t === q) return 100;
    if (t.indexOf(q) === 0) return 80;
    if (t.indexOf(q) > -1) return 60;
    if (s.indexOf(q) > -1) return 40;
    if (d.indexOf(q) > -1) return 25;
    if (String(item.n) === q) return 90;
    return 0;
  }

  function build() {
    var wrap = document.createElement('div');
    wrap.className = 'search-panel';
    wrap.setAttribute('hidden', 'hidden');
    wrap.innerHTML =
      '<div class="search-surface">' +
      '  <div class="search-box" role="search">' +
      '    <input type="search" class="search-input" placeholder="Найти страницу: дубли, позиции, цены" aria-label="Поиск по отчёту">' +
      '    <button class="search-close" type="button" aria-label="Закрыть">Esc</button>' +
      '  </div>' +
      '  <ul class="search-results"></ul>' +
      '  <p class="search-empty" hidden>Ничего не нашлось. Попробуйте «кластеры», «цены», «SQI».</p>' +
      '</div>';

    var btn = document.createElement('button');
    btn.className = 'search-open';
    btn.type = 'button';
    btn.setAttribute('aria-label', 'Поиск по отчёту');
    btn.innerHTML = 'Поиск <span class="search-key">/</span>';

    var input = wrap.querySelector('.search-input');
    var list = wrap.querySelector('.search-results');
    var empty = wrap.querySelector('.search-empty');
    var active = -1;

    function render(q) {
      q = norm(q);
      list.innerHTML = '';
      empty.hidden = true;
      active = -1;
      if (q.length < 2) {
        list.innerHTML = IDX.slice(0, 8).map(function (i) {
          return '<li><a href="' + rel(i.p) + '"><span class="sr-num">' + i.n + '</span>' +
            '<span class="sr-t">' + i.t + '</span><span class="sr-s">' + i.s + '</span></a></li>';
        }).join('');
        return;
      }
      var hits = IDX.map(function (i) { return { i: i, s: score(i, q) }; })
        .filter(function (x) { return x.s > 0; })
        .sort(function (a, b) { return b.s - a.s || a.i.n - b.i.n; })
        .slice(0, 10);
      if (!hits.length) { empty.hidden = false; return; }
      list.innerHTML = hits.map(function (h) {
        return '<li><a href="' + rel(h.i.p) + '"><span class="sr-num">' + h.i.n + '</span>' +
          '<span class="sr-t">' + h.i.t + '</span><span class="sr-d">' + h.i.d + '</span></a></li>';
      }).join('');
    }

    function mark(i) {
      var items = list.querySelectorAll('li');
      if (!items.length) return;
      if (i < 0) i = items.length - 1;
      if (i >= items.length) i = 0;
      items.forEach(function (el) { el.classList.remove('on'); });
      items[i].classList.add('on');
      active = i;
    }

    function open() {
      wrap.hidden = false;
      document.body.classList.add('search-open-state');
      input.focus();
      input.select();
      render(input.value);
      mark(0);
    }
    function close() {
      wrap.hidden = true;
      document.body.classList.remove('search-open-state');
      input.blur();
    }

    btn.addEventListener('click', open);
    wrap.querySelector('.search-close').addEventListener('click', close);
    input.addEventListener('input', function () { render(input.value); });
    input.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown') { e.preventDefault(); mark(active + 1); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); mark(active - 1); }
      else if (e.key === 'Enter') {
        var on = list.querySelector('li.on a') || list.querySelector('a');
        if (on) { e.preventDefault(); window.location.href = on.getAttribute('href'); }
      } else if (e.key === 'Escape') { close(); }
    });
    wrap.addEventListener('click', function (e) { if (e.target === wrap) close(); });
    document.addEventListener('keydown', function (e) {
      if (e.key === '/' && !/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName)) {
        e.preventDefault();
        open();
      } else if (e.key === 'Escape' && !wrap.hidden) {
        close();
      }
    });

    var header = document.querySelector('.header-inner');
    if (header) header.appendChild(btn);
    document.body.appendChild(wrap);
    render('');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', build);
  } else {
    build();
  }
})();
