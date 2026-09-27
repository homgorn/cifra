#!/usr/bin/env python3
"""Офлайн-вендоринг Chart.js: локальная копия + CDN-fallback.

Заменяет во всех 22 html:
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
на:
  <script src="{prefix}js/vendor/chart.umd.min.js"></script>
  <script>if(typeof Chart==="undefined"){document.write(...)}</script>  (CDN fallback)

Идемпотентен: повторный запуск ничего не меняет.
Запуск из корня проекта: python scripts/export/vendor_charts.py
"""
import glob
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SITE = os.path.join(ROOT, "reports", "cifra18-audit")
VENDOR = os.path.join(SITE, "js", "vendor", "chart.umd.min.js")
CDN = "https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"

if not os.path.isfile(VENDOR):
    print("Нет vendor-файла: %s — сначала скачайте Chart.js 4.4.1" % VENDOR)
    sys.exit(1)
with open(VENDOR, "r", encoding="utf-8") as f:
    head = f.read(200)
if "chart.js" not in head.lower():
    print("Vendor-файл не похож на Chart.js, остановка")
    sys.exit(1)

OLD = '<script src="%s"></script>' % CDN


def replacement(prefix):
    local = '<script src="%sjs/vendor/chart.umd.min.js"></script>' % prefix
    fb_open = "<script>"
    fb_code = 'if(typeof Chart==="undefined"){document.write('
    fb_arg = '"<script src=' + chr(39) + CDN + chr(39) + '><\\/script>")}'
    fb_close = "</" + "script>"
    return local + "\n" + fb_open + fb_code + fb_arg + fb_close


changed, skipped = 0, 0
files = [os.path.join(SITE, "index.html")]
files += sorted(glob.glob(os.path.join(SITE, "pages", "*.html")))
for path in files:
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    if "js/vendor/chart.umd.min.js" in html:
        skipped += 1
        continue
    n = html.count(OLD)
    if n != 1:
        print("SKIP (%d совпадений CDN-тега): %s" % (n, os.path.relpath(path, SITE)))
        continue
    prefix = "" if os.path.basename(path) == "index.html" else "../"
    html = html.replace(OLD, replacement(prefix), 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    changed += 1
    print("ok: %s" % os.path.relpath(path, SITE))

print("---\nИзменено: %d, уже с вендором: %d" % (changed, skipped))
