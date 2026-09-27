#!/usr/bin/env python3
"""Validate the cifra18 audit report site (reports/cifra18-audit).

Checks:
 1. all expected files exist (22 html + css/js)
 2. no em-dash anywhere in report html/js
 3. title + h1 + meta description on every page
 4. every <canvas id> has mk('id') in main.js and vice versa
 5. internal .html links resolve to files; #anchors resolve to ids
 6. forbidden tokens (name, 1st person, Google) with methodology allowlist
 7. Вебмастер dropdown present in every nav; footer 'из 22'; kicker coverage 1-22
 8. local HTTP server returns 200 for every page/asset
 9. node smoke test for charts/tables passes
Exit code 0 = all green, 1 = failures (listed).
"""
import os
import re
import subprocess
import sys
import threading
import urllib.request
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SITE = os.path.join(ROOT, "reports", "cifra18-audit")
PAGES = os.path.join(SITE, "pages")

fails = []


def fail(msg):
    fails.append(msg)
    print("FAIL: " + msg)


def ok(msg):
    print("ok: " + msg)


EXPECTED_PAGES = ["index.html"] + sorted(
    ["technical.html", "content.html", "competitors.html", "local.html", "geo.html",
     "knowledge.html", "roadmap.html", "prices.html", "season.html", "marketing.html",
     "methodology.html", "wm-overview.html", "wm-indexing.html", "wm-duplicates.html",
     "wm-errors.html", "wm-redirects.html", "wm-queries.html", "wm-clusters.html",
     "wm-gaps.html", "wm-links.html", "wm-plan.html",
     "dash-visibility.html", "dash-audience.html", "dash-money.html", "dash-maps.html",
     "plan-3m.html"])
TOTAL_PAGES = len(EXPECTED_PAGES)

# 1. files exist
missing = []
for p in EXPECTED_PAGES:
    full = os.path.join(SITE, p) if p == "index.html" else os.path.join(PAGES, p)
    if not os.path.isfile(full):
        missing.append(p)
for asset in ["css/main.css", "css/report.css", "css/nav.css", "js/main.js", "js/nav.js",
              "js/search.js", "js/page-index.js", "js/wm-data.js", "js/site-data.js",
              "js/dash-data.js", "js/vendor/chart.umd.min.js"]:
    if not os.path.isfile(os.path.join(SITE, asset)):
        missing.append(asset)
if missing:
    fail("missing files: %s" % missing)
else:
    ok("%d html + 11 assets present" % TOTAL_PAGES)


def read(p):
    with open(p, "r", encoding="utf-8") as f:
        return f.read()


def page_path(p):
    return os.path.join(SITE, p) if p == "index.html" else os.path.join(PAGES, p)


html = {p: read(page_path(p)) for p in EXPECTED_PAGES}
main_js = read(os.path.join(SITE, "js", "main.js"))

# 2. em-dash
emd = [p for p, h in html.items() if "\u2014" in h]
if "\u2014" in main_js:
    emd.append("js/main.js")
if emd:
    fail("em-dash found in: %s" % emd)
else:
    ok("no em-dash")

# 3. title/h1/meta
for p, h in html.items():
    if not re.search(r"<title>[^<]{5,}</title>", h):
        fail("no title: %s" % p)
    if "<h1>" not in h:
        fail("no h1: %s" % p)
    m = re.search(r'<meta name="description" content="([^"]*)"', h)
    if not m or len(m.group(1)) < 20:
        fail("weak meta description: %s" % p)
ok("title/h1/meta pass (see fails above if any)")

# 4. canvas <-> mk()
canvas_ids = set()
for p, h in html.items():
    canvas_ids.update(re.findall(r'<canvas id="([^"]+)"', h))
mk_ids = set(re.findall(r"mk\('([^']+)'", main_js))
if canvas_ids - mk_ids:
    fail("canvas without mk(): %s" % sorted(canvas_ids - mk_ids))
if mk_ids - canvas_ids:
    fail("mk() without canvas: %s" % sorted(mk_ids - canvas_ids))
if not (canvas_ids - mk_ids or mk_ids - canvas_ids):
    ok("canvas<->mk 1:1 (%d)" % len(canvas_ids))

# 5. links resolve
existing = set()
for p in EXPECTED_PAGES:
    existing.add(p)
    existing.add("pages/" + p if p != "index.html" else "index.html")
file_ids = {}
for p, h in html.items():
    file_ids[p] = set(re.findall(r'id="([^"]+)"', h))
for p, h in html.items():
    base = "" if p == "index.html" else "pages/"
    for m in re.finditer(r'href="([^"#]+?\.html)(#[^"]*)?"', h):
        target = m.group(1)
        if target.startswith("http"):
            continue
        norm = os.path.normpath(os.path.join(base, target)).replace("\\", "/")
        if norm not in existing and norm != "index.html":
            fail("broken page link %s -> %s" % (p, target))
    for m in re.finditer(r'href="#([^"]+)"', h):
        if m.group(1) not in file_ids[p]:
            fail("broken anchor %s -> #%s" % (p, m.group(1)))
ok("links/anchors pass (see fails above if any)")

# 6. forbidden tokens
ALLOW_GOOGLE_FILE = "methodology.html"
tokens = ["Константин", "Search Console", "Что я ", "Моя оценка", "Проверял и писал",
          "перепроверю", "Что я видел", " и Google", "Google и ", "Google-Extended",
          "валидаторами Google", "Я два вечера", "Ниже показываю", "Собрал ядро", "Делю на три"]
for p, h in html.items():
    for t in tokens:
        if t in h and not (p == ALLOW_GOOGLE_FILE and t in (" и Google", "Search Console")):
            fail("forbidden token '%s' in %s" % (t, p))
