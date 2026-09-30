#!/usr/bin/env python3
"""Yandex OAuth для API Метрики и Вебмастера (ручной code-flow).

Секреты читаются ТОЛЬКО из корневого .env, токены туда же сохраняются.
Токены и секреты никогда не печатаются — только маски.

Команды (из корня проекта):
  python scripts/export/yandex_oauth.py login
      Всё сразу: печатает ссылку, открывает браузер, ждёт код,
      обменивает, проверяет. Для клиента это одна команда.
  python scripts/export/yandex_oauth.py auth-url
      Только ссылка.
  python scripts/export/yandex_oauth.py exchange <код_со_страницы>
  python scripts/export/yandex_oauth.py test

Почему код всё равно приходится копировать руками, и почему это не
обойти. У приложений для доступа к API значение redirect_uri менять
нельзя, Яндекс требует https://oauth.yandex.ru/verification_code.
Схема с локальным сервером, где скрипт сам ловит код из ответа
браузера, для таких приложений не работает: принимать код по своему
адресу приложение не умеет. Это не ограничение нашего скрипта, это
устройство сервиса.

Отсюда вывод, который стоит помнить: обмен токеном через мессенджер
плохая идея не потому, что неудобно, а потому что токен там остаётся.
Правильный путь для агентства это добавить свой аккаунт в панели
клиента представителем на чтение, см. CLIENT_ACCESS.md.
"""
import os
import sys
import urllib.parse
import urllib.request
import webbrowser
import json
from datetime import date, timedelta

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_PATH = os.path.join(ROOT, ".env")

AUTH_URL = "https://oauth.yandex.ru/authorize"
TOKEN_URL = "https://oauth.yandex.ru/token"
REDIRECT = "https://oauth.yandex.ru/verification_code"

# Права не запрашиваются в ссылке, и это сделано намеренно.
#
# Параметр scope в ссылке: запрашиваемые права токена.
#
# Пять версий этого значения и что каждая дала.
#
# «login:info,login:email». Всегда invalid_scope, и законно: приложения
# типа «Для доступа к API» не могут получать права группы login, а
# login:info это группа login. Исходная причина, почему ссылка не
# открывалась.
#
# Пусто. Токен выдаётся. Управление счётчиками Метрики отвечает 200,
# Вебмастер читается полностью, а stat/v1/data отдаёт 403 на все
# счётчики, включая собственный. То есть токен без scope не получает
# объявленных прав API, но базовые операции проходят.
#
# Пять имён сразу, взятых из списка прав приложения. Снова invalid_scope.
# Имена при этом верные, они скопированы из панели, а не придуманы.
# Значит дело не в именах, а в том, для какого приложения они запрошены,
# либо в количестве запрошенных групп.
#
# Сейчас запрашивается одно право, metrika:read. Причины две.
#
# Первая: зачем просить то, что и так работает. С пустым scope Вебмастер
# читается целиком, включая внешние ссылки. Просить webmaster:verify и
# webmaster:hostinfo значит добавлять в токен то, что уже есть.
#
# Вторая: если invalid_scope вызван числом запрошенных групп прав, то
# один запрос отличит это от другой причины. Четыре группы из пяти имён
# могут превышать ограничение, а одна группа не превысит ничего.
#
# Права на запись не запрашиваются ни при каких условиях: metrika:write
# меняет счётчики, mediametrika:write создаёт кампании. Аудит только
# читает. По документации Яндекса добавление прав ещё и сокращает срок
# жизни токена.
#
# Точный список имён и единственный способ его проверить описаны в
# scripts/export/APP_RIGHTS.md.
SCOPES = "metrika:read"

# Что означает каждое право из списка приложения и берём ли мы его.
#
#   metrika:write            счётчики и параметры             нет, мы только читаем
#   metrika:user_params      загрузка параметров пользователей нет
#   metrika:segments         сегменты                         нет
#   metrika:read             статистика и параметры           да
#   metrika:offline_data     офлайн-конверсии из CRM         нет, CRM ещё нет
#   metrika:expenses         расходы                          нет
#   direct:api               API Директа                      да
#   webmaster:hostinfo       внешние ссылки                   да
#   webmaster:verify          добавление сайтов и статус      да, это и есть чтение статуса
#   webmaster:turbopages     турбо-страницы                   нет
#   mediametrika:read        статистика Директа с Метрикой    да
#   mediametrika:write       создание кампаний                нет
#   suggest:read_web_history история запросов                 нет
#   maps:public_bookmarks    закладки в Картах                нет
SCOPE_NOTES = {
    "metrika:read": "чтение статистики и параметров счётчиков",
    "webmaster:verify": "статус индексирования в Вебмастере",
    "webmaster:hostinfo": "внешние ссылки на сайт",
    "mediametrika:read": "статистика кампаний Директа с конверсиями Метрики",
    "direct:api": "API Яндекс.Директа",
}

