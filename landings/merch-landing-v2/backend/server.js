/**
 * server.js — прокси между формами лендинга (простая заявка + квиз-расчёт)
 * и двумя каналами доставки лида: Bitrix24 (CRM) и почта (nodemailer).
 *
 * ЗАЧЕМ ОТДЕЛЬНЫЙ БЭКЕНД, А НЕ ПРЯМОЙ ЗАПРОС ИЗ БРАУЗЕРА:
 *   1) Входящий webhook Bitrix24 — секрет уровня API-ключа. Вызов прямо из
 *      клиентского JS светит URL с ключом в devtools любому посетителю.
 *   2) SMTP-креды тем более нельзя отдавать в браузер.
 *   Прокси держит оба секрета на сервере и решает, какие поля вообще
 *   долетают до CRM/почты.
 *
 * ДВА КАНАЛА, ОБА — «ЛУЧШЕЕ УСИЛИЕ» (Promise.allSettled):
 *   Заказчик просил, чтобы расчёт из квиза уходил на почту — это сделано
 *   безусловно на обоих роутах. Bitrix оставлен как было раньше (нужен для
 *   учёта лидов в CRM). Если один канал недоступен — второй всё равно
 *   должен доставить заявку; лид не должен теряться из-за падения одного
 *   сервиса. Роут отвечает ok, если сработал хотя бы один канал.
 *
 * Запуск:
 *   BITRIX_WEBHOOK_URL="https://your.bitrix24.ru/rest/1/xxxxxxxx/" \
 *   SMTP_HOST="smtp.yandex.ru" SMTP_PORT="465" SMTP_SECURE="true" \
 *   SMTP_USER="izhcifra@yandex.ru" SMTP_PASS="xxxx" \
 *   MAIL_TO="izhcifra@yandex.ru" \
 *   ALLOWED_ORIGIN="https://xn--18-6kc5a3bxam.xn--p1ai" \
 *   node server.js
 *
 * САМОКРИТИКА (см. также в чате): без реальных SMTP_* переменных почтовый
 * канал молча отключается (см. isEmailConfigured) — сайт при этом не падает,
 * но и писем не будет, пока заказчик не даст доступ к почтовому ящику/SMTP.
 * Это НЕ автоматически настроится само — обязательно нужно прогнать реальный
 * тест отправки перед продакшеном.
 */

const express = require('express');
const helmet = require('helmet');
const cors = require('cors');
const nodemailer = require('nodemailer');

const PORT = process.env.PORT || 3000;
const BITRIX_WEBHOOK_URL = process.env.BITRIX_WEBHOOK_URL; // если не задан — канал в CRM просто пропускается
const ALLOWED_ORIGIN = process.env.ALLOWED_ORIGIN || '*'; // на проде — конкретный домен лендинга, не '*'

const SMTP_HOST = process.env.SMTP_HOST;
const SMTP_PORT = Number(process.env.SMTP_PORT || 465);
const SMTP_SECURE = process.env.SMTP_SECURE !== 'false'; // true по умолчанию (порт 465)
const SMTP_USER = process.env.SMTP_USER;
const SMTP_PASS = process.env.SMTP_PASS;
const MAIL_TO = process.env.MAIL_TO || 'izhcifra@yandex.ru';
const MAIL_FROM = process.env.MAIL_FROM || SMTP_USER;

if (!BITRIX_WEBHOOK_URL) {
  console.warn('WARN: BITRIX_WEBHOOK_URL не задан — лиды НЕ будут уходить в Bitrix24, только почта (если настроена).');
}

const isEmailConfigured = Boolean(SMTP_HOST && SMTP_USER && SMTP_PASS);
if (!isEmailConfigured) {
  console.warn('WARN: SMTP_* не заданы — расчёты из квиза НЕ будут уходить на почту, только в Bitrix24 (если настроен).');
}
if (!BITRIX_WEBHOOK_URL && !isEmailConfigured) {
  console.error('FATAL: не настроен ни Bitrix24, ни почта — лиды девать некуда. Останов.');
  process.exit(1);
}

const mailTransport = isEmailConfigured
  ? nodemailer.createTransport({
      host: SMTP_HOST,
      port: SMTP_PORT,
      secure: SMTP_SECURE,
      auth: { user: SMTP_USER, pass: SMTP_PASS }
    })
  : null;

const app = express();
app.use(helmet());
app.use(cors({ origin: ALLOWED_ORIGIN, methods: ['POST'] }));
app.use(express.json({ limit: '10kb' })); // лид маленький; ограничение — защита от переливания тела запроса

