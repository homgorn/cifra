<?php
/**
 * lead.php — приём заявок с лендингов Типографии «Цифра».
 *
 * ЗАЧЕМ ЭТОТ ФАЙЛ, А НЕ Node-СЕРВЕР
 *   Сайт заказчика на 1С-Битрикс, там PHP. Постоянный Node-процесс на
 *   таком хостинге не поднимется, это прямо называет риск №5 из
 *   landing-blueprint-2/reference/wordpress-spectra-astra-risks.md.
 *   Один файл на сервере сайта обслуживает все лендинги: ни npm install,
 *   ни второй сервер, ни CORS. Заявка уходит в Битрикс24, на почту и в
 *   инфоблок.
 *
 * ТРИ КАНАЛА, ДЕГРАДАЦИЯ ВМЕСТО ОТКАЗА
 *   1) Битрикс24, crm.lead.add, только при B24_ENABLED=1
 *   2) письмо через mail() на MAIL_TO
 *   3) запись в инфоблок 1С-Битрикс
 *   Если сработал хотя бы один канал, отвечаем 200. Если упали все три,
 *   отвечаем 502, а НЕ тихий ok: молчаливый успех при полной потере лида
 *   выглядит как рабочая форма, и заявка пропадает без следа.
 *
 * НАСТРОЙКА: копия рядом с этим файлом, lead.local.php, НЕ в git.
 *   Всё читается из $_ENV, который наполняется include'ом. Значения по
 *   умолчанию пустые: незаполненный канал честно падает и пишет в лог,
 *   вместо того чтобы молча уйти.
 *
 * ПРОВЕРЯТЬ НА ЖИВОЙ ИНСТАЛЛЯЦИИ, не рассуждением. Что обязательно
 * сделать после первого лида, см. reports/03_INSTRUCTIONS.md часть 3.
 */

declare(strict_types=1);

mb_internal_encoding('UTF-8');

/* ------------------------------------------------------------------ *
 * Конфигурация. Значения приходят из lead.local.php через $_ENV.
 * ------------------------------------------------------------------ */

$cfg = [
    'B24_ENABLED'    => getenv('B24_ENABLED') ?: '',
    'B24_HOST'       => getenv('B24_HOST') ?: '',
    'B24_WEBHOOK'    => getenv('B24_WEBHOOK') ?: '',
    'MAIL_TO'        => getenv('MAIL_TO') ?: '',
    'IBLOCK_ID'      => getenv('IBLOCK_ID') ?: '',
    'IBLOCK_FIELDS'  => getenv('IBLOCK_FIELDS') ?: '',   // "CODE_PROP=NAME,CODE_PROP2=NAME2"
    'RATE_DIR'       => getenv('RATE_DIR') ?: (sys_get_temp_dir() . '/lead-rate'),
    'LOG_FILE'       => getenv('LOG_FILE') ?: (sys_get_temp_dir() . '/lead.log'),
];
// Функции читают конфиг из $GLOBALS: они объявлены выше, чем настроен
// массив, и не принимают его параметром, иначе пришлось бы тащить $cfg
// через каждую из шести функций и легко где-то забыть.
$GLOBALS['__cfg'] = $cfg;

/* ---- Идентификация лендинга ----
   Читается из config.json рядом с обработчиком, а не зашивается.
   Первый вариант был константой 'Лендинг', и это оказалось неверно:
   обработчик обслуживает все лендинги одним файлом на весь домен, и в
   CRM у всех заявок было одинаковое TITLE и одинаковый
   SOURCE_DESCRIPTION. По такому лиду нельзя понять, с какой страницы он
   пришёл, то есть лиды с разных лендингов неразличимы, а это ровно то,
   ради чего идентификатор и нужен.

   Путь к конфигу задаётся переменной LEAD_CONFIG: обработчик может
   лежать рядом со страницами, а конфиг собирается отдельно. Если
   конфига нет, обработчик не падает: он пишет slug страницы, который
   приходит в поле page. */
