<?php
/**
 * Тестовый стенд для lead.php. Запуск: php _harness.php
 *
 * Что делает: поднимает встроенный веб-сервер PHP и бьёт в него
 * настоящими HTTP-запросами, как это делает браузер. Проверка через
 * php -l ловит только синтаксис и не говорит ничего о том, вернёт ли
 * обработчик 200 при живом лиде и 502 при обрыве каналов.
 *
 * Проверяет:
 *   1. honeypot отвечает 200 и НЕ создаёт лид
 *   2. пустое имя и короткий телефон дают 400
 *   3. кривой email даёт 400
 *   4. нормальная заявка при обрыве всех каналов даёт честный 502
 *   5. rate limit: после 5 попыток приходит 429, и квиз не блокируется
 *   6. квиз-маршрут отвечает независимо от простой формы
 */

declare(strict_types=1);

mb_internal_encoding('UTF-8');

$port = (int) ($argv[1] ?? 8321);
$docRoot = __DIR__;

/* Стенд имитирует окружение сервера. Ключевое: B24_ENABLED=0 и пустой
   MAIL_TO, то есть НИ ОДИН канал доставки не настроен. Именно в такой
   конфигурации обработчик обязан отдать 502, а не тихий ok. */
$env = [
    'B24_ENABLED'  => '0',
    'B24_HOST'     => '',
    'B24_WEBHOOK'  => '',
    'MAIL_TO'      => '',
    'IBLOCK_ID'    => '',
    'RATE_DIR'     => sys_get_temp_dir() . '/lead-rate-harness',
    'LOG_FILE'     => sys_get_temp_dir() . '/lead-harness.log',
];
/* Переменные окружения передаются массивом $env в proc_open, а НЕ через
   собственный php.ini. Первый вариант был неверным: свой ini заменял
   основной целиком, терялись extension_dir и подключённые расширения, и
   обработчик падал на mb_internal_encoding() ещё до чтения запроса.

   Массив $env в proc_open ЗАМЕНЯЕТ окружение целиком, а не дополняет его.
   Без SystemRoot и PATH дочерний PHP не мог поднять сокет и писал
   «Failed to listen», то есть стенд падал не из-за обработчика. Поэтому
   окружение дочернего процесса собирается из текущего и дополняется
   нужными ключами. */
/* Переменные окружения собираются из текущего и дополняются нужными.
   Массив $env в proc_open ЗАМЕНЯЕТ окружение целиком, а не дополняет его,
   и без SystemRoot дочерний PHP не мог поднять сокет. */
$childEnv = [];
foreach (getenv() as $k => $v) {
    $childEnv[$k] = (string) $v;
}
foreach ($env as $k => $v) {
    $childEnv[$k] = $v;
}
// Встроенный сервер PHP держит соединение и после десятка запросов подряд
// начинает обрывать его без ответа. На фоне этого обрыва проверить rate
// limit невозможно: неизвестно, что придёт в ответ. Поэтому сервер
// перезапускается между фазами, и каждая фаза получает свежее соединение.
$childEnv['PHP_CLI_SERVER_WORKERS'] = '4';

/** Поднимает сервер и ждёт готовности. Возвращает ресурс процесса. */
function startServer(array $childEnv, int $port, string $docRoot)
{
    $descriptors = [0 => ['pipe', 'r'], 1 => ['pipe', 'w'], 2 => ['pipe', 'w']];
    $server = proc_open(
        [PHP_BINARY, '-S', "127.0.0.1:$port", '-t', $docRoot],
        $descriptors, $pipes, $docRoot, $childEnv);
    if (!is_resource($server)) {
        fwrite(STDERR, "Не удалось поднять сервер на порту $port\n");
        exit(1);
    }
    stream_set_blocking($pipes[1], false);
    stream_set_blocking($pipes[2], false);
    return [$server, $pipes];
}

function stopServer($server, array $pipes): void
{
    if (is_resource($server)) {
        proc_terminate($server);
        proc_close($server);
    }
    foreach ($pipes as $p) {
        if (is_resource($p)) {
            fclose($p);
        }
    }
}

function waitForServer(string $base, int $port): bool
{
    for ($i = 0; $i < 60; $i++) {
        $ctx = stream_context_create(['http' => ['timeout' => 1, 'ignore_errors' => true]]);
        $body = @file_get_contents($base, false, $ctx);
        if ($body !== false) {
            return true;
        }
        usleep(200000);
    }
    return false;
}

