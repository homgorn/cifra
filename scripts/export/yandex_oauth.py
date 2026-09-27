#!/usr/bin/env python3
"""Yandex OAuth для API Метрики и Вебмастера (ручной code-flow).

Секреты читаются ТОЛЬКО из корневого .env, токены туда же сохраняются.
Токены и секреты никогда не печатаются — только маски.

Команды (из корня проекта):
  python scripts/export/yandex_oauth.py auth-url
  python scripts/export/yandex_oauth.py exchange <код_со_страницы>
  python scripts/export/yandex_oauth.py test
"""
import os
import sys
import urllib.parse
import urllib.request
import json

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_PATH = os.path.join(ROOT, ".env")

AUTH_URL = "https://oauth.yandex.ru/authorize"
TOKEN_URL = "https://oauth.yandex.ru/token"
REDIRECT = "https://oauth.yandex.ru/verification_code"

# Права, которые запрашиваем явно. Полный набор прав API Вебмастера
# (внешние ссылки, webmaster:hostinfo) выдаётся в настройках приложения на
# oauth.yandex.ru, а здесь нужен только явный scope, чтобы токен их помнил.
SCOPES = "login:info,login:email"


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


def cmd_auth_url(env):
    cid = env.get("YANDEX_CLIENT_ID", "")
    if not cid:
        print("Нет YANDEX_CLIENT_ID в .env")
        return 1
    q = urllib.parse.urlencode({
        "response_type": "code",
        "client_id": cid,
        "redirect_uri": REDIRECT,
        "scope": SCOPES,
    })
    print("Откройте в браузере, подтвердите доступ, скопируйте код со страницы:")
    print(AUTH_URL + "?" + q)
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
        print("invalid_grant = код протух/использован; invalid_client = неверный secret.")
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
    print("Токен: %s" % mask(token))
    # Метрика: список счётчиков
    try:
        st, data = api_get("https://api-metrika.yandex.net/management/v1/counters", token)
        counters = data.get("counters", [])
        print("Метрика API: OK, счётчиков доступно: %d" % len(counters))
        for c in counters[:10]:
            print("  - %s : %s" % (c.get("id"), c.get("site", "?")))
    except Exception as e:
        print("Метрика API: НЕДОСТУПНА (%s) — проверьте права приложения." % e)
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
        print("Внешние ссылки: НЕТ прав. Требуется scope EXTERNAL_LINKS")
        print("  Что сделать: oauth.yandex.ru -> приложение -> Права доступа ->")
        print("  добавить «Получение информации о внешних ссылках на сайт», затем")
        print("  пройти auth-url -> exchange заново.")
    return 0


if __name__ == "__main__":
    env = load_env()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "auth-url"
    if cmd == "auth-url":
        sys.exit(cmd_auth_url(env))
    elif cmd == "exchange" and len(sys.argv) > 2:
        sys.exit(cmd_exchange(env, sys.argv[2]))
    elif cmd == "test":
        sys.exit(cmd_test(env))
    else:
        print("Использование: auth-url | exchange <код> | test")
        sys.exit(2)