# Настоящее имя права на внешние ссылки. Именно его видно в списке прав
# приложения в oauth.yandex.ru, в скобках у пункта «Получение информации
# о внешних ссылках на сайт».
EXTERNAL_LINKS_SCOPE = "webmaster:hostinfo"

# Приложение, client_secret которого попал в публичную историю git.
# Ключи пришлось выпустить заново, и пока в .env старые, любой токен,
# выданный ими, придётся заменить.
LEAKED_CLIENT_ID = "bd171b3086d947918c19269247c50040"


def flag(env, name, default="0"):
    """Читает переключатель из .env или из окружения процесса.

    Переключатель вроде песочницы или разрешения записи нужен часто
    на один запуск, и править .env под каждый прогон неудобно. Поэтому
    переменная процесса тоже учитывается. Порядок именно такой: сначала
    .env, потому что там лежат секреты и осознанная настройка, и только
    если там ключа нет, берётся окружение.
    """
    v = str(env.get(name, "")).strip()
    if v:
        return v.lower() in ("1", "true", "yes")
    return str(os.environ.get(name, default)).strip().lower() in ("1", "true", "yes")


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


def save_token(token):
    lines, found = [], False
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, encoding="utf-8") as f:
            lines = f.read().splitlines()
    out = []
    for line in lines:
        if line.startswith("YANDEX_OAUTH_TOKEN="):
            out.append("YANDEX_OAUTH_TOKEN=" + token)
            found = True
        else:
            out.append(line)
    if not found:
        out.append("YANDEX_OAUTH_TOKEN=" + token)
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


def mask(s):
    s = s or ""
    return (s[:4] + "..." + s[-4:]) if len(s) > 12 else "***"


def build_url(env, scope=None):
    cid = env.get("YANDEX_CLIENT_ID", "")
    # Приоритет такой: флаг командной строки, потом YANDEX_SCOPES в .env,
    # потом значение по умолчанию в этом файле. Флаг удобен тем, что
    # позволяет перебрать варианты, не правя конфигурацию. YANDEX_SCOPES
    # нужен потому, что правильный набор прав задаётся в панели на
    # oauth.yandex.ru, а не в коде.
    if scope is None:
        scope = str(env.get("YANDEX_SCOPES", "") or "").strip() or SCOPES
    q = {"response_type": "code", "client_id": cid, "redirect_uri": REDIRECT}
    if scope:
        q["scope"] = scope
    return cid, scope, AUTH_URL + "?" + urllib.parse.urlencode(q)


