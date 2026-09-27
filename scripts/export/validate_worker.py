#!/usr/bin/env python3
"""Smoke-тест собранного воркера reports/cifra18-audit-worker.js.

Проверяет без деплоя:
 1. ROUTES/ASSETS парсятся, все цели роутов есть в ASSETS;
 2. каждый html-ассет содержит <title> (не битый);
 3. эмуляция логики fetch: все ожидаемые URL (/, /x, /x.html, /pages/x.html)
     для каждой страницы резолвятся; мусорный URL даёт 404;
 4. вес файла в лимите Workers free (1 MiB).

Запуск из корня проекта: python scripts/export/validate_worker.py
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORKER = os.path.join(ROOT, "reports", "cifra18-audit-worker.js")
SITE = os.path.join(ROOT, "reports", "cifra18-audit")
LIMIT = 1024 * 1024

fails = []


def fail(msg):
    fails.append(msg)
    print("FAIL: " + msg)


with open(WORKER, "r", encoding="utf-8") as f:
    src = f.read()

m = re.search(r"const ASSETS = (\{.*?\});\nconst ROUTES = ", src, re.DOTALL)
m2 = re.search(r"\nconst ROUTES = (\{.*?\});\n", src, re.DOTALL)
if not m or not m2:
    print("FAIL: не найдены ASSETS/ROUTES в воркере")
    sys.exit(1)
assets = json.loads(m.group(1))
routes = json.loads(m2.group(1))
print("ok: ассетов %d, роутов %d" % (len(assets), len(routes)))

# 1. все цели на месте
dangling = [r for r, t in routes.items() if t not in assets]
if dangling:
    fail("висячие роуты: %s" % dangling)
else:
    print("ok: все роуты ведут на существующие ассеты")

# 2. html не битые
bad = [k for k, v in assets.items()
       if k.endswith(".html") and "<title>" not in v]
if bad:
    fail("html без <title>: %s" % bad)
else:
    print("ok: все %d html с <title>" % sum(1 for k in assets if k.endswith(".html")))

# 3. эмуляция fetch


def resolve(path):
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]
    f = routes.get(path) or routes.get(path + ".html")
    if not f or f not in assets:
        return 404
    return 200


checked, bad = 0, []
pages = ["index.html"] + sorted(
    os.path.basename(p) for p in
    __import__("glob").glob(os.path.join(SITE, "pages", "*.html")))
expect = [("/", 200), ("/index.html", 200)]
for pg in pages:
    if pg == "index.html":
        continue
    name = pg[:-len(".html")]
    expect += [("/" + name, 200), ("/" + name + ".html", 200),
               ("/pages/" + pg, 200), ("/" + name + "/", 200)]
expect += [("/no-such-page", 404), ("/pages/nope.html", 404)]
for url, want in expect:
    checked += 1
    got = resolve(url)
    if got != want:
        bad.append("%s: ждали %d, получили %d" % (url, want, got))
if bad:
    fail("роутинг: %s" % bad[:10])
else:
    print("ok: роутинг %d URL (включая 404-кейсы)" % checked)

# 4. вес
size = os.path.getsize(WORKER)
print("Вес воркера: %.1f КБ (%.1f%% лимита)" % (size / 1024, size / LIMIT * 100))
if size > LIMIT:
    fail("превышен лимит 1 MiB")

print("---")
if fails:
    print("WORKER SMOKE FAILED: %d" % len(fails))
    sys.exit(1)
print("WORKER SMOKE PASSED")