// ---------- Простой rate limit по IP, без внешних зависимостей ----------
// Для продакшена с несколькими инстансами замените на Redis-backed лимитер
// (напр. rate-limiter-flexible) — этот вариант работает только в памяти одного процесса.
const RATE_LIMIT_WINDOW_MS = 60_000;
const RATE_LIMIT_MAX = 5;
const hits = new Map();

function isRateLimited(ip) {
  const now = Date.now();
  const windowStart = now - RATE_LIMIT_WINDOW_MS;
  const timestamps = (hits.get(ip) || []).filter((t) => t > windowStart);
  timestamps.push(now);
  hits.set(ip, timestamps);
  return timestamps.length > RATE_LIMIT_MAX;
}

setInterval(() => {
  const windowStart = Date.now() - RATE_LIMIT_WINDOW_MS;
  for (const [ip, timestamps] of hits.entries()) {
    const fresh = timestamps.filter((t) => t > windowStart);
    if (fresh.length === 0) hits.delete(ip);
    else hits.set(ip, fresh);
  }
}, RATE_LIMIT_WINDOW_MS).unref();

// ---------- Общая валидация контактов ----------
function normalizePhone(raw) {
  const digits = String(raw || '').replace(/\D/g, '');
  return digits.length >= 10 && digits.length <= 12 ? digits : null;
}
function isPlausibleEmail(raw) {
  const value = String(raw || '').trim();
  if (!value) return true; // email необязателен
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value) && value.length <= 200;
}

function validateContact(body) {
  const errors = [];
  const name = String(body.name || '').trim().slice(0, 120);
  const phoneDigits = normalizePhone(body.phone);
  const email = String(body.email || '').trim().slice(0, 200);
  const utm = String(body.utm || '').trim().slice(0, 300);
  const honeypot = String(body.website || '');

  if (!name) errors.push('name is required');
  if (!phoneDigits) errors.push('phone is invalid');
  if (!isPlausibleEmail(email)) errors.push('email is invalid');

  return { errors, clean: { name, phoneDigits, email, utm, honeypot } };
}

// ---------- Bitrix24 ----------
// ВАЖНО: если канал не настроен, бросаем ошибку, а не возвращаем null —
// иначе Promise.allSettled засчитывает такой вызов как "fulfilled" (успех),
// и оба канала могут молча отсутствовать, а ответ всё равно будет ok:true.
// Заявка в таком случае терялась бы без единого следа в логах.
async function createBitrixLead({ title, name, phoneDigits, email, comments, sourceDescription }) {
  if (!BITRIX_WEBHOOK_URL) throw new Error('bitrix_not_configured');

  const fields = {
    TITLE: title,
    NAME: name,
    PHONE: [{ VALUE: phoneDigits, VALUE_TYPE: 'WORK' }],
    ...(email ? { EMAIL: [{ VALUE: email, VALUE_TYPE: 'WORK' }] } : {}),
    COMMENTS: comments,
    SOURCE_ID: 'WEB',
    SOURCE_DESCRIPTION: sourceDescription
  };

  const url = BITRIX_WEBHOOK_URL.replace(/\/?$/, '/') + 'crm.lead.add.json';
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ fields })
  });

  const data = await res.json();
  if (!res.ok || data.error) {
    throw new Error('bitrix_error: ' + (data.error_description || data.error || res.status));
  }
  return data.result; // ID созданного лида
}

// ---------- Почта ----------
async function sendLeadEmail({ subject, text, replyTo }) {
  if (!mailTransport) throw new Error('email_not_configured');
  return mailTransport.sendMail({
    from: MAIL_FROM,
    to: MAIL_TO,
    replyTo: replyTo || undefined,
    subject,
    text
  });
}