/** Шлёт POST и возвращает [код, тело]. */
function post(string $url, array $payload): array
{
    $json = json_encode($payload, JSON_UNESCAPED_UNICODE);
    // Пауза и явный Connection: close. Встроенный сервер держит соединение
    // открытым, и после десятка запросов подряд поток начинает обрываться
    // без ответа: ошибка соединения, а не ошибка обработчика. Разрывать
    // соединение самому и ждать между запросами — единственный способ
    // получить стабильный стенд на этом сервере.
    usleep(150000);
    $ctx = stream_context_create(['http' => [
        'method'        => 'POST',
        'header'        => "Content-Type: application/json\r\nConnection: close\r\n",
        'content'       => $json,
        'timeout'       => 25,
        'ignore_errors' => true,
    ]]);
    $body = @file_get_contents($url, false, $ctx);
    $status = 0;
    foreach ($http_response_header ?? [] as $h) {
        if (preg_match('#^HTTP/\S+\s+(\d{3})#', $h, $m)) {
            $status = (int) $m[1];
        }
    }
    return [$status, (string) $body];
}

$pass = 0;
$fail = 0;

function check(string $name, bool $ok, string $detail = ''): void
{
    global $pass, $fail;
    if ($ok) {
        $pass++;
        echo "  OK   $name" . ($detail !== '' ? "  ($detail)" : '') . PHP_EOL;
    } else {
        $fail++;
        echo "  FAIL $name" . ($detail !== '' ? "  ($detail)" : '') . PHP_EOL;
    }
}

// Старые счётчики rate limit, чтобы тест был независим от прошлых прогонов.
foreach (glob($env['RATE_DIR'] . '/*.json') ?: [] as $f) {
    @unlink($f);
}
@mkdir($env['RATE_DIR'], 0770, true);

$base = "http://127.0.0.1:$port/lead.php";
[$server, $pipes] = startServer($childEnv, $port, $docRoot);

if (!waitForServer($base, $port)) {
    echo "Сервер не поднялся на порту $port" . PHP_EOL;
    stopServer($server, $pipes);
    exit(1);
}

echo "Тест lead.php, все каналы доставки недоступны" . PHP_EOL;
echo str_repeat('-', 60) . PHP_EOL;

[$code, $body] = post($base, [
    'name' => 'Бот', 'phone' => '+79990000000', 'website' => 'http://spam.example',
]);
check('honeypot отвечает 200', $code === 200, "код $code");
check('honeypot не выдаёт ошибку доставки', str_contains($body, '"ok":true'), $body);

// Снимаем honeypot из счётчика: он не должен расходовать лимит.
$lp = glob($env['RATE_DIR'] . '/lead_*.json') ?: [];
foreach ($lp as $f) {
    $d = json_decode((string) file_get_contents($f), true);
    if (is_array($d) && count($d) > 1) {
        file_put_contents($f, json_encode(array_slice($d, -1)));
    }
}

[$code, $body] = post($base, ['name' => '', 'phone' => '123']);
check('пустое имя и короткий телефон дают 400', $code === 400, "код $code");
check('400 называет обе ошибки',
    str_contains($body, 'name is required') && str_contains($body, 'phone is invalid'), $body);

[$code, $body] = post($base, ['name' => 'Иван', 'phone' => '+79658423241', 'email' => 'не-почта']);
check('кривой email даёт 400', $code === 400, "код $code");

[$code, $body] = post($base, [
    'name' => 'Пётр', 'phone' => '+79658423241', 'comment' => 'Нужен календарь на 2027',
]);
check('все каналы недоступны дают честный 502', $code === 502, "код $code");
check('502 не выдаёт ok', !str_contains($body, '"ok":true'), $body);
check('502 называет причину', str_contains($body, 'delivery_unavailable'), $body);

/* Фаза вторая: rate limit и независимость каналов.
   Сервер перезапускается, потому что встроенный сервер набирает счётчик
   соединений и обрывает поток без ответа. К проверке лимита это отношения
   не имеет: замер идёт по HTTP-кодам, а не по состоянию соединения. */
stopServer($server, $pipes);
$port++;
$base = "http://127.0.0.1:$port/lead.php";
foreach (glob($env['RATE_DIR'] . '/*.json') ?: [] as $f) {
    @unlink($f);
}
[$server, $pipes] = startServer($childEnv, $port, $docRoot);
if (!waitForServer($base, $port)) {
    echo "Сервер не поднялся на порту $port" . PHP_EOL;
    stopServer($server, $pipes);
    exit(1);
}

// Счётчик формы выжигается, но квиз живёт отдельно.
for ($i = 0; $i < 6; $i++) {
    post($base, ['name' => '', 'phone' => '1']);
}
[$code] = post($base, ['name' => '', 'phone' => '1']);
check('rate limit формы срабатывает, код 429', $code === 429, "код $code");

[$code, $body] = post($base, [
    'name' => 'Анна', 'phone' => '+79658423241',
    'quiz' => ['group' => 'Квартальные', 'item' => 'Стандарт 2027', 'qty' => 100],
    'summary' => 'Категория: Квартальные',
]);
if ($code === 0) {
    // Код 0 означает, что HTTP-ответа не было вообще: соединение оборвалось
    // или истекло. Сама причина нужна в выводе, иначе стенд просто скажет
    // «провалено» и не скажет почему. Последняя ошибка PHP и есть причина.
    $err = error_get_last();
    echo '  (ответа не было: ' . json_encode($err, JSON_UNESCAPED_UNICODE) . ')' . PHP_EOL;
}
check('квиз не заблокирован промахами формы', $code === 502, "код $code");
check('квиз-маршрут опознан', $code === 502 && !str_contains($body, 'rate_limited'), $body);

