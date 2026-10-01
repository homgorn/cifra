#!/usr/bin/env python3
"""Yandex OAuth для API Метрики и Вебмастера (ручной code-flow).

Секреты читаются ТОЛЬКО из корневого .env, токены туда же сохраняются.
Токены и секреты никогда не печатаются — только маски.

Команды (из корня проекта):
  python scripts/export/yandex_oauth.py login
      Всё сразу: печатает ссылку, открывает браузер, ждёт токен,
      сохраняет и проверяет. Для клиента это одна команда.
      Использует response_type=token по документации Метрики.
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

# Прямое получение токена, как велит документация Метрики:
# response_type=token, без redirect_uri и без scope. Токен показывается
# на странице как текст, копируется руками, обмен кода не нужен.
#
# Почему это главный способ, а кодовый запасной. Ответы invalid_scope
# приходили именно из кодового флоу: при response_type=code Яндекс
# проверяет scope по списку прав и отказывает, если что-то не так, а
# перечислить этот список негде: документация отсылает к странице
# oauth.yandex.ru/verify, которая отдаёт 404 и была удалена. При
# response_type=token список не нужен вовсе, потому что не запрашивается.
TOKEN_MODE_URL = "https://oauth.yandex.ru/authorize"

# Права не запрашиваются в ссылке, и это сделано намеренно.
#
# Параметр scope в ссылке КОДОВОГО флоу, response_type=code.
#
# По умолчанию пуст, и это не отладка, а вывод из четырёх попыток.
# «login:info,login:email» всегда давали invalid_scope, потому что
# приложения типа «Для доступа к API» не могут получать права группы
# login. Пустой scope выдавал токен без прав API. Пять имён, скопированных
# из панели, снова давали invalid_scope. Одно имя тоже.
#
# Причина в том, что кодовый флоу здесь лишний. Документация Метрики
# предписывает получать токен через response_type=token, где список прав
# не запрашивается вовсе и потому не проверяется. Основной путь теперь
# такой, см. token_url и cmd_login.
#
# Значение оставлено только для кодового флоу, на случай если кто-то
# вернётся к нему осознанно. Подробности в APP_RIGHTS.md.
# Права, запрашиваемые в ссылке входа.
#
# По умолчанию НЕ запрашиваются, и это проверено, а не предположено.
#
# Пустой scope даёт токен, который читает Вебмастер полностью, включая
# внешние ссылки, и управление счётчиками Метрики.
#
# Проверка со scope=metrika:read дала обратный и неожиданный результат.
# Вебмастер на таком токене перестал работать совсем:
#   HTTP 403, «Access to this resource is not allowed with scopes
#   available for this application. Required scope: ...»
# То есть перечень запрошенных прав работает как ограничитель, а не
# как добавка: назвал одно право, остальные отвалились. Управление
# счётчиками Метрики при этом продолжило работать.
#
# Отчёты не открылись ни с одним из вариантов, см. APP_RIGHTS.md.
# Запрашивать права оказалось не только бесполезно, но и вредно, потому
# что ломало то, что работало. Поэтому по умолчанию прав нет, и
# YANDEX_SCOPES в .env или флаг --scope= остаются для ручного разбора.
SCOPES = ""

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


def token_history(env, add=None):
    """Хвост ранее выданных токенов, новые в начало.

    Нужно потому, что за день пришлось выдать шесть токенов, и все они
    приходили в переписке вперемешку. Один из них прислали повторно через
    несколько шагов, он был выдан до добавления scope, повторный прогон
    дал ожидаемый 403, и вывод сделался неверный. Отличать новый токен
    от старого по маске в разговоре невозможно, последние четыре символа
    у разных токенов совпадают нечасто, но путаница происходит именно
    потому, что токен выглядит новым.

    Хранится в .env, то есть вне git.
    """
    raw = env.get("YANDEX_TOKEN_HISTORY", "")
    items = [x.strip() for x in raw.split(",") if x.strip()]
    if add:
        items = [add] + [x for x in items if x != add]
        items = items[:8]
        lines = []
        if os.path.exists(ENV_PATH):
            with open(ENV_PATH, encoding="utf-8") as f:
                lines = f.read().splitlines()
        out, found = [], False
        for line in lines:
            if line.startswith("YANDEX_TOKEN_HISTORY="):
                out.append("YANDEX_TOKEN_HISTORY=" + ",".join(items))
                found = True
            else:
                out.append(line)
        if not found:
            out.append("YANDEX_TOKEN_HISTORY=" + ",".join(items))
        with open(ENV_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(out) + "\n")
    return items


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


def _put_env(key, value):
    """Записать пару ключ-значение в .env, не трогая остальные строки."""
    lines = []
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, encoding="utf-8") as f:
            lines = f.read().splitlines()
    out, found = [], False
    for line in lines:
        if line.split("=", 1)[0].strip() == key:
            out.append(key + "=" + value)
            found = True
        else:
            out.append(line)
    if not found:
        out.append(key + "=" + value)
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


def save_token(token, app_id=None):
    """Сохранить токен и запомнить, каким приложением он выдан.

    Из самого токена нельзя узнать, какое приложение его выдало, а от
    этого зависит, работает ли он. Приложение без права metrika:read
    выдаёт токен, который читает список счётчиков и не читает ни одного
    отчёта. Причина описана в документации Яндекс Метрики дословно,
    раздел «Возможные проблемы и их решение», блок «На стороне токена»:
    «Токен создан не для того приложения... токен был заведён на
    приложение, не имеющее доступа к Метрике».

    Поэтому рядом с токеном пишется приложение. После этого любой
    прогон может назвать приложение, выдавшее текущий токен, и не
    гадать, откуда он взят.
    """
    _put_env("YANDEX_OAUTH_TOKEN", token)
    if app_id:
        _put_env("YANDEX_TOKEN_APP", app_id)
        print("Токен выдан приложением: %s" % app_id)


def app_mismatch(env):
    """Расхождение между приложением в .env и тем, что выдало токен.

    Возвращает строку с предупреждением или пустую строку, если всё
    сходится. Пустая строка означает, что проверить нечем: сведения о
    приложении ещё не записывались.
    """
    cur = env.get("YANDEX_CLIENT_ID", "")
    tok_app = env.get("YANDEX_TOKEN_APP", "")
    if not cur:
        return "Нет YANDEX_CLIENT_ID в .env, ссылку входа построить нечем."
    if not tok_app:
        return ""
    if cur == tok_app:
        return ""
    return ("ТОКЕН И ССЫЛКА ОТ РАЗНЫХ ПРИЛОЖЕНИЙ.\n"
            "  Токен в .env выдан приложению: %s\n"
            "  Ссылка входа сейчас строится на: %s\n"
            "  Токен, выданный приложением без права metrika:read, читает\n"
            "  список счётчиков и не читает ни одного отчёта. Отчётный\n"
            "  сервис отказывает до проверки счётчика, поэтому отказ\n"
            "  выглядит одинаково для любого номера, включая\n"
            "  несуществующий. Проверь, какое приложение живое, прежде\n"
            "  чем выдавать новый токен." % (tok_app, cur))


def mask(s):
    s = s or ""
    return (s[:4] + "..." + s[-4:]) if len(s) > 12 else "***"


def token_from_url(raw):
    """Достать токен из того, что Яндекс отдал в браузере.

    При response_type=token Яндекс возвращает токен во «якоре» адреса,
    то есть после символа #, и браузер этот кусок не отправляет на
    сервер. Пользователь копирует адрес целиком, и разбирать его
    приходится здесь.

    Принимается и голый токен, потому что люди копируют что попало:
    ссылку, только значение, значение с кавычками, строку с пробелами.
    """
    raw = (raw or "").strip().strip("\"'")
    if "access_token=" in raw:
        frag = raw.split("access_token=", 1)[1]
        return frag.split("&", 1)[0].split("#", 1)[0].strip()
    if raw.startswith("y0_"):
        return raw
    return ""


def build_url(env, scope=None):
    cid = env.get("YANDEX_CLIENT_ID", "")
    # Приоритет такой: флаг командной строки, потом YANDEX_SCOPES в .env,
    # потом значение по умолчанию в этом файле. Флаг удобен тем, что
    # позволяет перебрать варианты, не правя конфигурацию. YANDEX_SCOPES
    # нужен потому, что правильный набор прав задаётся в панели на
    # oauth.yandex.ru, а не в коде.
    if scope is None:
        scope = str(env.get("YANDEX_SCOPES", "") or "").strip() or SCOPES
    mode = "implicit" if str(env.get("YANDEX_FLOW", "")).strip() == \
        "token" else "code"
    q = {"response_type": "token" if mode == "implicit" else "code",
         "client_id": cid, "redirect_uri": REDIRECT}
    if scope:
        q["scope"] = scope
    return cid, scope, AUTH_URL + "?" + urllib.parse.urlencode(q)


def token_url(env, scope=None):
    """Адрес для прямого получения токена плюс запрошенные права.

    По умолчанию прав не запрашивается, и это соответствует документации
    Метрики. Но на практике токен без прав читает управление счётчиками и
    не читает отчёты, даже демо-счётчик из справки: проверено 30 сентября
    2026, ответ 403 access_denied и на счётчике, на который у токена нет
    никаких прав. То есть право на отчёты в токен просто не попало.

    Поэтому запрашивается явно. Сочетание response_type=token со scope
    раньше не пробовалось: scope проверялся только на кодовом флоу, где он
    давал invalid_scope, и на этом вывод встали. Здесь кодовый флоу и не
    используется.
    """
    cid = env.get("YANDEX_CLIENT_ID", "")
    q = {"response_type": "token", "client_id": cid}
    if scope is None:
        scope = str(env.get("YANDEX_SCOPES", "") or "").strip() or SCOPES
    if scope:
        q["scope"] = scope
    return cid, scope, ("%s?%s" % (TOKEN_MODE_URL, urllib.parse.urlencode(q)))


def cmd_login(env, scope=None):
    """Один шаг от запуска до проверенного токена.

    Используется response_type=token, то есть рекомендованный Метрикой
    способ. Токен появляется на странице текстом, копируется и вставляется
    сюда. Никакого кода подтверждения и никакого обмена, а значит и
    invalid_scope, который приходил трижды именно на кодовом флоу.

    Проверка личности токена идёт сразу после вставки. За этот проект
    было выдано несколько токенов не от того аккаунта, и каждый раз API
    отвечал успешно, поэтому ловить это нужно тут, пока человек у
    экрана.
    """
    cid, scope, url = token_url(env, scope)
    if not cid:
        print("Нет YANDEX_CLIENT_ID в .env")
        return 1
    print("=" * 62)
    print("Шаг 1 из 2. Откроется браузер.")
    print()
    print("Войдите под СВОИМ аккаунтом, тем, что добавлен в Вебмастер")
    print("и в счётчик Метрики. НЕ под аккаунтом владельца сайта %s."
          % env.get("YANDEX_ACCOUNT_EMAIL", "из .env"))
    print()
    print("Проверьте, кто вы в правом верхнем углу, ДО подтверждения.")
    print()
    print("Если браузер не открылся, откройте ссылку вручную:")
    print()
    print(url)
    print()
    try:
        webbrowser.open(url, new=2)
        print("Браузер открыт.")
    except Exception:
        print("Открыть браузер не вышло, откройте ссылку выше.")
    print("=" * 62)
    print()
    try:
        token = input("Шаг 2 из 2. Вставьте токен со страницы и нажмите Enter: ").strip()
    except EOFError:
        print("Токен не введён.")
        return 1
    token = token.strip().strip("'\"")
    if not token:
        print("Пустой токен, ничего не сделано.")
        return 1
    if len(token) < 20:
        print("Это не похоже на токен: %d символов." % len(token))
        print("Скопируйте текст со страницы целиком, а не то, что под ним.")
        return 1
    history = token_history(env)
    if token in history:
        print()
        print("ВНИМАНИЕ: этот токен уже присылался ранее, он не новый.")
        print("Что добавлялось после его выдачи, в него не попало.")
        print()
        print("Чтобы получить токен с новыми правами:")
        print("  1. Отозвать на id.yandex.ru/personal/data-access")
        print("  2. Открыть заново ссылку из login и подтвердить доступ")
        print("  3. Убедиться, что Яндекс показал новый токен, а не тот же")
        return 4

    # Токен не изменился после добавления прав. При response_type=token
    # Яндекс возвращает уже выданный действующий токен, а новые права в
    # него не подставляются: право появляется только в новом токене.
    # Проверка нужна потому, что иначе ситуация выглядит как «право
    # добавил, токен взял, не работает», и следующим шагом обычно
    # добавляют что-то ещё, вместо того чтобы отозвать токен.
    previous = env.get("YANDEX_OAUTH_TOKEN", "")
    if previous and previous == token:
        print()
        print("ВНИМАНИЕ: токен не изменился, он такой же, как был в .env.")
        print("Яндекс вернул уже выданный действующий токен. Новые права")
        print("в него не подставляются, они попадают только в новый токен.")
        print()
        print("Что сделать:")
        print("  1. Отозвать текущий токен:")
        print("     https://id.yandex.ru/personal/data-access")
        print("     Найти это приложение и отозвать доступ.")
        print("  2. Взять токен заново:")
        print("     python scripts\\export\\yandex_oauth.py login")
        print()
        print("Первый шаг пропускать нельзя. Без отзыва новый токен будет")
        print("выдан точно такой же, и разницы не будет.")
        return 4

    token_history(env, token)
    save_token(token)
    print("Токен новый, отличается от прежнего. Сохранён в .env, маска %s."
          % mask(token))
    print()
    print("Проверяю, что он от того аккаунта и что данные читаются.")
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
    print("Откройте в браузере, подтвердите доступ, скопируйте")
    print("адрес страницы целиком или только токен из него:")
    print(url)
    print()
    if scope:
        print("Запрошено прав: %s" % scope)
        print()
    print("Если страница ругается на invalid_scope, значит в ссылке scope,")
    print("которого нет в правах приложения. Список прав берётся из")
    print("настроек приложения на oauth.yandex.ru и вписывается в")
    print("YANDEX_SCOPES в .env либо проверяется флагом --scope=...")
    print()
    print("По умолчанию scope не передаётся, и это проверено: пустой")
    print("список даёт токен, который читает Вебмастер целиком. Список со")
    print("scope работает как ограничитель, а не как добавка: названное")
    print("право сохраняется, не названные отваливаются. Добавлять scope")
    print("ради одного сервиса нельзя, остальные от этого ломаются.")
    print()
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


def cmd_paste(env, raw):
    """Принять то, что прислал человек, и проверить токен.

    В неявном потоке Яндекс отдаёт токен в адресе страницы, и человек
    копирует либо сам адрес, либо только значение, либо значение в
    кавычках. Раньше скрипт ждал ровно токен, из-за чего годятся не
    все три варианта и приходилось гадать, что именно прислали.

    Порядок такой: сохранить, отметить приложение, прогнать пробу.
    Приложение записывается обязательно, иначе токен снова останется
    без следа о том, кто его выдал.
    """
    tok = token_from_url(raw)
    if not tok:
        print("Это не похоже на токен.")
        print()
        print("Ожидается одно из трёх:")
        print("  токен целиком, начинается с y0_")
        print("  адрес страницы, в нём есть access_token=")
        print("  токен в кавычках, кавычки снимаются сами")
        print()
        print("Прислано: %r" % (raw or "")[:120])
        return 2
    # Тот же токен, что уже сохранён. Проверять его и рапортовать о
    # результате как о новом нельзя: вывод будет правдивым и бесполезным,
    # а человек решит, что проверка состоялась. Именно так у человека в
    # Клубе Метрики и в задаче на GitHub ушло время впустую: токен
    # обновили, он не изменился, вывод сделали с новым.
    #
    # Почему токен может не измениться: если выданный токен ещё жив,
    # Яндекс OAuth возвращает тот же самый, новый не создаётся.
    # Следствие для проверки прав: пока прежний токен не отозван,
    # запрос с другим перечнем прав вернёт прежний, и проверить
    # ограничение нечем.
    if tok == env.get("YANDEX_OAUTH_TOKEN", ""):
        print("Это тот же токен, что уже лежит в .env, символ в символ.")
        print()
        print("Новым он не стал, поэтому и права в нём прежние. Проверять")
        print("смысла нечего, результат ниже повторит уже известный.")
        print()
        print("Почему так бывает: если выданный токен ещё действителен,")
        print("Яндекс OAuth отдаёт его же, а новый не создаёт.")
        print()
        print("Чтобы получить токен с другим набором прав, нужно:")
        print("  1. Отозвать прежний на id.yandex.ru/personal/data-access")
        print("  2. Открыть ссылку заново и скопировать токен")
        print()
        return 1

    save_token(tok, app_id=env.get("YANDEX_CLIENT_ID", ""))
    print()
    print("Токен принят и сохранён.")
    print()
    # Проверять нужно по только что записанному токену, а не по тому
    # окружению, которое было прочитано при запуске процесса. Иначе
    # paste показывает права старого токена, и вывод относится не к
    # тому, что только что прислали. На случилось 1 октября: токен
    # принят, показан предыдущий.
    return cmd_test(load_env())


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
    # Каким приложением выдан токен. Из самого токена это не читается,
    # поэтому хранится рядом с ним и сверяется с тем, на что сегодня
    # строится ссылка входа.
    print("ПРИЛОЖЕНИЕ ТОКЕНА")
    _app_now = env.get("YANDEX_CLIENT_ID", "")
    _app_tok = env.get("YANDEX_TOKEN_APP", "")
    print("  ссылка строится на: %s" % (_app_now or "нет в .env"))
    if _app_tok:
        print("  токен выдан на:     %s" % _app_tok)
    else:
        print("  токен выдан на:     НЕИЗВЕСТНО, ключа нет в .env")
        print("  Приложение, выдавшее токен, из токена не читается, сверить")
        print("  нечем. Пустое значение выглядит как отсутствие проблемы,")
        print("  поэтому названо прямо. Ключ ставится при выдаче токена.")
    _warn = app_mismatch(env)
    if _warn:
        print()
        print(_warn)
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
        print("Карточка не доказывает доступ: она открывается любому, кто")
        print("знает номер. Проверяю список доступных счётчиков, он честный.")
        _st3, b3 = api_get(
            "https://api-metrika.yandex.net/management/v1/counters", token)
        have = {str(c.get("id")) for c in (b3.get("counters") or [])}
        org = None
        try:
            _st4, b4 = api_get(
                "https://api-metrika.yandex.net/management/v1/accounts", token)
            _a = b4.get("accounts") or []
            org = _a[0].get("user_login") if _a else None
        except Exception:
            pass

        print()
        print("ПРИЧИНА 1, её решает не токен, а владелец счётчика:")
        if want in have:
            print("  Счётчик %s в списке доступных, этот пункт закрыт." % want)
        else:
            print("  Счётчика сайта %s НЕТ в списке доступных." % want)
            print("  Значит аккаунт, под которым вы вошли, не добавлен к этому")
            print("  счётчику. Угадать это нельзя и токеном не лечится.")
            print("  Нужно: владелец счётчика открывает metrika.yandex.ru,")
            print("  счётчик %s, Настройка, Доступы, и добавляет аккаунт" % want)
            print("  исполнителя с правами «Просмотр».")

        print()
        print("ПРИЧИНА 2, её решают права приложения:")
        own = [c for c in (b3.get("counters") or [])
               if c.get("permission") == "own"]
        # api_get бросает исключение на 403, а 403 здесь и есть ожидаемый
        # ответ, который нужно разобрать, а не поймать как сбой. Без
        # обработки проверка падала с трассировкой ровно в том случае,
        # когда неполадки и происходили, то есть всегда не вовремя.
        probe = (own[0].get("id") if own else want)
        try:
            api_get("https://api-metrika.yandex.net/stat/v1/data?counters=%s"
                    "&fields=visits&period=day&date_from=2026-09-01"
                    "&date_to=2026-09-27" % probe, token)
            reports_ok = True
        except Exception:
            reports_ok = False
        if reports_ok:
            print("  Отчёты по собственному счётчику читаются, всё в порядке.")
            print("  Если счётчик сайта не в списке, закрывается только причина 1.")
        else:
            print("  Отчёты отдают 403 даже по счётчику, которым этот аккаунт")
            print("  владеет. Права на отчёты в токене нет.")
            if org:
                print("  Счётчики принадлежат организации %s." % org)
                print("  Право passport:business у приложения есть, проверено")
                print("  30 сентября: «Работа с организациями Яндекс ID» в")
                print("  выданных правах токена присутствует.")
                print()
                print("  Значит остаётся одно из двух:")
                print("  а) токен выдан раньше, чем это право появилось, и")
                print("     новые права в него не подставились. Отозвать токен")
                print("     на id.yandex.ru/personal/data-access и взять новый.")
                print("  б) аккаунт не входит в организацию %s либо не имеет" % org)
                print("     в ней прав на эти счётчики. Это решает владелец")
                print("     организации, то есть клиент.")
            else:
                print("  Нужно: проверить выданные токену права на")
                print("  id.yandex.ru/personal/data-access.")
        print()
        print("Итог: эти две причины независимы, закрывать нужно обе.")
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
    elif cmd == "paste" and len(args) > 1:
        sys.exit(cmd_paste(env, args[1]))
    elif cmd == "test":
        sys.exit(cmd_test(env))
    else:
        print("Использование:")
        print("  login                        всё сразу: ссылка, код, проверка")
        print("  auth-url [--scope=значение]  ссылка для входа")
        print("  exchange <код>               обменять код на токен")
        print("  paste <строка>               принять токен или адрес")
        print("                              и сразу проверить его")
        print("  test                         проверить токен и права")
        print()
        print("Для клиента нужна одна команда login. Остальное на случай, если")
        print("код нужен отдельно, например для выяснения, что пошло не так.")
        print()
        print("Без --scope ссылка не передаёт список прав, и токен получает все")
        print("права, объявленные у приложения. Это обычный режим.")
        sys.exit(2)
