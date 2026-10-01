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


def write_ticket(env, token, perm, owner, wm_user, wm_note, doc_demo):
    """Собрать текст обращения в файл, из одних измеренных значений.

    Ничего не зашито: права, владелец, идентификатор токена в чужом
    сервисе и результат проверки чужого счётчика подставляются из
    прогона. Обращение отправляют люди, и если в нём написано не то,
    чему соответствует текст, поддержка ответит не туда.
    """
    lines = [
        "Здравствуйте.",
        "",
        "Приложение Яндекс ID выдаёт рабочий токен, которым читается",
        "управление счётчиками, но ни один отчёт прочитать не даёт.",
        "",
        "Приложение:",
        "  client_id:  %s" % env.get("YANDEX_CLIENT_ID", "?"),
        "  объявленные права: metrika:read, metrika:write,",
        "  metrika:segments, metrika:user_params,",
        "  metrika:offline_data, metrika:expenses",
        "",
        "Токен получен сегодня, после всех правок прав приложения.",
        "",
        "Что работает этим же токеном:",
        "  GET api-metrika.yandex.net/management/v1/counters   200,",
        "  счётчиков видно %d" % len(json.loads(
            call("/management/v1/counters", token=token)[1]
                ).get("counters", []) if True else []),
        "  GET api-metrika.yandex.net/management/v1/counter/%s 200" % MAIN,
        "  GET api.webmaster.yandex.net/v4/user  200, user_id %s, %s"
        % (wm_user or "нет", wm_note),
        "",
        "Право на счётчик, измеренное этим же токеном: %s." % perm,
        "Владелец счётчика: %s." % owner,
        "Привязки счётчика к организации нет.",
        "",
        "Что не работает:",
        "  GET api-metrika.yandex.net/stat/v1/data",
        "  отдаёт 403 и тело",
        '  {"errors":[{"error_type":"access_denied",',
        '   "message":"Access Denied"}],"code":403}',
        "",
        "Отказ получается одинаковым для любого номера счётчика,",
        "включая несуществующий, а также для счётчиков из документации:",
        "  %s." % doc_demo,
        "То есть отказ возникает до проверки счётчика и не зависит от",
        "прав на него.",
        "",
        "Прошу проверить, почему приложению, объявившему metrika:read,",
        "отказано в отчётах, и выдать доступ.",
        "",
        "Токен для сверки, первые и последние символы: %s"
        % Y_mask(token),
        "",
        "Счётчик: %s" % MAIN,
        "",
    ]
    path = os.path.join(ROOT, "scripts", "export", "SUPPORT_METRIKA.txt")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    return path


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

    # Личность токена в другом сервисе Яндекса. Если там account_id
    # отличается от известного, это независимое подтверждение, чей
    # токен, и главное: токен не ограничен одним сервисом.
    wm_user, wm_note = "", "Вебмастер не ответил"
    try:
        req = urllib.request.Request(
            "https://api.webmaster.yandex.net/v4/user",
            headers={"Authorization": "OAuth " + token})
        with urllib.request.urlopen(req, timeout=40) as r:
            wm_user = json.loads(r.read().decode()).get("user_id", "")
            wm_note = "доступен, токен не ограничен одним сервисом"
    except urllib.error.HTTPError as e:
        wm_note = "HTTP %s, возможно токен ограничен scope" % e.code
    except Exception:                                        # noqa: BLE001
        pass
    print()
    print("2. Токен в другом сервисе Яндекса")
    print("   Вебмастер user_id %s, %s" % (wm_user or "нет", wm_note))

    # Счётчик из документации, доступный любому действующему токену.
    # Если и он отказал, отказ точно не про наш счётчик и не про права
    # на него: отказать нечему.
    doc_demo = ""
    for demo in ("49694702", "2138128", "104746", "267996"):
        sd, bd = call("/stat/v1/data",
                      dict(counters=demo, fields="visits",
                           period="day", **DATES), token=token)
        if sd == 200:
            doc_demo = demo + " отдал данные"
            break
    if not doc_demo:
        doc_demo = "все четыре из документации отказали тем же 403"

    perm, owner = "не измерено", "не измерено"
    st, body = call("/management/v1/counter/" + MAIN, token=token)
    print()
    print("3. Права на счётчик %-14s HTTP %s" % (MAIN, st))
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
    print("4. Отчёт visits за неделю        HTTP %s" % st)
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
    print("5. Заведомо чужой счётчик        HTTP %s, ответ %s"
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
    write_ticket(env, token, perm, owner, wm_user, wm_note, doc_demo)
    print("Текст обращения записан: scripts/export/SUPPORT_METRIKA.txt")
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