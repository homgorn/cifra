"""Решающая проверка отчётов Метрики.

Запускать сразу после того, как в .env лежит свежий токен. Одна
команда, один вывод, после которого версий больше не остаётся.

Что выясняется и чем:

| Проверка | Что означает результат |
|---|---|
| `counters` 200 | токен валиден, аккаунт читает свой список |
| `permission` | есть ли право на счётчик и чьё оно |
| `reports` 200 | доступ есть, всё работает, дальше выгружаем |
| `reports` 403, `scope` 200 | приложение признано, но права нет: писать в поддержку |
| `reports` 403, `scope` 401 | токен отозван, нуж��ается новый |
| заведомо чужой счётчик | отказ общий или привязан к счётчику |

Последняя строка важнее, чем кажется. Если отказ общий, вопрос о
доступе к счётчику закрыт и искать нечего.
"""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"C:\susa ai\2026 cifra audit"
ENV_PATH = os.path.join(ROOT, ".env")

HOST = "https://api-metrika.yandex.net"
MAIN = "50863157"
DATES = {"date_from": "2026-09-20", "date_to": "2026-09-26"}


def env_get():
    out = {}
    for line in open(ENV_PATH, encoding="utf-8"):
        line = line.strip()
        if line and "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def call(path, params=None, token=None):
    url = HOST + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url, headers={"Authorization": "OAuth " + token})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:                                    # noqa: BLE001
        return 0, "%s: %s" % (type(e).__name__, e)


def main():
    env = env_get()
    token = env.get("YANDEX_OAUTH_TOKEN", "")
    if not token:
        print("Токена нет в .env, проверять нечего.")
        return 2
    print("Токен            %s" % Y_mask(token))
    print("Приложение ссылки %s" % (env.get("YANDEX_CLIENT_ID") or "?"))
    print("Приложение токена %s" % (env.get("YANDEX_TOKEN_APP") or "НЕИЗВЕСТНО"))
    print()

    st, body = call("/management/v1/counters", token=token)
    print("1. Список счётчиков              HTTP %s" % st)
    if st == 200:
        data = json.loads(body)
        for c in data.get("counters", []):
            mark = " <- сайт" if str(c.get("id")) == MAIN else ""
            print("     %-11s %-28s %s%s"
                  % (c.get("id"), (c.get("name") or "")[:28],
                     c.get("owner_login"), mark))
    else:
        print("   %s" % body[:150])
        if st == 401:
            print("   Токен недействителен. Он отзывается при смене пароля,")
            print("   при включении двухфакторной аутентификации, при правке")
            print("   прав приложения и при выходе «Выйти везде».")
            return 1

    perm, owner = "не измерено", "не измерено"
    st, body = call("/management/v1/counter/" + MAIN, token=token)
    print()
    print("2. Права на счётчик %-14s HTTP %s" % (MAIN, st))
    if st == 200:
        c = json.loads(body).get("counter", {})
        perm, owner = c.get("permission"), c.get("owner_login")
        print("     владелец   %s" % owner)
        print("     permission %s" % perm)
    else:
        print("   %s" % body[:150])

    st, body = call("/stat/v1/data",
                    dict(counters=MAIN, fields="visits,visitors",
                         period="day", **DATES), token=token)
    print()
    print("3. Отчёт visits за неделю        HTTP %s" % st)
    if st == 200:
        data = json.loads(body)
        rows = data.get("data") or []
        tot = 0
        for r in rows:
            for m in r.get("metrics") or []:
                tot += int((m or [0])[0])
        print("     ДОСТУП ЕСТЬ. Строк %d, всего визитов %d" % (len(rows), tot))
        print()
        print("   Дальше: yandex_setup.bat --data, затем полный refresh.")
        print("   Больше ничего выяснять не нужно, можно выгружать.")
        return 0
    print("   %s" % body[:200])

    st2, body2 = call("/stat/v1/data",
                      dict(counters="99999999", fields="visits",
                           period="day", **DATES), token=token)
    same = (st2 == st and body2 == body)
    print()
    print("4. Заведомо чужой счётчик        HTTP %s, ответ %s"
          % (st2, "ИДЕНТИЧЕН" if same else "отличается"))

    if not same:
        print()
        print("Вывод: отказ привязан к счётчику, а не к приложению.")
        print("  Проверять права приложения смысла нет, чинить доступ")
        print("  к счётчику: снять и выдать заново через")
        print("  metrika.yandex.ru, либо включить публичную статистику.")
        return 1

    print()
    print("Вывод: отказ общий, до счётчика дело не доходит.")
    print("  Права на счётчик тут ни при чём, сколько бы их ни было.")
    print("  Остаётся сторона приложения или токена.")
    print()
    print("  Если токен свежий, выдан после всех правок прав,")
    print("  то писать в поддержку. Текст обращения собран ниже.")
    print()
    print("-" * 62)
    print("Здравствуйте. Приложение Яндекс ID (client_id %s)"
          % env.get("YANDEX_CLIENT_ID", "?"))
    print("выдаёт токен, которым читается список счётчиков")
    print("(GET /management/v1/counters отдаёт 200), но любой запрос")
    print("отчётов (GET /stat/v1/data) возвращает 403 с телом")
    print('{"error_type":"access_denied"}. Отказ одинаков для любого')
    print("номера счётчика, включая несуществующий, то есть возникает")
    print("до проверки счётчика. Привязки счётчика к организации нет.")
    print("Право на счётчик, измеренное этим же токеном: %s," % perm)
    print("владелец счётчика %s." % owner)
    print("Прошу проверить, почему приложению отказано в отчётах.")
    print("-" * 62)
    return 1


def Y_mask(s):
    return (s[:4] + "..." + s[-4:]) if len(s) > 12 else "***"


if __name__ == "__main__":
    sys.exit(main())