/* Фаза третья: опознание страницы по реестру.
   Обработчик один на домен и обслуживает одиннадцать лендингов, поэтому
   подпись лида берётся из реестра по slug из поля page. Раньше проверок
   этого не было, и реестр можно было положить на сервер сломанным или не
   положить вовсе: обработчик не падал, заявки принимались, а в CRM у всех
   было одинаковое название. Отсюда и проверка. */
echo PHP_EOL . 'Фаза третья: опознание страницы по реестру' . PHP_EOL;

/* Сервер перезапускается по той же причине, что и во второй фазе:
   встроенный сервер набирает счётчик соединений и обрывает поток без
   ответа. Ниже идут ещё два запроса, и без перезапуска второй из них
   вернёт код 0, то есть никакого ответа, и проверка «заявка принята»
   провалится из-за инструмента, а не из-за обработчика. */
stopServer($server, $pipes);
$port++;
$base = "http://127.0.0.1:$port/lead.php";
foreach (glob($env['RATE_DIR'] . '/*.json') ?: [] as $f) {
    @unlink($f);
}
[$server, $pipes] = startServer($childEnv, $port, $docRoot);
if (!waitForServer($base, $port)) {
    echo "Сервер не поднялся на порту $port" . PHP_EOL;
    stopServer($server, $pipes);
    exit(1);
}

// Лимит формы выжегли шесть заведомо пустых заявок выше. Без сброса
// обе проверки ниже уедут в 429, и отметка об неизвестной странице
// «сработает» на пустом месте: её напишет чужая, более ранняя заявка.
foreach (glob($env['RATE_DIR'] . '/*.json') ?: [] as $f) {
    @unlink($f);
}

$registryFile = $docRoot . '/lead_registrations.json';
check('реестр заявок на месте', is_file($registryFile), $registryFile);
$registry = is_file($registryFile)
    ? json_decode((string) @file_get_contents($registryFile), true)
    : [];
check('реестр читается', is_array($registry) && count($registry) > 0,
    'страниц: ' . (is_array($registry) ? count($registry) : 0));

/* Ищет в логе отметку о неизвестной странице с конкретным slug.
   Искать просто подстроку `"page":"slug"` нельзя: такая же строка есть в
   обычной записи LEAD, то есть проверка «не должно быть такой подстроки»
   никогда не прошла бы. */
$unknownMarked = function (string $slug) use ($env): bool {
    $log = (string) @file_get_contents($env['LOG_FILE']);
    foreach (preg_split('/\R/', $log) ?: [] as $line) {
        if (str_contains($line, 'LEAD_UNKNOWN_PAGE')
            && str_contains($line, '"page":"' . $slug . '"')) {
            return true;
        }
    }
    return false;
};

// Страница из реестра: заявка принимается, и в лог не попадает отметка
// о неизвестной странице.
$knownSlug = (string) array_key_first((array) $registry);
[$code] = post($base, ['name' => 'Гость', 'phone' => '+79658423241',
                       'page' => $knownSlug,
                       'comment' => 'Проверка подписи страницы']);
check('заявка со страницы из реестра принята', $code === 502, "код $code");
check('страница из реестра не отмечена как неизвестная',
    !$unknownMarked($knownSlug),
    $unknownMarked($knownSlug) ? 'отметка есть, а не должна' : 'отметки нет');

// Страница вне реестра: заявка всё равно принимается, но попадает в лог
// как неизвестная. Иначе потерянный или старый реестр обнаружится через
// месяц, когда в отчёте у всех лидов будет одно и то же название.
$badSlug = 'nesushchestvuyushchiy-landing';
[$code] = post($base, ['name' => 'Гость2', 'phone' => '+79658423241',
                       'page' => $badSlug,
                       'comment' => 'Проверка неизвестной страницы']);
check('заявка с неизвестной страницы принята', $code === 502, "код $code");
check('неизвестная страница отмечена в логе', $unknownMarked($badSlug),
    $unknownMarked($badSlug) ? 'отметка есть' : 'отметки нет');

echo str_repeat('-', 60) . PHP_EOL;
echo "Пройдено $pass, провалено $fail" . PHP_EOL;

echo PHP_EOL . "Лог обработчика, последние строки:" . PHP_EOL;
$log = $env['LOG_FILE'];
if (is_file($log)) {
    $lines = file($log, FILE_IGNORE_NEW_LINES) ?: [];
    foreach (array_slice($lines, -12) as $l) {
        echo "  $l" . PHP_EOL;
    }
} else {
    echo "  лог не создан" . PHP_EOL;
}

stopServer($server, $pipes);
exit($fail === 0 ? 0 : 1);
