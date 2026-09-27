#!/usr/bin/env python3
"""Сборка Cloudflare Worker, раздающего сайт отчёта cifra18-audit.

Сканирует reports/cifra18-audit (index.html, pages/*.html, css/*, js/*),
генерирует reports/cifra18-audit-worker.js со встроенными ассетами.
Роуты на страницу: /x, /x.html, /pages/x.html (+ / для главной).

Запуск из корня проекта: python scripts/export/build_report_worker.py
Лимит Cloudflare Workers (free): 1 MiB на скрипт — скрипт проверяет вес.
"""
import glob
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE = os.path.join(ROOT, "reports", "cifra18-audit")
OUT = os.path.join(ROOT, "reports", "cifra18-audit-worker.js")
WORKER_LIMIT = 1024 * 1024  # 1 MiB, free-план Cloudflare Workers

MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
}

files = ["index.html"]
files += sorted(
    os.path.relpath(p, BASE).replace(os.sep, "/")
    for p in glob.glob(os.path.join(BASE, "pages", "*.html")))
files += ["css/main.css", "css/report.css", "js/main.js", "js/wm-data.js",
          "js/site-data.js", "js/vendor/chart.umd.min.js"]

missing = [f for f in files if not os.path.isfile(os.path.join(BASE, f))]
if missing:
    print("Нет файлов: %s" % missing)
    sys.exit(1)

ROUTES = {
    "/": "index.html",
    "/index.html": "index.html",
    "/css/main.css": "css/main.css",
    "/css/report.css": "css/report.css",
    "/js/main.js": "js/main.js",
    "/js/wm-data.js": "js/wm-data.js",
    "/js/site-data.js": "js/site-data.js",
    "/js/vendor/chart.umd.min.js": "js/vendor/chart.umd.min.js",
}
for rel in files:
    if not rel.endswith(".html") or rel == "index.html":
        continue
    if rel.startswith("pages/"):
        name = rel[len("pages/"):-len(".html")]
        ROUTES["/" + name] = rel
        ROUTES["/" + name + ".html"] = rel
        ROUTES["/" + rel] = rel

assets = {}
for rel in sorted(set(ROUTES.values())):
    with open(os.path.join(BASE, rel), "r", encoding="utf-8") as f:
        assets[rel] = f.read()

print("Файлов: %d, роутов: %d" % (len(assets), len(ROUTES)))

assets_json = json.dumps(assets, ensure_ascii=False)
routes_json = json.dumps(ROUTES, ensure_ascii=False)

worker = """const ASSETS = %s;
const ROUTES = %s;

function mime(path) {
  if (path.endsWith('.css')) return 'text/css; charset=utf-8';
  if (path.endsWith('.js')) return 'text/javascript; charset=utf-8';
  if (path.endsWith('.json')) return 'application/json; charset=utf-8';
  if (path.endsWith('.svg')) return 'image/svg+xml';
  if (path.endsWith('.png')) return 'image/png';
  return 'text/html; charset=utf-8';
}

export default {
  async fetch(request) {
    const url = new URL(request.url);
    let path = url.pathname;
    if (path.length > 1 && path.endsWith('/')) path = path.slice(0, -1);
    const file = ROUTES[path] || ROUTES[path + '.html'];
    if (!file || !(file in ASSETS)) {
      return new Response('Страница не найдена. Вернитесь на главную: /', {
        status: 404,
        headers: { 'content-type': 'text/plain; charset=utf-8' },
      });
    }
    return new Response(ASSETS[file], {
      headers: {
        'content-type': mime(file),
        'cache-control': 'public, max-age=3600',
        'x-report': 'cifra18-audit-2026-09',
      },
    });
  },
};
""" % (assets_json, routes_json)

with open(OUT, "w", encoding="utf-8") as f:
    f.write(worker)

size = os.path.getsize(OUT)
print("Записан %s (%.1f КБ)" % (OUT, size / 1024))
if size > WORKER_LIMIT:
    print("ОШИБКА: больше лимита Workers free (1 MiB)")
    sys.exit(1)
print("Вес в лимите: %.1f%% от 1 MiB" % (size / WORKER_LIMIT * 100))