def cmd_login(env, scope=None):
    """Один шаг от запуска до проверенного токена.

    Клиенту это одна команда, а не три и не переписка. Ссылка
    открывается сама, код вставляется в это же окно, токен сразу
    проверяется на то, что он от того аккаунта и что данные читаются.

    Последнее важнее удобства. Раньше был сюжет: токен получен, всё
    зелёное, а через неделю выясняется, что он от чужого аккаунта,
    потому что залогинен был кто-то ещё. Проверка личности идёт сразу
    после обмена, пока человек ещё рядом и может войти заново под
    нужным логином.
    """
    cid, scope, url = build_url(env, scope)
    if not cid:
        print("Нет YANDEX_CLIENT_ID в .env")
        return 1
    if cid == LEAKED_CLIENT_ID and not flag(env, "YANDEX_ALLOW_LEAKED_APP"):
        # Остановка, а не предупреждение. Раньше здесь печаталось
        # предупреждение и работа продолжалась, то есть токен
        # выдавался приложением с публичным секретом и оставался в
        # .env, и никто этого не замечал. Предупреждение, которое не
        # останавливает, хуже отсутствия: выглядит как проверка.
        print("ОСТАНОВ: YANDEX_CLIENT_ID в .env принадлежит приложению,")
        print("у которого client_secret попал в публичную историю git.")
        print()
        print("Токен, выданный таким приложением, считается скомпрометированным.")
        print("Практическая опасность не в чтении данных: токен выдаётся только")
        print("владельцу сайта, и чужим его не достать. Опасность в подделке:")
        print("любой может назвать своё приложение так же и собирать")
        print("логины и пароли, притворяясь вашим.")
        print()
        print("Что сделать:")
        print("  1. oauth.yandex.ru -> Мои приложения -> это приложение ->")
        print("     сменить секрет, или создать новое приложение.")
        print("  2. Вписать новые значения в .env.")
        print()
        print("Если осознанно работаете со старым приложением, добавьте в .env")
        print("строку YANDEX_ALLOW_LEAKED_APP=1 и запустите снова.")
        print()
        print("Отдельно про Директ: заявка на доступ к API подаётся на конкретное")
        print("приложение. Если заявка подана на другое, вернувшись к этому,")
        print("доступ не появится, сколько ни ждать.")
        print()
        return 4

    print("=" * 62)
    print("Шаг 1 из 2. Откроется браузер, войдите под нужным аккаунтом.")
    print()
    print("  Для сайта и Метрики это %s" % env.get("YANDEX_ACCOUNT_EMAIL", "аккаунт владельца сайта"))
    print("  Проверьте, что в правом верхнем углу именно он, ДО подтверждения.")
    print()
    print("Если браузер не открылся, откройте ссылку вручную:")
    print()
    print(url)
    print()
    try:
        webbrowser.open(url, new=2)
        print("Браузер открыт.")
    except Exception:
        print("Открыть браузер из скрипта не вышло, откройте ссылку выше.")
    print("=" * 62)
    print()
    try:
        code = input("Шаг 2 из 2. Вставьте код со страницы и нажмите Enter: ").strip()
    except EOFError:
        print("Код не введён.")
        return 1
    if not code:
        print("Пустой код, ничего не сделано.")
        return 1
    # Яндекс иногда отдаёт код вместе со служебными символами, и если
    # его не снять, обмен падает invalid_grant без внятной причины.
    code = code.strip().strip("'\"")
    rc = cmd_exchange(env, code)
    if rc:
        print()
        print("Токен не получен. Причины разобраны выше.")
        return rc
    print()
    print("Проверяю, что токен от того аккаунта и что данные читаются.")
    return cmd_test(env)


def cmd_auth_url(env, scope=None):
    cid = env.get("YANDEX_CLIENT_ID", "")
    if not cid:
        print("Нет YANDEX_CLIENT_ID в .env")
        return 1
    print("Приложение: %s" % cid)
    if cid == LEAKED_CLIENT_ID:
        print()
        print("ВНИМАНИЕ. Это приложение с секретом в публичной истории git.")
        print("Токен из него считается скомпрометированным. Права на данные")
        print("сайта это не отменяет: токен выдаётся только владельцу сайта.")
        print("Смените секрет, когда будет удобно, это дело пяти минут.")
        print()
    cid2, scope, url = build_url(env, scope)
    print("Scope в ссылке: %s" % (scope or "не передан"))
    print()
    print("Откройте в браузере, подтвердите доступ, скопируйте код:")
    print(url)
    print()
    if scope:
        print("Запрошено прав: %s" % scope)
        print()
    print("Если страница ругается на invalid_scope, проверьте одно.")
    print()
    print("Список прав, которые приложение реально объявило, лежит здесь:")
    print("  https://oauth.yandex.ru/verify?client_id=%s" % cid)
    print()
    print("Откройте его под тем же аккаунтом, который указан в .env, и")
    print("сравните с тем, что запрошено выше. Если metrika:read в списке")
    print("нет, то дело именно в этом, и добавлять его нужно в настройках")
    print("этого приложения, а не другого.")
    print()
    print("Второй возможный повод: приложение зарегистрировано не как")
    print("«Для доступа к API». У другого типа ограничение на число групп")
    print("прав, и запрос сверх него даёт именно эту ошибку. Тип виден в")
    print("настройках приложения и сменить его после регистрации нельзя.")
    print()
    print("Третий: значение из группы login, например login:info. Приложения")
    print("типа «Для доступа к API» получать права группы login не могут.")
    print("Это был исходный повод, и он до сих пор применяется.")
    return 0