// ---------- Роут 1: простая заявка (форма в блоке 9) ----------
app.post('/api/lead', async (req, res) => {
  const ip = req.headers['x-forwarded-for']?.split(',')[0]?.trim() || req.ip;
  if (isRateLimited(ip)) return res.status(429).json({ ok: false, error: 'rate_limited' });

  const { errors, clean } = validateContact(req.body || {});
  if (clean.honeypot) return res.status(200).json({ ok: true }); // похоже на бота — «успех», ничего не создаём

  if (errors.length) return res.status(400).json({ ok: false, error: 'validation_failed', details: errors });

  const comment = String(req.body.comment || '').trim().slice(0, 1000);
  const calcSummary = String(req.body.calcSummary || '').trim().slice(0, 500);

  const title = calcSummary
    ? `Заявка с лендинга (мерч): ${calcSummary.slice(0, 80)}`
    : 'Заявка с лендинга (мерч)';
  const commentsParts = [comment, calcSummary && `Расчёт: ${calcSummary}`, clean.utm && `UTM: ${clean.utm}`]
    .filter(Boolean).join('\n');

  const results = await Promise.allSettled([
    createBitrixLead({
      title, name: clean.name, phoneDigits: clean.phoneDigits, email: clean.email,
      comments: commentsParts, sourceDescription: 'Лендинг: мерч под Директ — форма'
    }),
    sendLeadEmail({
      subject: title,
      text: `Имя: ${clean.name}\nТелефон: +${clean.phoneDigits}\n${clean.email ? 'Email: ' + clean.email + '\n' : ''}${commentsParts}`,
      replyTo: clean.email
    })
  ]);

  logChannelFailures('lead', results);

  const anyOk = results.some((r) => r.status === 'fulfilled');
  if (!anyOk) return res.status(502).json({ ok: false, error: 'delivery_unavailable' });
  return res.status(200).json({ ok: true });
});

// ---------- Роут 2: квиз-расчёт (блок 6) — приоритет почты по требованию заказчика ----------
app.post('/api/quiz-lead', async (req, res) => {
  const ip = req.headers['x-forwarded-for']?.split(',')[0]?.trim() || req.ip;
  if (isRateLimited(ip)) return res.status(429).json({ ok: false, error: 'rate_limited' });

  const { errors, clean } = validateContact(req.body || {});
  if (clean.honeypot) return res.status(200).json({ ok: true });

  if (errors.length) return res.status(400).json({ ok: false, error: 'validation_failed', details: errors });

  const quiz = req.body.quiz || {};
  const summary = String(req.body.summary || '').trim().slice(0, 1000);

  // Собираем текст письма/CRM-комментария построчно и с ограничением длины
  // каждого поля — так лишние данные в JSON не смогут «раздуть» карточку.
  const quizLines = [
    quiz.group && `Категория: ${String(quiz.group).slice(0, 120)}`,
    quiz.item && `Товар: ${String(quiz.item).slice(0, 120)}`,
    quiz.method && `Способ нанесения: ${String(quiz.method).slice(0, 120)}`,
    quiz.qty && `Тираж: ${String(quiz.qty).slice(0, 20)} шт.`,
    quiz.layout && `Макет: ${String(quiz.layout).slice(0, 120)}`,
    quiz.deadline && `Срок: ${String(quiz.deadline).slice(0, 120)}`,
    quiz.notes && `Пожелания: ${String(quiz.notes).slice(0, 500)}`
  ].filter(Boolean).join('\n');

  const title = `Квиз-расчёт мерча: ${String(quiz.item || 'товар не указан').slice(0, 80)}`;
  const bodyText =
    `Имя: ${clean.name}\nТелефон: +${clean.phoneDigits}\n${clean.email ? 'Email: ' + clean.email + '\n' : ''}\n` +
    `${quizLines || summary}\n${clean.utm ? '\nUTM: ' + clean.utm : ''}`;

  const results = await Promise.allSettled([
    sendLeadEmail({ subject: title, text: bodyText, replyTo: clean.email }),
    createBitrixLead({
      title, name: clean.name, phoneDigits: clean.phoneDigits, email: clean.email,
      comments: bodyText, sourceDescription: 'Лендинг: мерч под Директ — квиз'
    })
  ]);

  logChannelFailures('quiz-lead', results);

  const anyOk = results.some((r) => r.status === 'fulfilled');
  if (!anyOk) return res.status(502).json({ ok: false, error: 'delivery_unavailable' });
  return res.status(200).json({ ok: true });
});

function logChannelFailures(routeName, settledResults) {
  settledResults.forEach((r, idx) => {
    if (r.status === 'rejected') {
      // Заявку не теряем молча — минимум логируем на сервере для ручной обработки.
      console.error(`[${routeName}] channel #${idx} failed:`, r.reason && r.reason.message);
    }
  });
}

app.get('/healthz', (_req, res) => res.status(200).send('ok'));

app.listen(PORT, () => {
  console.log(`Lead proxy listening on :${PORT} — Bitrix: ${BITRIX_WEBHOOK_URL ? 'on' : 'OFF'}, Email: ${isEmailConfigured ? 'on' : 'OFF'}`);
});
