#!/usr/bin/env python3
"""Validate the cifra18 audit report site (reports/cifra18-audit).

Checks:
 1. all expected files exist (27 html + css/js)
 2. no em-dash in shipped html/js, CLIENT_REPORT.md and the wiki
 3. title + h1 + meta description on every page
 4. every <canvas id> has mk('id') in main.js and vice versa
 5. internal .html links resolve to files; #anchors resolve to ids
 6. forbidden tokens (name, 1st person, Google) with methodology allowlist
 7. nav/footer present everywhere, footer lists all 27, numbering 1-27
 8. local HTTP server returns 200 for every page/asset
 9. node smoke test for charts/tables passes
10. theme: one scheme, tokens only, contrast in range
11. layout in a real browser: canvas sizes, overflow, JS errors
12. numbers in client docs match facts from data
13. client report blocks are generated, not hand-typed
14. Russian pluralisation helper is not inverted
 16. no unescaped percent signs in page text
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


# Список страниц берётся из build_nav.py, а не из файлов на диске.
#
# Почему не из диска. Тогда любая забытая страница прошла бы проверку
# молча: она лежит в папке, значит существует, значит на неё можно
# ссылаться. Ровно это и произошло с четырьмя новыми страницами: они
# собраны и лежат на диске, но не были в списке, и все ссылки на них
# из двадцати девяти страниц отчитались битыми.
#
# Почему из build_nav.py. Это единственный список, который что-то
# значит: из него собираются меню, подвал, нумерация и индекс поиска.
# Если страницы нет в нём, на неё нельзя перейти и она не находится
# поиском, то есть существовать ей незачем.
EXPECTED_PAGES = None
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import build_nav
    # Список build_nav содержит пути от корня сайта, «pages/wm-plan.html»,
    # а проверка ниже строит путь сама через page_path(), который уже
    # добавляет папку pages. Поэтому префикс убирается здесь, иначе
    # получается pages/pages/wm-plan.html.
    EXPECTED_PAGES = sorted(
        slug[len("pages/"):] if slug.startswith("pages/") else slug
        for _n, slug, _s, _d in build_nav.REGISTRY)
except Exception as _exc:
    raise SystemExit("не удалось прочитать список страниц из build_nav.py: %s"
                     % _exc)
if not EXPECTED_PAGES:
    raise SystemExit("build_nav.py вернул пустой список страниц")
TOTAL_PAGES = len(EXPECTED_PAGES)

# Папки вики, файлы из которых клиент получает как приложение к отчёту.
# Именно они обязаны быть чистыми от em-dash, см. проверку 2.
CLIENT_WIKI_DIRS = {"webmaster_analytics", "metrika_analytics"}

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

# 2. em-dash. Проверялось раньше только main.js, и знак проехал в
# site-data.js, который собирается отдельным скриптом. Список файлов
# берётся с диска, новый js не может добавиться незамеченным.
#
# Порог. Жёстко проверяется всё, что читается как текст: сайт,
# CLIENT_REPORT.md и вики. Три строки в вики содержат знак как часть
# формулировки самого правила, «Fix em-dash (—) → comma», их замена
# сделала бы правило бессмысленным, поэтому они разрешены явно.
#
# Раньше вики считалась, но не блокировала. На практике это 1240 знаков
# в 73 файлах, из них 260 в таблицах, где тире вместо пустой ячейки
# делает таблицу нечитаемой. Правка сделана редакторским проходом,
# fix_em_dash.py разбирает роль тире по месту, гейт следит, чтобы новые
# не вернулись.
# chr(), а не "\u2014" в исходнике. Литерал в коде оказался шестью
# символами \, u, 2, 0, 1, 4, проверка искала их в тексте, не
# находила никогда и была зелёной всегда. Гейт, который не может
# сработать, хуже отсутствующего: он создаёт ощущение проверки.
EMDASH = chr(0x2014)
MENTION = ("em-dash", "em dash", chr(0x442) + chr(0x438) + chr(0x440) + chr(0x435))
assert EMDASH == "\u2014", "EM-DASH константа сломана"
shipped = []
for dirpath, _dirnames, filenames in os.walk(SITE):
    if "_qa" in dirpath or "vendor" in dirpath:
        continue
    for fn in filenames:
        if fn.endswith((".html", ".js", ".css")):
            shipped.append(os.path.join(dirpath, fn))
shipped.sort()
emd = [os.path.relpath(f, ROOT) for f in shipped if EMDASH in read(f)]
report_md = os.path.join(ROOT, "CLIENT_REPORT.md")
if EMDASH in read(report_md):
    emd.append("CLIENT_REPORT.md")

WIKI = os.path.join(ROOT, "brain", "wiki")
for dirpath, _d, filenames in os.walk(WIKI):
    if "__pycache__" in dirpath:
        continue
    for fn in sorted(filenames):
        if not fn.endswith(".md"):
            continue
        p = os.path.join(dirpath, fn)
        for ln, line in enumerate(read(p).split("\n"), 1):
            if EMDASH in line and not any(m in line.lower() for m in MENTION):
                emd.append("%s:%d" % (os.path.relpath(p, ROOT), ln))

if emd:
    fail("em-dash in %d place(s): %s" % (len(emd), emd[:12]))
else:
    ok("no em-dash in %d shipped files, CLIENT_REPORT.md and wiki" % len(shipped))

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
    # Номер страницы берётся из реестра build_nav. Раньше здесь стоял
    # перечень из четырёх чисел, «из 22», «из 12», «из 23», «из 26»:
    # проверка ловила устаревшую нумерацию только для тех значений,
    # которые кто-то успел посмотреть, и молча пропускала все
    # остальные.
    _nslug = p if p == "index.html" else "pages/" + p
    _pnum = build_nav.BY_SLUG[_nslug][0]
    if re.search(r"Страница \d+ из \d+\b", h) and \
            ("Страница %d из %d" % (_pnum, TOTAL_PAGES)) not in h:
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
    # Правило берётся из build_nav: подшапка ставится разделу, который
    # перечислен в SUBBAR_SECTIONS и в котором больше одной страницы.
    # Раньше здесь стояло «кроме главной и методики», то есть перечень
    # страниц-исключений, а не правило. Он совпадал с реальностью,
    # пока в методике была одна страница, и перестал сразу, как
    # появилась вторая.
    _slug = p if p == "index.html" else "pages/" + p
    _grp = build_nav.section_of(_slug)
    _cnt = sum(1 for _n, _s, _g, _d in build_nav.REGISTRY if _g == _grp
               and _s != "index.html")
    should = _grp in build_nav.SUBBAR_SECTIONS and _cnt >= 2
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

# 11b. Правила разбора ручных выгрузок Метрики. Проверки на данных
# которые когда-то ломались: разные периоды в одной папке, неизвестный
# период, доля одинаковых чисел, разбор чисел с неразрывным пробелом.
# Без них правки в разборщике выглядят рабочими, пока не попадут в
# отчёт.
r = subprocess.run([sys.executable, "scripts/export/test_metrika_manual.py"],
                   cwd=ROOT, capture_output=True, text=True,
                   encoding="utf-8", errors="replace")
if r.returncode != 0:
    fail("metrika manual rules failed: %s"
         % " | ".join([ln.strip() for ln in (r.stdout or "").splitlines()
                       if "НЕ ПРОЙДЕНО" in ln or "НЕ ПРОШЛИ" in ln][:4]))
else:
    ok("metrika manual: periods, duplicates, numbers, kinds")

# 12. числа в документах совпадают с фактами из данных
r = subprocess.run([sys.executable, "scripts/export/sync_cluster_counts.py", "--check"],
                   cwd=ROOT, capture_output=True, text=True,
                   encoding="utf-8", errors="replace")
if r.returncode != 0:
    fail("stale numbers in docs: %s"
         % " | ".join([ln.strip() for ln in (r.stdout or "").splitlines()
                       if ln.startswith("FAIL")][:2]))
else:
    ok("doc counts: numbers match facts from data")

# 13. блоки клиентского отчёта собраны скриптом, а не вписаны руками.
# Проверяется не текст, а способ его получения: если блок разошёлся с
# данными, пересобери скриптом, иначе он так и останется врать.
r = subprocess.run([sys.executable, "scripts/export/build_client_report.py", "--check"],
                   cwd=ROOT, capture_output=True, text=True,
                   encoding="utf-8", errors="replace")
if r.returncode != 0:
    fail("client report out of sync: %s"
         % " | ".join([ln.strip() for ln in (r.stdout or "").splitlines()
                       if ln.startswith("FAIL")][:3]))
else:
    ok("client report: blocks generated from data, no em-dash")

# 14. склонение по числу. Функция печатает текст клиенту и не падает при
# ошибке, поэтому проверяется таблицей, а не вызовом на одном числе.
sys.path.insert(0, os.path.join(ROOT, "scripts", "export"))
try:
    import facts as _facts
    cases = {1: "запрос", 2: "запроса", 4: "запроса", 5: "запросов",
             11: "запросов", 12: "запросов", 14: "запросов", 21: "запрос",
             22: "запроса", 25: "запросов", 53: "запроса", 111: "запросов",
             492: "запроса", 535: "запросов"}
    wrong = {n: _facts.plural(n, "запрос", "запроса", "запросов")
             for n, want in cases.items()
             if _facts.plural(n, "запрос", "запроса", "запросов") != want}
    if wrong:
        fail("plural() is wrong: %s" % wrong)
    else:
        ok("plural: 14 cases correct")
finally:
    pass

# 15. счётчик Метрики в данных совпадает со счётчиком сайта. Путаница
# между сайтом и карточкой в Яндекс Картах уже случалась дважды: сначала
# в тексте отчёта, потом в самих данных, где metrikaVisits был 79 002 от
# карточки. Здесь проверяется идентификатор, а не значение: значение
# меняется каждый день, а счётчик не должен меняться никогда.
env = {}
if os.path.isfile(os.path.join(ROOT, ".env")):
    for ln in open(os.path.join(ROOT, ".env"), encoding="utf-8"):
        ln = ln.strip()
        if ln and not ln.startswith("#") and "=" in ln:
            k, v = ln.split("=", 1)
            env[k.strip()] = v.strip()
want_counter = env.get("METRIKA_COUNTER_ID", "")
maps_counter = env.get("METRIKA_MAPS_COUNTER_ID", "")
site_data = os.path.join(SITE, "js", "site-data.js")
if want_counter and os.path.isfile(site_data):
    sd = read(site_data)
    m = re.search(r'"metrikaCounter"\s*:\s*"?(\d+)"?', sd)
    got = m.group(1) if m else ""
    if got == maps_counter:
        fail("site-data.js built from the Maps card counter %s, not the site %s"
             % (got, want_counter))
    elif got != want_counter:
        fail("site-data.js has no verified site counter "
             "(found %r, expected %s)" % (got or "nothing", want_counter))
    else:
        ok("metrika counter is the site counter %s" % got)
else:
    print("skip: METRIKA_COUNTER_ID not set in .env, counter not verified")

# 16. В собранных страницах не должно быть незакрытых «%%». Строка с
# «60%%» в шаблоне, который не проходит через %-форматирование, попадает
# в страницу буквально, и это видно только глазами на отрендеренной
# странице, но ловится текстом за секунду.
pct = [p for p, h in html.items() if "%%" in h]
if pct:
    fail("unescaped %% in: %s" % pct)
else:
    ok("no unescaped %% in page text")

print("---")
if fails:
    print("VALIDATION FAILED: %d problem(s)" % len(fails))
    sys.exit(1)
print("VALIDATION PASSED: all green")