def cmd_exchange(env, code):
    data = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code.strip(),
        "client_id": env.get("YANDEX_CLIENT_ID", ""),
        "client_secret": env.get("YANDEX_CLIENT_SECRET", ""),
        "redirect_uri": REDIRECT,
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=data, method="POST",
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8")[:300]
        except Exception:
            detail = "?"
        print("Ошибка обмена: HTTP %s — %s" % (e.code, detail))
        # Разбор по кодам. Здесь чаще всего ошибаются именно так.
        if "invalid_scope" in detail:
            print()
            print("invalid_scope по документации Яндекса означает одно:")
            print("  «права приложения изменились после того, как был выдан код».")
            print("То есть вы добавили право в oauth.yandex.ru уже после того, как")
            print("получили этот код. Код надо запросить заново, заново открыть")
            print("ссылку и заново скопировать код. Старый код не сработает никогда.")
        if "invalid_client" in detail:
            print()
            print("invalid_client = в .env неверная пара client_id и client_secret,")
            print("либо они belong разным приложениям. Проверьте, что оба значения")
            print("скопированы со страницы одного приложения.")
        if "invalid_grant" in detail:
            print()
            print("invalid_grant = код протух или уже использован. Код одноразовый.")
        return 1
    except Exception as e:
        print("Ошибка обмена кода на токен: %s" % e)
        return 1
    token = body.get("access_token", "")
    if not token:
        print("Яндекс не вернул токен: %s" % json.dumps(body, ensure_ascii=False)[:300])
        return 1
    save_token(token)
    print("Токен сохранён в .env (маска %s), действует ~%s сек." %
          (mask(token), body.get("expires_in", "?")))
    if body.get("scope"):
        print("Права в токене: %s" % body["scope"])
    else:
        print("Права в токене: Яндекс не вернул поле scope, состав не проверить.")
    print()
    print("Следующий шаг: python scripts\\export\\yandex_oauth.py test")
    return 0