ok("tokens pass (see fails above if any)")

# 7. nav/footer/numbering
NAV_SECTIONS = ["Резюме", "Вебмастер", "Дашборды", "Анализ", "План", "Методика"]
footer_slugs = set()
for p, h in html.items():
    nav = h.split("</nav>")[0]
    if "nav-dropdown" in h or 'id="menuBtn"' in h:
        fail("выпадающий список остался в: %s" % p)
    for s in NAV_SECTIONS:
        if ">%s<" % s not in nav:
            fail("нет пункта '%s' в меню: %s" % (s, p))
    if "nav-link-all" not in nav:
        fail("нет ссылки «Все страницы»: %s" % p)
    if "css/nav.css" not in h or "js/nav.js" not in h or "js/search.js" not in h:
        fail("не подключены nav.css, nav.js или search.js: %s" % p)
    if re.search(r"Страница \d+ из (22|12|23|26)\b", h):
        fail("stale numbering in: %s" % p)
    foot = h.split("</footer>")[0]
    for m in re.finditer(r'<footer class="site-footer">.*?</footer>', h, re.DOTALL):
        for href in re.findall(r'href="([^"#]+?\.html)"', m.group(0)):
            base = "" if p == "index.html" else "pages/"
            slug = os.path.normpath(os.path.join(base, href)).replace("\\", "/")
            footer_slugs.add(slug)

expect_slugs = {"index.html"} | {"pages/" + p for p in EXPECTED_PAGES if p != "index.html"}
if footer_slugs != expect_slugs:
    only_footer = sorted(footer_slugs - expect_slugs)
    only_pages = sorted(expect_slugs - footer_slugs)
    fail("футер не совпадает со списком страниц: лишнее %s, нет %s" % (only_footer, only_pages))
else:
    ok("в футере все %d страниц" % len(expect_slugs))

# подшапка: есть в разделах, нет на главной и методике
for p, h in html.items():
    has_sub = 'class="subnav"' in h
    should = p not in ("index.html", "methodology.html")
    if has_sub != should:
        fail("подшапка %s там, где её быть не должно: %s" % ("есть" if has_sub else "нет", p))
if 'id="toc"' not in html.get("index.html", ""):
    fail("на главной нет карты отчёта")
elif html["index.html"].count('class="toc-card"') < 20:
    fail("карта отчёта на главной собрана не полностью")
else:
    ok("карта отчёта на главной: %d карточек" % html["index.html"].count('class="toc-card"'))
nums = {}
for p, h in html.items():
    m = re.search(r"Страница (\d+) из %d" % TOTAL_PAGES, h)
    if not m:
        fail("no page number: %s" % p)
    else:
        nums.setdefault(int(m.group(1)), []).append(p)
dupes = {k: v for k, v in nums.items() if len(v) > 1}
if dupes:
    fail("duplicate page numbers: %s" % dupes)
missing_nums = [n for n in range(1, TOTAL_PAGES + 1) if n not in nums]
if missing_nums:
    fail("missing page numbers: %s" % missing_nums)
if not dupes and not missing_nums:
    ok("numbering 1-%d contiguous, nav+footer everywhere" % TOTAL_PAGES)

# 8. local server 200
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Quiet, directory=SITE))
port = server.server_address[1]
t = threading.Thread(target=server.serve_forever, daemon=True)
t.start()
bad = []
urls = ["index.html", "css/main.css", "css/report.css", "css/nav.css", "js/main.js",
        "js/nav.js", "js/search.js", "js/page-index.js", "js/wm-data.js",
        "js/site-data.js", "js/dash-data.js", "js/vendor/chart.umd.min.js"]
urls += ["pages/" + p for p in EXPECTED_PAGES if p != "index.html"]
for u in urls:
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d/%s" % (port, u), timeout=10) as r:
            if r.status != 200:
                bad.append("%s -> %s" % (u, r.status))
    except Exception as e:
        bad.append("%s -> %s" % (u, e))
server.shutdown()
if bad:
    fail("non-200 urls: %s" % bad)
else:
    ok("local server 200 for %d urls" % len(urls))

# 9. node smoke test
r = subprocess.run(["node", "scripts/export/smoke_wm_js.js"], cwd=ROOT,
                   capture_output=True, text=True)
print(r.stdout.strip())
if r.returncode != 0:
    fail("node smoke test failed: %s" % r.stderr.strip()[-500:])
else:
    ok("node smoke test green")

# 10. тема и контраст
r = subprocess.run([sys.executable, "scripts/export/validate_theme.py"], cwd=ROOT,
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
if r.returncode != 0:
    fail("theme validation failed: %s" % (r.stdout or "").strip()[-400:])
else:
    ok("theme: one scheme, tokens only, contrast in range")

# 11. раскладка и графики в браузере. Без этого гейта страница может
# пройти все проверки и выглядеть разобранной: канвасы 300x150, полосы
# наезжают, элементы уехали из колонки. Видно только рендером.
r = subprocess.run([sys.executable, "scripts/export/check_layout.py"], cwd=ROOT,
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
last = [ln for ln in (r.stdout or "").splitlines() if ln.strip()]
if r.returncode != 0:
    fail("layout failed in browser: %s"
         % " | ".join([ln.strip() for ln in last if "FAIL" in ln or "LAYOUT" in ln][:4]))
else:
    ok("layout: canvases sized, no overflow, no JS errors, both schemes")

print("---")
if fails:
    print("VALIDATION FAILED: %d problem(s)" % len(fails))
    sys.exit(1)
print("VALIDATION PASSED: all green")
