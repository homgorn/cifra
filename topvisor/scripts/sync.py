#!/usr/bin/env python3
"""
Topvisor full sync: projects, keywords, positions history, competitors -> SQLite + MD.
ALL calls here are READ-ONLY (get/*) and FREE. Balance is printed at start and end.
Usage: python3 sync.py [--project-id 32490624] [--dates 2026-08-28,2026-08-28]
"""
import json
import os
import sqlite3
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tv import load_env, call, get_balance_quiet

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "db", "topvisor.db")
EXP_DIR = os.path.join(BASE_DIR, "exports")

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT);
CREATE TABLE IF NOT EXISTS projects(id INTEGER PRIMARY KEY, name TEXT, site TEXT, url TEXT, date TEXT);
CREATE TABLE IF NOT EXISTS searchers(id INTEGER PRIMARY KEY, project_id INTEGER, name TEXT, region_index INTEGER, region_name TEXT, region_key INTEGER);
CREATE TABLE IF NOT EXISTS keywords(id INTEGER PRIMARY KEY, project_id INTEGER, name TEXT, group_id INTEGER, group_name TEXT);
CREATE TABLE IF NOT EXISTS positions(keyword_id INTEGER, keyword TEXT, project_id INTEGER, region_index INTEGER, date TEXT, position TEXT, PRIMARY KEY(keyword_id, project_id, region_index, date));
CREATE TABLE IF NOT EXISTS tops_snapshots(ts TEXT, project_id INTEGER, region_index INTEGER, dates TEXT, t10 INTEGER, t30 INTEGER, t50 INTEGER, t100 INTEGER, rest INTEGER, avg REAL, visibility REAL);
CREATE TABLE IF NOT EXISTS competitors(id INTEGER PRIMARY KEY, project_id INTEGER, name TEXT, site TEXT);
CREATE TABLE IF NOT EXISTS balance_snapshots(ts TEXT, balance_all REAL, balance_personal REAL, balance_bonus REAL);
"""


def save_balance(env):
    b = get_balance_quiet(env)
    con = sqlite3.connect(DB_PATH)
    con.execute("INSERT INTO balance_snapshots VALUES(?,?,?,?)",
                (datetime.now().isoformat(timespec="seconds"),
                 b.get("balance_all"), b.get("balance_personal"), b.get("balance_bonus")))
    con.commit()
    con.close()
    return b


def sync_project(env, project_id):
    con = sqlite3.connect(DB_PATH)
    con.executescript(SCHEMA)
    # project + searchers
    out = call("get/projects_2/projects",
               {"limit": 100, "offset": 0, "fields": ["id", "name", "site", "url", "date"],
                "show_searchers_and_regions": 1, "include_positions_summary": 1}, env)
    projs = [p for p in (out.get("result") or []) if p.get("id") == project_id]
    if not projs:
        print("[X] Project not found")
        sys.exit(1)
    p = projs[0]
    con.execute("INSERT OR REPLACE INTO projects VALUES(?,?,?,?,?)",
                (p["id"], p.get("name"), p.get("site"), p.get("url"), p.get("date")))
    regions = []
    for s in p.get("searchers", []):
        for r in s.get("regions", []):
            con.execute("INSERT OR REPLACE INTO searchers VALUES(?,?,?,?,?,?)",
                        (r.get("id"), p["id"], s.get("name"), r.get("index"),
                         r.get("name"), r.get("key")))
            regions.append((s.get("name"), r.get("index")))
            ps = r.get("positions_summary") or {}
            tops = (ps.get("tops") or [{}])[0]
            avgs = ps.get("avgs") or [None]
            vis = ps.get("visibilities") or [None]
            con.execute("INSERT INTO tops_snapshots VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                        (datetime.now().isoformat(timespec="seconds"), p["id"], r.get("index"),
                         ",".join(ps.get("dates", [])), tops.get("1_10"), tops.get("11_30"),
                         tops.get("31_50"), tops.get("51_100"), tops.get("101_10000"),
                         avgs[0], vis[0]))
    con.execute("INSERT OR REPLACE INTO meta VALUES('last_sync',?)",
                (datetime.now().isoformat(timespec="seconds"),))
    con.commit()
    con.close()
    print(f"[+] Project: {p.get('name')} ({p.get('site')}), regions: {regions}")
    return p, regions


def sync_keywords(env, project_id):
    con = sqlite3.connect(DB_PATH)
    offset, total, n = 0, None, 0
    while True:
        out = call("get/keywords_2/keywords",
                   {"project_id": project_id, "limit": 1000, "offset": offset,
                    "fields": ["id", "name", "group_id", "group_name"]}, env)
        rows = out.get("result") or []
        if total is None:
            total = out.get("total", 0)
        if not rows:
            break
        for k in rows:
            con.execute("INSERT OR REPLACE INTO keywords VALUES(?,?,?,?,?)",
                        (k["id"], project_id, k["name"], k.get("group_id"), k.get("group_name")))
        n += len(rows)
        offset += len(rows)
        if n >= (total or 0):
            break
    con.commit()
    con.close()
    print(f"[+] Keywords: {n}/{total}")


def sync_history(env, project_id, region_index, date1, date2):
    con = sqlite3.connect(DB_PATH)
    # map keyword name -> id
    cur = con.execute("SELECT id, name FROM keywords WHERE project_id=?", (project_id,))
    name2id = {r[1]: r[0] for r in cur.fetchall()}
    offset, total, n = 0, None, 0
    while True:
        out = call("get/positions_2/history",
                   {"project_id": project_id, "regions_indexes": [region_index],
                    "type_range": 2, "date1": date1, "date2": date2,
                    "limit": 500, "offset": offset,
                    "history_fields": ["position"]}, env)
        res = out.get("result") or {}
        rows = res.get("keywords") or []
        dates = (res.get("headers") or {}).get("dates") or [date1]
        if total is None:
            total = res.get("total", len(rows))
        if not rows:
            break
        for k in rows:
            kid = name2id.get(k["name"])
            for dkey, pd in (k.get("positionsData") or {}).items():
                parts = dkey.split(":")
                d = parts[0]
                con.execute("INSERT OR REPLACE INTO positions VALUES(?,?,?,?,?,?)",
                            (kid, k["name"], project_id, region_index, d,
                             str(pd.get("position"))))
                n += 1
        offset += len(rows)
        if offset >= (total or 0):
            break
    con.commit()
    con.close()
    print(f"[+] Positions rows: {n} (dates {date1}..{date2})")


def sync_competitors(env, project_id):
    out = call("get/projects_2/competitors", {"project_id": project_id}, env)
    rows = out.get("result") or []
    con = sqlite3.connect(DB_PATH)
    for c in rows:
        con.execute("INSERT OR REPLACE INTO competitors VALUES(?,?,?,?)",
                    (c.get("id"), project_id, c.get("name"), c.get("site")))
    con.commit()
    con.close()
    print(f"[+] Competitors: {len(rows)}")


def export_md():
    os.makedirs(EXP_DIR, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    projs = list(con.execute("SELECT * FROM projects"))
    with open(os.path.join(EXP_DIR, "projects.md"), "w", encoding="utf-8") as f:
        f.write(f"# Topvisor: проекты\n\nОбновлено: {ts}\n\n")
        for p in projs:
            f.write(f"## {p['name']} (ID {p['id']})\n\n")
            f.write(f"- Сайт: {p['site']}\n- Создан: {p['date']}\n")
            regs = list(con.execute("SELECT * FROM searchers WHERE project_id=?", (p["id"],)))
            f.write(f"- Поисковики и регионы: {len(regs)}\n")
            for r in regs:
                f.write(f"  - {r['name']}, {r['region_name']} (index {r['region_index']})\n")
            f.write("\n")

    kws = list(con.execute("SELECT name FROM keywords ORDER BY name"))
    with open(os.path.join(EXP_DIR, "keywords.md"), "w", encoding="utf-8") as f:
        f.write(f"# Topvisor: ключи ({len(kws)})\n\nОбновлено: {ts}\n\n")
        groups = {}
        for r in con.execute("SELECT group_name, COUNT(*) c FROM keywords GROUP BY group_name"):
            groups[r[0]] = r[1]
        f.write("## Группы\n\n")
        for g, c in groups.items():
            f.write(f"- {g or '(без группы)'}: {c}\n")
        f.write("\n## Все ключи\n\n")
        for k in kws:
            f.write(f"- {k['name']}\n")

    with open(os.path.join(EXP_DIR, "positions.md"), "w", encoding="utf-8") as f:
        f.write(f"# Topvisor: позиции\n\nОбновлено: {ts}\n\n")
        for t in con.execute("SELECT * FROM tops_snapshots ORDER BY ts DESC LIMIT 5"):
            f.write(f"## Срез {t['ts']} (регион {t['region_index']}, даты {t['dates']})\n\n")
            f.write(f"- Топ-10: {t['t10']}, 11-30: {t['t30']}, 31-50: {t['t50']}, "
                    f"51-100: {t['t100']}, дальше: {t['rest']}\n")
            f.write(f"- Средняя: {t['avg']}, видимость: {t['visibility']}%\n\n")
        f.write("## Последние позиции по ключам\n\n")
        f.write("| Ключ | Дата | Позиция |\n|---|---|---|\n")
        for r in con.execute("SELECT keyword, date, position FROM positions ORDER BY date DESC LIMIT 200"):
            f.write(f"| {r[0]} | {r[1]} | {r[2]} |\n")

    comps = list(con.execute("SELECT * FROM competitors"))
    with open(os.path.join(EXP_DIR, "competitors.md"), "w", encoding="utf-8") as f:
        f.write(f"# Topvisor: конкуренты ({len(comps)})\n\nОбновлено: {ts}\n\n")
        for c in comps or [None]:
            if c:
                f.write(f"- {c['name']} ({c['site']})\n")
        if not comps:
            f.write("В проекте конкуренты не заданы. Добавить можно в интерфейсе Топвизора, чтение бесплатное.\n")

    bals = list(con.execute("SELECT * FROM balance_snapshots ORDER BY ts DESC LIMIT 10"))
    with open(os.path.join(EXP_DIR, "balance.md"), "w", encoding="utf-8") as f:
        f.write(f"# Topvisor: баланс\n\nОбновлено: {ts}\n\n")
        f.write("| Дата | Всего | Личные | Бонус |\n|---|---|---|---|\n")
        for b in bals:
            f.write(f"| {b[0]} | {b[1]} | {b[2]} | {b[3]} |\n")
    con.close()
    print(f"[+] MD exports -> {EXP_DIR}")


def main():
    from tv import load_env
    env = load_env()
    project_id = 32490624
    date1 = date2 = "2026-08-28"
    args = sys.argv[1:]
    if "--project-id" in args:
        project_id = int(args[args.index("--project-id") + 1])
    if "--dates" in args:
        d = args[args.index("--dates") + 1].split(",")
        date1, date2 = d[0], d[1] if len(d) > 1 else d[0]

    print("=== Topvisor sync (только чтение, БЕСПЛАТНО) ===")
    con0 = sqlite3.connect(DB_PATH)
    con0.executescript(SCHEMA)
    con0.commit()
    con0.close()
    b0 = save_balance(env)
    print(f"Баланс на старте: {b0.get('balance_all')} RUB")
    p, regions = sync_project(env, project_id)
    sync_keywords(env, project_id)
    for name, rindex in regions:
        sync_history(env, project_id, int(rindex), date1, date2)
    sync_competitors(env, project_id)
    export_md()
    b1 = save_balance(env)
    print(f"Баланс в конце: {b1.get('balance_all')} RUB (потрачено: "
          f"{round((b0.get('balance_all') or 0) - (b1.get('balance_all') or 0), 2)})")
    print("=== Готово ===")


if __name__ == "__main__":
    main()