$registryFile = getenv('LEAD_REGISTRY') ?: (__DIR__ . '/lead_registrations.json');
$registry = [];
if (is_file($registryFile)) {
    $rawRegistry = @file_get_contents($registryFile);
    if ($rawRegistry !== false) {
        $parsedRegistry = json_decode($rawRegistry, true);
        if (is_array($parsedRegistry)) {
            $registry = $parsedRegistry;
        }
    }
}

/* Подпись страницы по её slug.
 *
 * Почему реестр, а не один config.json рядом с обработчиком. Лендингов
 * стало одиннадцать, обработчик один на весь домен, и один файл может
 * назвать только один из них. Пока лендинг был один, этого хватало;
 * с одиннадцатью у всех заявок стало бы снова одинаковое TITLE и
 * одинаковый SOURCE_DESCRIPTION, то есть вернулась бы ровно та ошибка,
 * которую этот блок чинит. Реестр сопоставляет slug страницы её
 * названию, а slug приходит в поле page с самой страницы.
 *
 * Реестр собирает landings/build_all.py из config.json всех лендингов,
 * поэтому разойтись с ними он не может: он и есть их оглавление.
 *
 * Если реестра нет или в нём нет такой страницы, обработчик не падает.
 * Он пишет slug и добавляет в лог LEAD_UNKNOWN_PAGE, чтобы недостающая
 * запись была видна сразу, а не обнаружилась через месяц в отчёте, где
 * у всех лидов одно и то же название.
 *
 * Возвращает [подпись, найдено ли]. */
function resolve_landing(string $page, array $registry): array
{
    if (isset($registry[$page]) && is_string($registry[$page])) {
        $title = trim($registry[$page]);
        if ($title !== '') {
            return [$title, true];
        }
    }
    return ['Лендинг', false];
}

const RATE_LIMIT_WINDOW = 60;      // секунд
const RATE_LIMIT_MAX    = 5;       // попыток на канал и IP

/* ------------------------------------------------------------------ *
 * Логи и ответы
 * ------------------------------------------------------------------ */

/**
 * Пишет в лог одну строку. Отдельная функция, потому что забытый вызов
 * error_log означает потерю лида без объяснения, а это ровно тот класс
 * ошибок, ради которого файл и писался.
 */
function lg(string $message, array $context = []): void
{
    $line = sprintf(
        "[%s] %s%s\n",
        gmdate('Y-m-d H:i:s\Z'),
        $message,
        $context ? ' ' . json_encode($context, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) : ''
    );
    @file_put_contents($GLOBALS['__cfg']['LOG_FILE'], $line, FILE_APPEND | LOCK_EX);
    error_log(rtrim($line));
}

