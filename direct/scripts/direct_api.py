#!/usr/bin/env python3
"""Клиент API Яндекс Директа версии 5.

Зачем отдельный файл. АПИ Директа устроен иначе, чем Вебмастер и Метрика.
Те запрашиваются GET-ом по адресу ресурса и отдают JSON. Здесь всё
идёт POST-ом на один адрес, тело запроса и ответа это JSON, а часть
методов возвращает не JSON, а TSV во вложении.

Три вещи, которые ломают молча, и поэтому здесь сделаны явно.

Баллы. Сервер считает баллы за каждый вызов, включая упавшие с ошибкой,
и при их нехватке отдаёт 152 вместо данных. Ответ содержит заголовок
Units вида «израсходовано / остаток / суточный лимит», который
обязателен к чтению. Без него запросы будут падать в 152 без всякого
предупреждения, и причина будет непонятна. Остаток проверяется до
запроса, и при нехватке работа останавливается до того, как потратит
остаток впустую.

Офлайн-отчёты. Отчёт по поисковым запросам формируется только в
офлайн-режиме, это не сбой, а устройство сервиса: сервер отвечает 201 и
кладёт отчёт в очередь, а данные приходят позже отдельным запросом.
Сервер сам говорит, через сколько приходить, в заголовке retryIn.
Клиент опрашивает до готовности, а не сдаётся на первом 201.

Деньги. По умолчанию суммы приходят в микроединицах, целое число,
умноженное на миллион. Число 1 450 000 читается как 1450000 и очень
легко попадает в отчёт как есть. Заголовок returnMoneyInMicros со
значением false заставляет сервер отдавать рубли.

Песочница. Отдельный адрес и отдельный токен, включается переменной
DIRECT_SANDBOX=1. Ошибка песочницы и ошибка боевого контура выглядят
одинаково, и путать их дорого: можно час править рабочее приложение,
которое на самом деле работает с тестовыми данными.

Из модуля импортируются:
    DirectClient(token=..., sandbox=False)
    .call(service, method, body)      -> dict
    .report(definition)              -> str, тело TSV
    .units                          -> (spent, remaining, daily)
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_PATH = os.path.join(ROOT, ".env")

PROD = "https://api.direct.yandex.com"
SANDBOX = "https://sandbox.direct.yandex.com"
REPORTS_PROD = "https://api.direct.yandex.com/json/v501/reports"
REPORTS_SANDBOX = "https://sandbox.direct.yandex.com/json/v501/reports"

# Сервисы делятся по цене вызова, и это влияет на то, что имеет смысл
# опрашивать часто. Значения взяты из раздела «Ограничения, баллы».
# Ключ это метод, значение это баллы за вызов и за объект.
UNITS_PER_CALL = {
    "Campaigns.get": (10, 1), "Campaigns.update": (10, 3),
    "AdGroups.get": (15, 1),
    "Ads.get": (15, 1), "Ads.update": (20, 20), "Ads.moderate": (15, 0),
    "Keywords.get": (15, 0), "Keywords.update": (20, 2), "Keywords.add": (20, 2),
    "Bids.get": (15, 0), "Bids.set": (25, 0),
    "KeywordBids.get": (15, 0), "KeywordBids.set": (25, 0),
    "Clients.get": (10, 0),
    "Dictionaries.get": (1, 0),
    "RetargetingLists.get": (1, 1),
    "Leads.get": (1, 1),
    "KeywordsResearch.hasSearchVolume": (1, 0),
    "KeywordsResearch.deduplicate": (10, 0),
    "Changes.check": (10, 0), "Changes.checkCampaigns": (10, 0),
}

# Методы, которые меняют деньги или состояние. Клиент по умолчанию их
# не выполняет, даже если они переданы, потому что отчёт ошибается в
# одном предложении, а отменить уже показанные объявления можно не
# сразу. Для работы с ними нужен явный вызов write=True.
WRITE_METHODS = frozenset(
    name for name in UNITS_PER_CALL
    if any(p in name for p in (".add", ".update", ".set", ".delete",
                               ".suspend", ".resume", ".archive", ".moderate"))
)

# Коды, которые означают не ошибку запроса, а состояние доступа.
MEANING = {
    "1": "неизвестная ошибка, попробовать позже",
    "10": "нет доступа к каталогу регионов, нужен другой токен",
    "34": "нет доступа к аккаунту. Проверить заявку на доступ, условия "
          "соглашения на direct.yandex.ru и то, что токен выдан от "
          "нужного аккаунта",
    "58": "заявка на доступ к API не подана или не одобрена. Добавление "
          "права в приложении на oauth.yandex.ru этого не заменяет. "
          "Заявка подаётся на direct.yandex.ru, вкладка «Мои заявки»",
    "60": "объект не найден",
    "61": "объект в статусе удаления",
    "101": "не хватает баллов, пополнить или подождать",
    "152": "не хватает баллов, суточный лимит исчерпан",
    "214": "операцию сейчас выполнить нельзя, объект на модерации",
    "8000": "сервер не понял запрос. Если при этом текст «OAuth token is "
           "missing», дело не в токене, а в том, что запрос ушёл со схемой "
           "OAuth вместо Bearer: клиент отправляет Bearer",
    "1002": "токен неверен или отозван, получить новый",
    "1003": "логин клиента не найден",
    "2001": "кампания не найдена",
    "3006": "доступ к клиенту запрещён",
    "5004": "нет прав на операцию с этим объектом",
}


def _decode(text):
    """Тело ответа: JSON, если это JSON, иначе разбор SOAP-ошибки.

    Директ отвечает XML-конвертом с faults даже на JSON-эндпоинт, и
    отдаёт его с кодом 200. Поэтому успешный HTTP-ответ не означает
    успешный вызов, и json.loads на таком теле падает. Разбор ошибки
    вынесен в общий разбор, чтобы и HTTP-ошибки, и 200 с faults
    читались одинаково.
    """
    stripped = text.lstrip()
    if stripped.startswith("<"):
        raise _fault(stripped)
    return json.loads(text)


def _fault(xml):
    code = _tag(xml, "errorCode")
    detail = _tag(xml, "errorDetail") or _tag(xml, "faultstring") or ""
    return DirectError(200, code, detail, _tag(xml, "requestId"))


def _split_error(raw):
    """Достаёт код и текст из тела ошибки, JSON или XML."""
    s = raw.lstrip()
    if s.startswith("<"):
        return _tag(raw, "errorCode"), _tag(raw, "errorDetail")
    try:
        d = json.loads(raw)
    except json.JSONDecodeError:
        return "", raw[:300]
    return d.get("error") or d.get("errorCode") or "", (
        d.get("error-message") or d.get("message") or "")


def load_env():
    env = {}
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    return env


class DirectError(Exception):
    """Ошибка Директа с разобранным кодом."""

    def __init__(self, http, code, message, request_id=""):
        self.http = http
        self.code = code
        self.message = message
        self.request_id = request_id
        self.hint = MEANING.get(str(code), "")
        super().__init__("Директ вернул %s: %s%s"
                         % (code or http, message,
                            "" if not self.hint else " (%s)" % self.hint))


class DirectClient:
    def __init__(self, token=None, sandbox=False, min_units=500, log=None,
                 write=None):
        env = load_env()
        self.token = token if token is not None else (
            env.get("DIRECT_OAUTH_TOKEN") or env.get("YANDEX_OAUTH_TOKEN") or "")
        if sandbox is False and str(env.get("DIRECT_SANDBOX", "")).strip() in ("1", "true", "yes"):
            sandbox = True
        self.sandbox = bool(sandbox)
        self.base = SANDBOX if self.sandbox else PROD
        self.reports_url = REPORTS_SANDBOX if self.sandbox else REPORTS_PROD
        self.min_units = min_units
        self.log = log or (lambda *a: None)
        # Режим записи. По умолчанию выключен, и это не ограничение API,
        # а защита от ошибки в собственном коде: выгрузка не должна
        # иметь возможности остановить чужую кампанию. Включается
        # переменной DIRECT_WRITE=1 в .env, когда представителю в
        # Директе выданы права на редактирование.
        #
        # Про права представителя. Роль «Только чтение» даёт всё, что
        # нужно для аудита, аналитики и общей таблицы: выгрузка кампаний,
        # фраз и все четыре отчёта это операции чтения, и роль на них не
        # влияет. Полный доступ нужен только для правки ставок, паузы и
        # изменения текстов объявлений.
        if write is None:
            write = str(env.get("DIRECT_WRITE", "")).strip() in ("1", "true", "yes")
        self.write = bool(write)
        self.spent = 0
        self.remaining = None
        self.daily = None
        self.calls = 0
        if not self.token:
            raise DirectError(0, "no_token", "нет токена в .env: DIRECT_OAUTH_TOKEN")

    # ---------- низкий уровень ----------

    def _read_units(self, headers):
        raw = headers.get("Units") or headers.get("units")
        if not raw:
            return
        parts = raw.split("/")
        try:
            self.spent = int(parts[0])
            self.remaining = int(parts[1])
            self.daily = int(parts[2])
        except (ValueError, IndexError):
            pass

    def _headers(self, extra=None):
        # Схема Bearer, а не OAuth, как в документации.
        #
        # Проверено живьём 30 сентября 2026 на одном и том же токене и
        # одном и том же запросе. Со схемой OAuth сервер отвечает кодом
        # 8000 «OAuth token is missing», то есть утверждает, что токен не
        # прислан, хотя он прислан. Со схемой Bearer тот же запрос
        # доходит до проверки прав и отвечает по существу: код 58,
        # «нужно подать заявку на доступ к API в интерфейсе Директа».
        #
        # Разница в том, что ошибка 8000 про токен уводит в сторону, а
        # ошибка 58 говорит ровно то, что надо сделать. Токен был не при
        # чём, дело было в схеме заголовка, но сообщение об этом молча
        # противоречило реальности. По схеме Bearer причина видна сразу.
        h = {
            "Authorization": "Bearer " + self.token,
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
            # Деньги сразу в рублях, а не в микроединицах.
            "returnMoneyInMicros": "false",
        }
        if extra:
            h.update(extra)
        return h

    def _post(self, url, body, extra=None, timeout=120, raw_response=False):
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            url, data=data, method="POST", headers=self._headers(extra))
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                self._read_units(r.headers)
                self.calls += 1
                text = r.read().decode("utf-8", "replace")
                if raw_response:
                    return r.status, text, dict(r.headers)
                return r.status, _decode(text), dict(r.headers)
        except urllib.error.HTTPError as e:
            self._read_units(e.headers)
            raw = e.read().decode("utf-8", "replace")
            rid = e.headers.get("RequestId", "") if e.headers else ""
            code, msg = _split_error(raw)
            raise DirectError(e.code, code, msg or raw[:300], rid) from None

    # ---------- методы сервисов ----------

    def units_for(self, service, method, count=0):
        """Сколько баллов съест вызов.

        Для методов из таблицы берётся точная цена. Для остальных
        подставляется максимум по всей таблице, 25 за вызов и 20 за
        объект, а не середина. Заглушка нужна для того, чтобы
        недовыпуск приводил к остановке работы, а перерасход к
        неожиданной ошибке 152 на середине выгрузки. Между «остановились
        раньше, чем нужно» и «упали посреди серии запросов» второе
        хуже: часть данных уже записана, и срез получается неполным,
        а выглядит как полный.
        """
        per_call, per_obj = UNITS_PER_CALL.get(
            "%s.%s" % (service, method), (25, 20))
        return per_call + per_obj * count

    def check_budget(self, service, method, count=0, force=False):
        """Не даёт запросу упасть с 152 на середине работы."""
        if self.remaining is None or force:
            return True
        need = self.units_for(service, method, count)
        if need <= self.remaining:
            return True
        self.log("Баллов Директа не хватит: нужно %d, осталось %d из %d"
                 % (need, self.remaining, self.daily or 0))
        return False

    def call(self, service, method, body=None, write=False, count=0):
        """Один вызов метода. Возвращает разобранное тело ответа."""
        name = "%s.%s" % (service, method)
        if name in WRITE_METHODS and not (write or self.write):
            raise DirectError(0, "write_blocked",
                              "%s меняет состояние, вызов заблокирован: "
                              "включите DIRECT_WRITE=1 в .env, когда "
                              "представителю в Директе выданы права на "
                              "редактирование" % name)
        if not self.check_budget(service, method, count):
            raise DirectError(0, "no_units", "баллы исчерпаны, запрос не отправлен")
        url = "%s/v5/%s/%s" % (self.base, service, method)
        _st, data, _h = self._post(url, body or {})
        return data

    def get_paged(self, service, method, body, page_size=1000, cap=1000000):
        """Догружает постранично, пока сервер отдаёт записи."""
        out = []
        offset = 0
        while offset < cap:
            page = dict(body)
            page["Page"] = {"Limit": page_size, "Offset": offset}
            data = self.call(service, method, page)
            rows = data.get(service) or []
            if not rows:
                break
            out.extend(rows)
            offset += len(rows)
            if len(rows) < page_size:
                break
            # Страховка от бесконечного цикла при повторяющихся ответах.
            if not self.check_budget(service, method, len(rows)):
                self.log("Догрузка остановлена: баллы кончились на %d строк" % len(out))
                break
        return out

    # ---------- отчёты ----------

    def report(self, definition, max_wait=1800, poll=15):
        """Формирует отчёт, сам разбираясь с офлайн-очередью.

        Возвращает текст отчёта в формате TSV. Строка заголовков и
        данные разделены табуляцией, значения с разделителем внутри
        экранированы кавычками, поэтому готовый TSV не пересобирается.
        """
        definition = dict(definition)
        definition.setdefault("Format", "TSV")
        definition.setdefault("IncludeVAT", "NO")
        # Офлайн обязателен: по поисковым запросам другого режима нет.
        definition.setdefault("ReportName",
                              "cifra-%s" % str(definition.get("ReportType", "report")))
        attempts = 0
        waited = 0
        last_status = None
        while waited < max_wait:
            attempts += 1
            st, text, headers = self._post(
                self.reports_url, definition,
                extra={"processingMode": "auto"}, raw_response=True)
            last_status = st
            if st == 200:
                return text
            if st == 202:
                retry = headers.get("retryIn") or headers.get("Retry-In")
                try:
                    wait = max(int(str(retry).strip()), 5)
                except (TypeError, ValueError):
                    wait = poll
                self.log("  отчёт в очереди, ждём %d с (попытка %d)"
                         % (wait, attempts))
                time.sleep(wait)
                waited += wait
                continue
            if st == 201:
                time.sleep(poll)
                waited += poll
                continue
            # 400 и 500 сервер возвращают с телом, где есть код ошибки.
            try:
                d = json.loads(text)
            except json.JSONDecodeError:
                d = {}
            raise DirectError(st, d.get("error"),
                              d.get("message") or text[:300],
                              headers.get("RequestId", ""))
        raise DirectError(last_status or 0, "report_timeout",
                          "отчёт не собрался за %d с" % max_wait)

    @staticmethod
    def tsv_to_dicts(text):
        """Разбирает TSV-отчёт в список словарей по строке заголовков.

        Первая строка это заголовок отчёта с его названием, вторая это
        имена полей. Дальше идут данные. Пустые значения и строки из
        одних табуляций пропускаются: Директ отдаёт их в конце отчёта.
        """
        lines = text.split("\n")
        head = None
        for i, line in enumerate(lines):
            if line.strip() and i > 0:
                head = i
                break
        if head is None:
            return [], []
        names = _split_tsv(lines[head])
        rows = []
        for line in lines[head + 1:]:
            if not line.strip():
                continue
            cells = _split_tsv(line)
            if len(cells) < len(names):
                cells += [""] * (len(names) - len(cells))
            rows.append(dict(zip(names, cells[:len(names)])))
        return names, rows


def _tag(xml, name):
    """Достаёт текст тега из XML-конверта Директа."""
    a, b = "<%s>" % name, "</%s>" % name
    i = xml.find(a)
    if i < 0:
        return ""
    j = xml.find(b, i)
    return xml[i + len(a):j].strip() if j > 0 else ""


def _split_tsv(line):
    """Делит строку TSV по табуляции с учётом кавычек.

    Поля Директа содержат запятые и точки с запятой внутри, поэтому
    наивный split по табуляции их не портит, но кавычки в значении
    могут содержать и табуляцию. Разбор с кавычками стоит сорока строк
    и снимает целый класс ошибок разбора.
    """
    out, cur, inq, i = [], [], False, 0
    while i < len(line):
        c = line[i]
        if inq:
            if c == '"':
                if i + 1 < len(line) and line[i + 1] == '"':
                    cur.append('"')
                    i += 1
                else:
                    inq = False
            else:
                cur.append(c)
        elif c == '"':
            inq = True
        elif c == "\t":
            out.append("".join(cur))
            cur = []
        else:
            cur.append(c)
        i += 1
    out.append("".join(cur))
    return out


def to_float(x, default=0.0):
    try:
        return float(str(x).replace(" ", "").replace(",", "."))
    except (TypeError, ValueError):
        return default


if __name__ == "__main__":
    c = DirectClient()
    print("адрес: %s%s" % (c.base, " (песочница)" if c.sandbox else ""))
    try:
        r = c.call("Clients", "get")
        print("логин клиента: %s" % r.get("login"))
        print("баллов: %s" % c.remaining)
    except DirectError as e:
        print("ошибка: %s" % e)
        sys.exit(1)