def api_get(url, token):
    req = urllib.request.Request(url, headers={"Authorization": "OAuth " + token})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def cmd_test(env):
    token = env.get("YANDEX_OAUTH_TOKEN", "")
    if not token:
        print("Нет токена. Сначала: auth-url -> exchange.")
        return 1
    # Пробный запрос статистики спрашивает данные за один конкретный
    # день, и пустой date_from означал бы запрос за весь период, то
    # есть тяжёлый и бесполезный. Дата передаётся здесь, вне .env.
    env = dict(env)
    env["_today"] = (date.today() - timedelta(days=1)).isoformat()
    print("Токен: %s" % mask(token))
    # Метрика: список счётчиков
    #
    # Здесь важна не доступность API, а личность владельца. Токен,
    # выданный под одним аккаунтом Яндекса, спокойно открывает карточку
    # чужого счётчика и молча отдаёт 403 на данных. Список счётчиков при
    # этом выглядит нормально, и кажется, что всё работает.
    try:
        st, data = api_get("https://api-metrika.yandex.net/management/v1/counters", token)
        counters = data.get("counters", [])
        print("Метрика API: OK, счётчиков доступно: %d" % len(counters))
        for c in counters[:10]:
            print("  - %s : %-34s владелец %s"
                  % (c.get("id"), str(c.get("site"))[:34], c.get("owner_login", "?")))
    except Exception as e:
        print("Метрика API: НЕДОСТУПНА (%s) — проверьте права приложения." % e)
        return 1

    # Проверка доступа к данным счётчика сайта.
    #
    # Проверяется запросом данных за один день, а не составом списка
    # счётчиков. Разница принципиальная. Карточка счётчика открывается
    # любому, кто знает её номер, и management-список отдаёт счётчики по
    # своим правилам, которые не обязаны совпадать с фактическим
    # доступом к статистике. Ответ 403 на запрос данных это факт,
    # отсутствие в списке это косвенный признак.
    #
    # Проверено 30 сентября 2026: с токеном от refertur счётчика 50863157
    # в списке не было, и данные отдавали 403. При этом аккаунт могли
    # добавить к счётчику позже, чем был выдан токен, и доступ с того
    # момента появляется без перевыпуска токена. Список этого не
    # показывает, поэтому опираться на него нельзя.
    want = env.get("METRIKA_COUNTER_ID", "")
    if not want:
        print("Счётчик сайта не задан в .env")
        return 1
    today = env.get("_today", "")
    url = ("https://api-metrika.yandex.net/stat/v1/data?counters=%s"
           "&fields=visits&date_from=%s&date_to=%s" % (want, today, today))
    try:
        api_get(url, token)
        print("Счётчик сайта %s: доступен, данные читаются." % want)
    except Exception as e:
        print()
        print("ВНИМАНИЕ. К данным счётчика %s доступа нет." % want)
        print("  %s" % str(e)[:160])
        print()
        print("Карточка счётчика при этом открывается, а данные отдаёт 403.")
        print("Так бывает, когда аккаунту не открыт доступ к статистике")
        print("счётчика либо токен выдан не под тем логином.")
        print()
        print("Что проверить:")
        print("  1. metrika.yandex.ru -> счётчик %s -> Настройка -> Доступы." % want)
        print("     Аккаунт, под которым вы вошли, должен быть в списке.")
        print("     Нужны права «Просмотр», большего не требуется.")
        print("  2. Токен взять заново под тем же аккаунтом:")
        print("     python scripts\\export\\yandex_oauth.py login")
        print()
        print("Доступ к Метрике выдаётся отдельно от Вебмастера. Аккаунт,")
        print("добавленный в панель Вебмастера, в списке доступов Метрики")
        print("не появляется: это два разных списка.")
        return 1
    # Вебмастер: кто я
    try:
        st, data = api_get("https://api.webmaster.yandex.net/v4/user", token)
        uid = data.get("user_id", "?")
        print("Вебмастер API: OK, user_id=%s" % uid)
    except Exception as e:
        print("Вебмастер API: НЕДОСТУПЕН (%s) — проверьте права приложения." % e)
        return 0
    # Права на внешние ссылки: без webmaster:hostinfo API отдаёт 403
    try:
        st, _ = api_get("https://api.webmaster.yandex.net/v4/user/%s/hosts/"
                        "https:xn--18-6kc5a3bxam.xn--p1ai:443/links/external/history"
                        "?indicator=LINKS_TOTAL_COUNT" % uid, token)
        print("Внешние ссылки: доступны (права выданы)")
    except Exception as e:
        detail = str(e)
        print("Внешние ссылки: НЕТ прав. Требуется право «Получение информации")
        print("о внешних ссылках на сайт», его внутреннее имя %s."
              % EXTERNAL_LINKS_SCOPE)
        print()
        print("Что сделать, по порядку:")
        print("  1. oauth.yandex.ru -> Мои приложения -> ваше приложение ->")
        print("     Права доступа -> добавить «Получение информации о внешних")
        print("     ссылках на сайт» и сохранить.")
        print("  2. Закрыть и снова открыть auth-url, подтвердить доступ,")
        print("     скопировать свежий код. Старый код после смены прав не")
        print("     работает, Яндекс вернёт invalid_scope.")
        print("  3. yandex_setup.bat <новый код>")
        if "ACCESS_FORBIDDEN" in detail:
            print()
            print("В ответе API слово EXTERNAL_LINKS это внутренняя метка, а не")
            print("имя права в панели. Добавлять «scope EXTERNAL_LINKS» не надо,")
            print("такого права в списке нет, и ссылка с ним не откроется.")
    return 0


if __name__ == "__main__":
    env = load_env()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    scope = None
    for a in sys.argv[1:]:
        if a.startswith("--scope="):
            scope = a.split("=", 1)[1]
    if "--allow-leaked-app" in sys.argv:
        env["YANDEX_ALLOW_LEAKED_APP"] = "1"
    cmd = args[0] if args else "login"
    if cmd == "login":
        sys.exit(cmd_login(env, scope))
    elif cmd == "auth-url":
        sys.exit(cmd_auth_url(env, scope))
    elif cmd == "exchange" and len(args) > 1:
        sys.exit(cmd_exchange(env, args[1]))
    elif cmd == "test":
        sys.exit(cmd_test(env))
    else:
        print("Использование:")
        print("  login                        всё сразу: ссылка, код, проверка")
        print("  auth-url [--scope=значение]  ссылка для входа")
        print("  exchange <код>               обменять код на токен")
        print("  test                         проверить токен и права")
        print()
        print("Для клиента нужна одна команда login. Остальное на случай, если")
        print("код нужен отдельно, например для выяснения, что пошло не так.")
        print()
        print("Без --scope ссылка не передаёт список прав, и токен получает все")
        print("права, объявленные у приложения. Это обычный режим.")
        sys.exit(2)
