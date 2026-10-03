(function () {
  'use strict';

  const LEAD_ENDPOINT = '/api/lead';
  const QUIZ_ENDPOINT = '/api/quiz-lead';
  const { CATALOG_GROUPS, QUIZ_COMMON_FIELDS } = window.Catalog;

  // Единственные бизнес-специфичные константы во всём движке —
  // подставляются render.js из config.contact / config.site.
  const FALLBACK_PHONE_DISPLAY = '+7 (3412) 32-32-41';
  const CONTACT_EMAIL = 'izhcifra@yandex.ru';
  const SITE_DOMAIN = 'xn--18-6kc5a3bxam.xn--p1ai';

  // ---------- Рендер каталога (блок 4, витрина) ----------
  // Каждая функция инициализации проверяет свой корень и молча выходит, если его
  // нет. Раньше проверял только initQuiz, а renderCatalog() начинал с
  // getElementById('catalog-container') и падал на null ВЫШЕ по цепочке:
  // TypeError обрывал весь обработчик DOMContentLoaded, и ни квиз, ни форма,
  // ни cookie-баннер не навешивались. Набор блоков на странице меняется
  // (рендер-wp.js собирает не все секции), поэтому корень отсутствует — это
  // норма, а не ошибка сборки.
  function renderCatalog() {
    const container = document.getElementById('catalog-container');
    if (!container) return;
    CATALOG_GROUPS.forEach((group) => {
      const groupEl = document.createElement('div');
      groupEl.className = 'catalog-group';
      groupEl.dataset.reveal = '';

      const heading = document.createElement('h3');
      heading.textContent = group.title;
      groupEl.appendChild(heading);

      if (group.intro) {
        const introP = document.createElement('p');
        introP.className = 'catalog-group-intro';
        introP.textContent = group.intro;
        groupEl.appendChild(introP);
      }

      const grid = document.createElement('div');
      grid.className = 'catalog-grid';

      (group.items || []).forEach((item) => {
        const card = document.createElement('article');
        card.className = 'item-card';
        card.innerHTML = `
          <div class="thumb"><img src="${item.img}" alt="${item.name}" loading="lazy" width="1100" height="777"></div>
          <div class="body">
            <h4>${item.name}</h4>
            <p class="specs">${item.specs}</p>
            <div class="item-card-footer">
              <span class="method-tag">${item.method}</span>
              ${item.priceFrom ? `<span class="price-tag">${item.priceFrom}</span>` : ''}
            </div>
          </div>`;
        grid.appendChild(card);
      });

      groupEl.appendChild(grid);
      container.appendChild(groupEl);
    });
  }

  // ---------- Анимации (опционально, сайт рабочий и без них) ----------
  function initAnimations() {
    // ScrollTrigger грузится отдельным CDN-скриптом: если gsap есть, а плагин
    // ещё не загрузился, registerPlugin бросает и обрывает цепочку инициализации.
    if (!window.gsap || !window.ScrollTrigger) return;
    gsap.registerPlugin(ScrollTrigger);

    const stampTarget = document.querySelector('[data-stamp]');
    if (stampTarget) {
      gsap.fromTo(stampTarget,
        { opacity: 0, y: 20, scale: 1.03 },
        { opacity: 1, y: 0, scale: 1, duration: 0.7, ease: 'power3.out' });
    }

    gsap.from('.hero-lead, .eyebrow, .hero-cta, .hero-stats, .hero-visual', {
      opacity: 0, y: 16, duration: 0.6, delay: 0.2, stagger: 0.08, ease: 'power2.out'
    });

    document.querySelectorAll('section').forEach((section) => {
      const items = section.querySelectorAll('[data-reveal]');
      if (!items.length) return;
      gsap.from(items, {
        opacity: 0, y: 20, duration: 0.5, stagger: 0.05, ease: 'power2.out',
        scrollTrigger: { trigger: section, start: 'top 80%' }
      });
    });
  }

  // ============================================================
  //  КВИЗ-ВИЗАРД (блок 6) — 4 шага. Общий движок, специфика бизнеса
  //  живёт только в catalog.js (сгенерирован render.js из config.catalog).
  // ============================================================
  function initQuiz() {
    const app = document.getElementById('quiz-app');
    if (!app) return;

    const state = { step: 1, groupId: null, itemId: null, qty: 20, layout: null, deadline: null, notes: '' };

    const groupsEl = document.getElementById('quiz-groups');
    const itemsEl = document.getElementById('quiz-items');
    const layoutEl = document.getElementById('q-layout');
    const deadlineEl = document.getElementById('q-deadline');
    const qtyInput = document.getElementById('q-qty');
    const notesInput = document.getElementById('q-notes');
    const selectedItemBox = document.getElementById('quiz-selected-item');
    const finalSummaryBox = document.getElementById('quiz-final-summary');
    const progressFill = document.getElementById('quiz-progress-fill');

    function currentGroup() {
      return CATALOG_GROUPS.find((g) => g.id === state.groupId) || null;
    }
    function currentItem() {
      const g = currentGroup();
      return g ? g.items.find((i) => i.id === state.itemId) : null;
    }

    function renderGroups() {
      groupsEl.innerHTML = '';
      CATALOG_GROUPS.forEach((g) => {
        const card = document.createElement('button');
        card.type = 'button';
        card.className = 'quiz-card' + (g.id === state.groupId ? ' is-selected' : '');
        card.innerHTML = `<span class="quiz-card-title">${g.title}</span><span class="quiz-card-sub">${g.items.length} позиций</span>`;
        card.addEventListener('click', () => {
          state.groupId = g.id;
          state.itemId = null;
          renderGroups();
          renderItems();
          goToStep(2);
        });
        groupsEl.appendChild(card);
      });
    }

    function renderItems() {
      const g = currentGroup();
      itemsEl.innerHTML = '';
      if (!g) return;
      g.items.forEach((item) => {
        const card = document.createElement('button');
        card.type = 'button';
        card.className = 'quiz-card quiz-card-item' + (item.id === state.itemId ? ' is-selected' : '');
        card.innerHTML = `
          <img src="${item.img}" alt="" loading="lazy">
          <span class="quiz-card-title">${item.name}</span>
          <span class="quiz-card-sub">${item.method}${item.priceFrom ? ' · ' + item.priceFrom : ''}</span>`;
        card.addEventListener('click', () => {
          state.itemId = item.id;
          renderItems();
          renderStep3();
          goToStep(3);
        });
        itemsEl.appendChild(card);
      });
    }

    function renderRadioRow(container, options, groupName, currentValue, onPick) {
      container.innerHTML = '';
      options.forEach((opt) => {
        const id = `${groupName}-${opt.value}`;
        const label = document.createElement('label');
        label.className = 'quiz-radio' + (currentValue === opt.value ? ' is-selected' : '');
        label.innerHTML = `<input type="radio" name="${groupName}" id="${id}" value="${opt.value}"${currentValue === opt.value ? ' checked' : ''}> ${opt.label}`;
        label.querySelector('input').addEventListener('change', () => onPick(opt.value));
        container.appendChild(label);
      });
    }

    function renderStep3() {
      const item = currentItem();
      selectedItemBox.innerHTML = item
        ? `<b>${item.name}</b>${item.priceFrom ? ` <span class="price-tag">${item.priceFrom}</span>` : ''}<br><span>${item.method} · ${item.specs}</span>`
        : '';

      renderRadioRow(layoutEl, QUIZ_COMMON_FIELDS.layoutOptions, 'q-layout', state.layout, (v) => { state.layout = v; renderStep3(); });
      renderRadioRow(deadlineEl, QUIZ_COMMON_FIELDS.deadlineOptions, 'q-deadline', state.deadline, (v) => { state.deadline = v; renderStep3(); });
    }

    qtyInput.addEventListener('input', () => { state.qty = Number(qtyInput.value) || 0; });
    notesInput.addEventListener('input', () => { state.notes = notesInput.value.trim(); });

    function goToStep(n) {
      state.step = n;
      app.querySelectorAll('.quiz-step').forEach((el) => {
        el.classList.toggle('is-active', Number(el.dataset.step) === n);
      });
      app.querySelectorAll('.qp-step').forEach((el) => {
        const idx = Number(el.dataset.stepIndicator);
        el.classList.toggle('is-active', idx === n);
        el.classList.toggle('is-done', idx < n);
      });
      progressFill.style.width = `${(n - 1) / 3 * 100}%`;
      if (n === 4) renderFinalSummary();
      app.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    app.querySelectorAll('.quiz-back').forEach((btn) => {
      btn.addEventListener('click', () => goToStep(Number(btn.dataset.back)));
    });

    document.getElementById('quiz-to-step4').addEventListener('click', () => {
      if (!currentItem()) { goToStep(2); return; }
      goToStep(4);
    });

    function layoutLabel(v) {
      const f = QUIZ_COMMON_FIELDS.layoutOptions.find((o) => o.value === v);
      return f ? f.label : 'не указано';
    }
    function deadlineLabel(v) {
      const f = QUIZ_COMMON_FIELDS.deadlineOptions.find((o) => o.value === v);
      return f ? f.label : 'не указано';
    }

    function buildSummaryText() {
      const g = currentGroup();
      const item = currentItem();
      if (!g || !item) return '';
      const parts = [
        `Категория: ${g.title}`,
        `Товар: ${item.name} (${item.method})`,
        `Количество: ${state.qty} шт.`,
        `Готовность: ${layoutLabel(state.layout)}`,
        `Срок: ${deadlineLabel(state.deadline)}`
      ];
      if (state.notes) parts.push(`Пожелания: ${state.notes}`);
      return parts.join('\n');
    }

    function renderFinalSummary() {
      finalSummaryBox.innerHTML = buildSummaryText().split('\n').map((l) => `<div>${l}</div>`).join('');
      updateMailtoLink();
    }

    const mailtoLink = document.getElementById('quiz-mailto-link');
    function updateMailtoLink() {
      if (!mailtoLink) return;
      const item = currentItem();
      const name = (document.getElementById('q-name') || {}).value || '';
      const phone = (document.getElementById('q-phone') || {}).value || '';

      const subject = `Расчёт с сайта ${SITE_DOMAIN}${item ? ' — ' + item.name : ''}`;
      const bodyLines = [
        'Здравствуйте!',
        '',
        `Пишу с сайта ${SITE_DOMAIN} — прошёл(-ла) квиз-расчёт, вот что интересует:`,
        '',
        buildSummaryText(),
        ''
      ];
      if (name.trim()) bodyLines.push(`Имя: ${name.trim()}`);
      if (phone.trim()) bodyLines.push(`Телефон: ${phone.trim()}`);

      mailtoLink.href = `mailto:${CONTACT_EMAIL}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(bodyLines.join('\n'))}`;
    }

    ['q-name', 'q-phone'].forEach((id) => {
      const el = document.getElementById(id);
      if (el) el.addEventListener('input', () => { if (state.step === 4) updateMailtoLink(); });
    });

    const quizForm = document.getElementById('quiz-form');
    const quizStatus = document.getElementById('quiz-status');

    function isPlausiblePhone(value) {
      const digits = value.replace(/\D/g, '');
      return digits.length >= 10 && digits.length <= 12;
    }

    quizForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      quizStatus.textContent = '';
      quizStatus.removeAttribute('data-state');

      const name = quizForm.name.value.trim();
      const phone = quizForm.phone.value.trim();
      const email = quizForm.email.value.trim();
      const website = quizForm.website.value;

      if (website) {
        quizStatus.textContent = 'Расчёт отправлен, спасибо!';
        quizStatus.setAttribute('data-state', 'ok');
        quizForm.reset();
        return;
      }

      if (!name || !isPlausiblePhone(phone)) {
        quizStatus.textContent = 'Проверьте, пожалуйста, имя и телефон.';
        quizStatus.setAttribute('data-state', 'error');
        return;
      }
      if (!quizForm.consent.checked) {
        quizStatus.textContent = 'Нужно согласие на обработку персональных данных — отметьте галочку.';
        quizStatus.setAttribute('data-state', 'error');
        return;
      }
      if (!currentItem()) {
        quizStatus.textContent = 'Похоже, товар не выбран — вернитесь на шаг 2.';
        quizStatus.setAttribute('data-state', 'error');
        return;
      }

      const g = currentGroup();
      const item = currentItem();

      const payload = {
        name, phone, email, website,
        utm: window.location.search || '',
        quiz: {
          group: g.title,
          item: item.name,
          method: item.method,
          qty: state.qty,
          layout: layoutLabel(state.layout),
          deadline: deadlineLabel(state.deadline),
          notes: state.notes
        },
        summary: buildSummaryText()
      };

      const submitBtn = quizForm.querySelector('button[type="submit"]');
      submitBtn.disabled = true;
      quizStatus.textContent = 'Отправляем расчёт…';

      try {
        const res = await fetch(QUIZ_ENDPOINT, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error('bad_status_' + res.status);

        quizStatus.textContent = 'Готово! Расчёт получен, менеджер свяжется с вами и продублирует его на почту.';
        quizStatus.setAttribute('data-state', 'ok');
        quizForm.reset();
        // Номер счётчика приходит из config.analytics.yandexMetrikaId — раньше он был
        // зашит как 12345678, и цели уходили в чужой счётчик, даже если в HTML
        // подставлялся правильный. Плейсхолдер обязателен: '0' означает «счётчик не задан».
        if (window.ym) { try { ym(50863157, 'reachGoal', 'quiz_submit'); } catch (_) {} }
      } catch (err) {
        quizStatus.textContent = `Не получилось отправить. Позвоните нам: ${FALLBACK_PHONE_DISPLAY}`;
        quizStatus.setAttribute('data-state', 'error');
      } finally {
        submitBtn.disabled = false;
      }
    });

    renderGroups();
  }

  // ---------- Простая форма заявки (блок 9, без квиза) ----------
  function initForm() {
    const form = document.getElementById('lead-form');
    if (!form) return;
    const statusEl = document.getElementById('form-status');
    const utmField = document.getElementById('f-utm');
    if (utmField) utmField.value = window.location.search || '';

    function isPlausiblePhone(value) {
      const digits = value.replace(/\D/g, '');
      return digits.length >= 10 && digits.length <= 12;
    }

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      statusEl.textContent = '';
      statusEl.removeAttribute('data-state');

      const name = form.name.value.trim();
      const phone = form.phone.value.trim();
      const website = form.website.value;

      if (website) {
        statusEl.textContent = 'Заявка отправлена, спасибо!';
        statusEl.setAttribute('data-state', 'ok');
        form.reset();
        return;
      }

      if (!name || !isPlausiblePhone(phone)) {
        statusEl.textContent = 'Проверьте, пожалуйста, имя и телефон.';
        statusEl.setAttribute('data-state', 'error');
        return;
      }
      if (!form.consent.checked) {
        statusEl.textContent = 'Нужно согласие на обработку персональных данных — отметьте галочку.';
        statusEl.setAttribute('data-state', 'error');
        return;
      }

      const payload = {
        name, phone,
        comment: form.comment.value.trim(),
        calcSummary: form.calcSummary.value,
        utm: form.utm.value,
        website
      };

      const submitBtn = form.querySelector('button[type="submit"]');
      submitBtn.disabled = true;
      statusEl.textContent = 'Отправляем…';

      try {
        const res = await fetch(LEAD_ENDPOINT, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error('bad_status_' + res.status);

        statusEl.textContent = 'Заявка отправлена, свяжемся в ближайшее время!';
        statusEl.setAttribute('data-state', 'ok');
        form.reset();
        if (window.ym) { try { ym(50863157, 'reachGoal', 'lead_submit'); } catch (_) {} }
      } catch (err) {
        statusEl.textContent = `Не получилось отправить. Позвоните нам: ${FALLBACK_PHONE_DISPLAY}`;
        statusEl.setAttribute('data-state', 'error');
      } finally {
        submitBtn.disabled = false;
      }
    });
  }

  // ---------- Cookie-баннер (152-ФЗ): Метрика стартует только после согласия ----------
  function initCookieConsent() {
    const KEY = 'cookie_consent_v1';
    const banner = document.getElementById('cookie-banner');
    const acceptBtn = document.getElementById('cookie-accept');
    if (!banner || !acceptBtn) return;

    function startAnalytics() {
      if (typeof window.__initYandexMetrika === 'function') {
        try { window.__initYandexMetrika(); } catch (_) {}
      }
    }

    let alreadyAccepted = false;
    try { alreadyAccepted = localStorage.getItem(KEY) === '1'; } catch (_) {}

    if (alreadyAccepted) {
      startAnalytics();
    } else {
      banner.hidden = false;
    }

    acceptBtn.addEventListener('click', () => {
      try { localStorage.setItem(KEY, '1'); } catch (_) {}
      banner.hidden = true;
      startAnalytics();
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    renderCatalog();
    initQuiz();
    initForm();
    initAnimations();
    initCookieConsent();
  });
})();