function respond(int $code, array $body): void
{
    http_response_code($code);
    header('Content-Type: application/json; charset=utf-8');
    header('X-Content-Type-Options: nosniff');
    echo json_encode($body, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

/* ------------------------------------------------------------------ *
 * Валидация
 * ------------------------------------------------------------------ */

/** Обрезает строку и убирает управляющие символы. */
function field($raw, int $max): string
{
    $s = is_scalar($raw) ? (string) $raw : '';
    $s = preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/u', '', $s) ?? '';
    $s = trim($s);
    if (function_exists('mb_substr')) {
        return mb_substr($s, 0, $max, 'UTF-8');
    }
    return substr($s, 0, $max);
}

function normalizePhone($raw): ?string
{
    $digits = preg_replace('/\D+/', '', (string) $raw) ?? '';
    // 10-12 цифр: 11 цифр это российский номер с восьмёркой или без,
    // 10 это формат без кода страны. Длиннее 12 значит мусор в поле.
    if (strlen($digits) < 10 || strlen($digits) > 12) {
        return null;
    }
    return $digits;
}

function isPlausibleEmail(string $email): bool
{
    if ($email === '') {
        return true; // email необязателен
    }
    if (strlen($email) > 200) {
        return false;
    }
    return (bool) filter_var($email, FILTER_VALIDATE_EMAIL);
}

/* ------------------------------------------------------------------ *
 * Rate limit по паре канал+IP
 * ------------------------------------------------------------------ */

/**
 * Счётчик ведётся по файлу, ключ содержит роут. Общий счётчик на оба
 * роута означал бы, что пять опечаток в простой форме блокируют отправку
 * квиза: посетитель не мог бы оформить заявку после ошибок в другой форме.
 */
function isRateLimited(string $ip, string $route): bool
{
    $dir = $GLOBALS['__cfg']['RATE_DIR'];
    if (!is_dir($dir) && !@mkdir($dir, 0770, true) && !is_dir($dir)) {
        // Без каталога лимитер не работает. Это не повод молчать:
        // записываем в лог и пропускаем запрос, иначе форма молча
        // перестанет защищаться, и никто об этом не узнает.
        lg('RATE_LIMIT_DIR_FAIL', ['dir' => $dir]);
        return false;
    }

    $key = $route . '_' . sha1($ip);
    $file = $dir . '/' . $key . '.json';
    $now = time();

    $fh = @fopen($file, 'c+');
    if ($fh === false) {
        lg('RATE_LIMIT_OPEN_FAIL', ['file' => $file]);
        return false;
    }
    if (!flock($fh, LOCK_EX)) {
        fclose($fh);
        lg('RATE_LIMIT_LOCK_FAIL', ['file' => $file]);
        return false;
    }

    $raw = stream_get_contents($fh) ?: '';
    $data = json_decode($raw, true);
    $hits = [];
    if (is_array($data)) {
        foreach ($data as $t) {
            if (is_int($t) && ($now - $t) < RATE_LIMIT_WINDOW) {
                $hits[] = $t;
            }
        }
    }
    $hits[] = $now;
    $limited = count($hits) > RATE_LIMIT_MAX;

    ftruncate($fh, 0);
    rewind($fh);
    fwrite($fh, (string) json_encode(array_values($hits)));
    fflush($fh);
    flock($fh, LOCK_UN);
    fclose($fh);

    return $limited;
}

/* ------------------------------------------------------------------ *
 * Каналы доставки
 * ------------------------------------------------------------------ */

/**
 * Битрикс24, crm.lead.add.
 *
 * Бросает исключение, если канал не настроен. Это не формальность:
 * если вернуть null, «успешность» будет засчитана, и при отказе всех
 * каналов ответ всё равно окажется 200.
 */
function createBitrixLead(array $lead): array
{
    if ($GLOBALS['__cfg']['B24_ENABLED'] !== '1') {
        throw new RuntimeException('b24_disabled');
    }
    $host = rtrim($GLOBALS['__cfg']['B24_HOST'], '/');
    $hook = $GLOBALS['__cfg']['B24_WEBHOOK'];
    if ($host === '' || $hook === '') {
        throw new RuntimeException('b24_not_configured');
    }

    $fields = [
        'TITLE'             => $lead['title'],
        'NAME'              => $lead['name'],
        'PHONE'             => [['VALUE' => $lead['phone'], 'VALUE_TYPE' => 'WORK']],
        'SOURCE_DESCRIPTION' => $lead['sourceDescription'],
    ];
    if ($lead['email'] !== '') {
        $fields['EMAIL'] = [['VALUE' => $lead['email'], 'VALUE_TYPE' => 'WORK']];
    }
    if ($lead['comments'] !== '') {
        $fields['COMMENTS'] = $lead['comments'];
    }
    // SOURCE_ID: значение WEB есть не в каждом портале, и несуществующее
    // значение молча игнорируется, поэтому оно настраивается, а не зашито.
    $sourceId = getenv('B24_SOURCE_ID') ?: 'WEB';
    $fields['SOURCE_ID'] = $sourceId;

    $url = $host . '/rest/1/' . $hook . '/crm.lead.add.json';
    $ch = curl_init($url);
    if ($ch === false) {
        throw new RuntimeException('b24_curl_init_failed');
    }
    curl_setopt_array($ch, [
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => json_encode(['fields' => $fields], JSON_UNESCAPED_UNICODE),
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 20,
        CURLOPT_CONNECTTIMEOUT => 8,
        CURLOPT_SSL_VERIFYPEER => true,
        CURLOPT_SSL_VERIFYHOST => 2,
        CURLOPT_HTTPHEADER     => ['Content-Type: application/json'],
    ]);
    $body = curl_exec($ch);
    $errno = curl_errno($ch);
    $error = curl_error($ch);
    $status = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($errno !== 0) {
        // Самоподписанный сертификат на коробке это известная ситуация.
        // Сообщение в лог должно называть её прямо, иначе диагностика
        // уйдёт по ложному следу.
        throw new RuntimeException('b24_transport: ' . $error . ' (код ' . $errno . ')');
    }
    $data = json_decode((string) $body, true);
    if ($status !== 200 || !is_array($data)) {
        $desc = is_array($data) ? ($data['error_description'] ?? $data['error'] ?? 'нет ответа') : 'ответ не JSON';
        throw new RuntimeException('b24_http_' . $status . ': ' . $desc);
    }
    if (isset($data['error'])) {
        throw new RuntimeException('b24_error: ' . ($data['error_description'] ?? $data['error']));
    }

    return [
        'id'     => $data['result'] ?? null,
        'fields' => array_keys($fields),
    ];
}

/** Письмо менеджеру. */
function sendLeadEmail(string $subject, string $text, string $replyTo): bool
{
    $to = $GLOBALS['__cfg']['MAIL_TO'];
    if ($to === '') {
        throw new RuntimeException('mail_not_configured');
    }
    if (!function_exists('mail')) {
        throw new RuntimeException('mail_function_missing');
    }
    $from = getenv('MAIL_FROM') ?: ('no-reply@' . preg_replace('/^www\./i', '', $_SERVER['HTTP_HOST'] ?? 'localhost'));
    $headers = 'From: ' . $from . "\r\n"
        . 'Content-Type: text/plain; charset=UTF-8' . "\r\n"
        . 'Content-Transfer-Encoding: 8bit' . "\r\n";
    if ($replyTo !== '' && isPlausibleEmail($replyTo)) {
        $headers .= 'Reply-To: ' . $replyTo . "\r\n";
    }
    $ok = @mail($to, '=?UTF-8?B?' . base64_encode($subject) . '?=', $text, $headers);
    if (!$ok) {
        throw new RuntimeException('mail_returned_false');
    }
    return true;
}

/** Запись в инфоблок 1С-Битрикс. */
function saveToInfoblock(array $lead): bool
{
    $iblockId = $GLOBALS['__cfg']['IBLOCK_ID'];
    if ($iblockId === '' || !defined('BX_ORIGIN')) {
        throw new RuntimeException('iblock_not_configured');
    }
    $fields = [
        'NAME'              => $lead['title'],
        'PREVIEW_TEXT'      => $lead['comments'],
        'CODE'              => 'lead-' . date('Ymd-His') . '-' . substr(sha1($lead['phone']), 0, 6),
        'DETAIL_TEXT'       => $lead['comments'],
        'IBLOCK_ID'         => $iblockId,
        'PROPERTY_VALUE'    => [],
    ];
    if ($lead['email'] !== '') {
        $fields['EMAIL'] = $lead['email'];
    }
    // Пользовательские свойства. Коды берутся из настройки, потому что
    // у каждого инфоблока свои, и зашитый код молча ушёл бы в никуда.
    $propMap = [];
    if ($GLOBALS['__cfg']['IBLOCK_FIELDS'] !== '') {
        foreach (explode(',', $GLOBALS['__cfg']['IBLOCK_FIELDS']) as $pair) {
            $bits = explode('=', $pair, 2);
            if (count($bits) === 2) {
                $propMap[trim($bits[0])] = trim($bits[1]);
            }
        }
    }
    foreach ($propMap as $propCode => $leadKey) {
        $value = $lead[$leadKey] ?? '';
        if ($value !== '') {
            $fields['PROPERTY_VALUE'][$propCode] = $value;
        }
    }

    $element = new \CIBlockElement();
    if (!$element->Add($fields)) {
        $err = $element->GetLastError();
        throw new RuntimeException('iblock_add_failed: ' . (is_array($err) ? implode('; ', $err) : 'без текста'));
    }
    return (bool) $element->GetID();
}

/* ------------------------------------------------------------------ *
 * Разбор запроса
 * ------------------------------------------------------------------ */

$rawBody = file_get_contents('php://input');
$in = json_decode((string) $rawBody, true);
if (!is_array($in)) {
    // Форма может прийти и как form-data, если кто-то отключит JS.
    $in = $_POST;
}
if (!is_array($in) || $in === []) {
    lg('BAD_JSON');
    respond(400, ['ok' => false, 'error' => 'bad_request']);
}

/* Роут. ВАЖНО: определение по имени файла здесь ломало квиз.
   Обработчик один на все лендинги и лежит по адресу /lead.php, поэтому
   basename() для квиза и для простой формы давал одно и то же имя, квиз
   уходил в ветку простой заявки, а лимит делился между ними.

   Теперь тип заявки определяется по телу запроса, поле quiz присутствует
   только у квиза. Дополнительно принимается ?type=quiz, если front-end
   когда-нибудь будет звать разными адресами. Порядок: сначала тело,
   потому что клиентский JS не передаёт query. */
$isQuiz = is_array($in['quiz'] ?? null);
$typeParam = strtolower((string) ($_GET['type'] ?? ''));
if ($typeParam === 'quiz' || $typeParam === 'lead') {
    $isQuiz = ($typeParam === 'quiz');
}
$route = $isQuiz ? 'quiz-lead' : 'lead';

$ip = $_SERVER['REMOTE_ADDR'] ?? '0.0.0.0';
$forwarded = $_SERVER['HTTP_X_FORWARDED_FOR'] ?? '';
if ($forwarded !== '') {
    $first = trim(explode(',', $forwarded)[0]);
    if (filter_var($first, FILTER_VALIDATE_IP)) {
        $ip = $first;
    }
}

/* ---- honeypot до всего остального ----
   Поле называется website, потому что так его шлёт script.js. Раньше в
   спецификации было honeypot, и это расхождение тихо ломало бы защиту:
   бот заполнил бы не то поле, проверка прошла бы, лид создался. */
$honeypot = field($in['website'] ?? $in['honeypot'] ?? '', 200);
if ($honeypot !== '') {
    lg('HONEYPOT', ['ip' => $ip, 'route' => $route]);
    // Успех без создания лида: бот не должен понимать, что его поймали.
    respond(200, ['ok' => true]);
}

/* ---- rate limit по каналу. Тип заявки уже определён выше по телу ---- */
if (isRateLimited($ip, $route)) {
    lg('RATE_LIMITED', ['ip' => $ip, 'route' => $route]);
    respond(429, ['ok' => false, 'error' => 'rate_limited']);
}

/* ---- валидация ---- */
$name  = field($in['name'] ?? '', 120);
$phone = normalizePhone($in['phone'] ?? '');
$email = field($in['email'] ?? '', 200);

$errors = [];
if ($name === '') {
    $errors[] = 'name is required';
}
if ($phone === null) {
    $errors[] = 'phone is invalid';
}
if (!isPlausibleEmail($email)) {
    $errors[] = 'email is invalid';
}
if ($errors) {
    lg('VALIDATION_FAILED', ['ip' => $ip, 'route' => $route, 'errors' => $errors]);
    respond(400, ['ok' => false, 'error' => 'validation_failed', 'details' => $errors]);
}

/* ---- содержимое заявки ---- */
$utm      = field($in['utm'] ?? '', 300);
$page      = field($in['page'] ?? '', 120);
[$landingTitle, $landingKnown] = resolve_landing($page, $registry);
if (!$landingKnown) {
    // Страница в реестре не найдена. Это не ошибка обработки заявки,
    // но её надо видеть: значит, на сервер положили не тот реестр или
    // добавили лендинг и не пересобрали.
    lg('LEAD_UNKNOWN_PAGE', ['page' => $page]);
}
$comment  = field($in['comment'] ?? '', 1000);
$summary  = field($in['summary'] ?? field($in['calcSummary'] ?? '', 500), 1000);

$quizLines = [];
$quiz = is_array($in['quiz'] ?? null) ? $in['quiz'] : [];
$map = [
    'group'    => 'Категория',
    'item'     => 'Товар',
    'method'   => 'Способ нанесения',
    'qty'      => 'Тираж',
    'layout'   => 'Макет',
    'deadline' => 'Срок',
    // Доставка отдельной строкой: по ней видно, из какого города заявка,
    // и она же объясняет менеджеру, считать ли доставку СДЭК в расчёте.
    'delivery' => 'Доставка',
    'notes'    => 'Пожелания',
];
foreach ($map as $key => $label) {
    $v = field($quiz[$key] ?? '', 500);
    if ($v !== '') {
        $quizLines[] = $label . ': ' . $v;
    }
}

$parts = array_filter([
    $comment !== '' ? $comment : null,
    $summary !== '' ? 'Расчёт: ' . $summary : null,
    $quizLines ? implode("\n", $quizLines) : null,
    'Источник: ' . $landingTitle . ' (' . $page . ')',
    $utm !== '' ? 'UTM: ' . $utm : null,
], static fn($v) => $v !== null);
$comments = implode("\n", $parts);

$title = $isQuiz
    ? 'Расчёт: ' . $landingTitle . ', ' . field($quiz['item'] ?? 'товар не указан', 80)
    : 'Заявка: ' . $landingTitle;

$lead = [
    'title'            => $title,
    'name'             => $name,
    'phone'            => $phone,
    'email'            => $email,
    'comments'         => $comments,
    'sourceDescription' => $landingTitle . ' — ' . $page,
    // Ключи для пользовательских свойств инфоблока.
    'utm'              => $utm,
    'page'             => $page,
    'comment'          => $comment,
];

$bodyText = "Имя: {$name}\nТелефон: +{$phone}\n"
    . ($email !== '' ? "Email: {$email}\n" : '')
    . "\n{$comments}\n";

/* ---- доставка: все три канала, деградация вместо отказа ---- */
$results = [];
$channels = ['bitrix24', 'email', 'infoblock'];

try {
    $results['bitrix24'] = createBitrixLead($lead);
} catch (Throwable $e) {
    $results['bitrix24'] = new RuntimeException($e->getMessage());
    lg('CHANNEL_FAIL bitrix24', ['route' => $route, 'error' => $e->getMessage()]);
}

try {
    $results['email'] = sendLeadEmail($title, $bodyText, $email);
} catch (Throwable $e) {
    $results['email'] = new RuntimeException($e->getMessage());
    lg('CHANNEL_FAIL email', ['route' => $route, 'error' => $e->getMessage()]);
}

try {
    $results['infoblock'] = saveToInfoblock($lead);
} catch (Throwable $e) {
    $results['infoblock'] = new RuntimeException($e->getMessage());
    lg('CHANNEL_FAIL infoblock', ['route' => $route, 'error' => $e->getMessage()]);
}

$ok = [];
foreach ($channels as $ch) {
    if (!($results[$ch] instanceof Throwable)) {
        $ok[] = $ch;
    }
}

lg('LEAD', [
    'route'    => $route,
    'ip'       => $ip,
    'page'     => $page,
    'channels' => $ok,
    'failed'   => array_values(array_filter($channels, static fn($c) => !in_array($c, $ok, true))),
]);

/* Отладочная накладка на время установки. Комментируется целиком перед
   сдачей. Причина: обработчик в fatal-ошибке отдаёт клиенту HTML с
   текстом ошибки и кодом 200, и это выглядит как «форма отработала».
   Фаталы должны попадать в лог, а не в ответ посетителю. */
if (getenv('LEAD_DEBUG') === '1') {
    ini_set('display_errors', '1');
    error_reporting(E_ALL);
} else {
    ini_set('display_errors', '0');
    error_reporting(E_ALL & ~E_DEPRECATED);
}

if ($ok === []) {
    // Честный отказ. Тихий ok здесь означал бы потерю заявки, которая
    // выглядела бы как успешно отправленная.
    respond(502, ['ok' => false, 'error' => 'delivery_unavailable']);
}

respond(200, ['ok' => true]);
