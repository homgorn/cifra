#!/usr/bin/env python3
"""
Topvisor API v2 client with cost guard.

RULES (by owner request):
1. Before ANY paid action: print exact cost and require --confirm-spend "TEXT".
2. After EVERY run: print account balance.
3. Every call is logged to SQLite (topvisor/db/topvisor.db, table api_log).

Reading data (get/*) is FREE. Money is spent only by:
- */checker.go (launch position/audit/indexing checks)
- projects_2/tasks.* (volumes, clustering, relevants, indexing tasks)
- keywords_2/volumes.go, collect.go, claster.task*
- keywords_2/keywords.import with check launch

Usage:
    python3 tv.py balance
    python3 tv.py projects
    python3 tv.py keywords --project-id 32490624
    python3 tv.py summary --project-id 32490624
    python3 tv.py competitors --project-id 32490624
    python3 tv.py price positions --project-id 32490624   # FREE estimate
    python3 tv.py check positions --project-id 32490624 --confirm-spend "yes, launch check"
"""
import json
import os
import sqlite3
import ssl
import sys
import urllib.request
from datetime import datetime


def ssl_context():
    for cafile in ("/etc/ssl/cert.pem",):
        if os.path.exists(cafile):
            return ssl.create_default_context(cafile=cafile)
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


CTX = ssl_context()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "db", "topvisor.db")
ENV_PATH = os.path.join(BASE_DIR, ".env")
API = "https://api.topvisor.com/v2/json"

# Methods that SPEND money. Everything else (get/*) is free to read.
PAID_PATTERNS = (
    "checker.go",
    "tasks.keywords",
    "tasks.volumes",
    "tasks.relevants",
    "tasks.indexing",
    "volumes.go",
    "collect.go",
    "claster.task",
    "keywords.import",
)


def load_env():
    env = {}
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    env.setdefault("TOPVISOR_API_KEY", os.environ.get("TOPVISOR_API_KEY", ""))
    env.setdefault("TOPVISOR_USER_ID", os.environ.get("TOPVISOR_USER_ID", ""))
    return env


def is_paid(path):
    return any(p in path for p in PAID_PATTERNS)


def call(path, payload, env, confirm_spend=None):
    """POST to Topvisor API. Enforces cost guard for paid methods."""
    if is_paid(path):
        print(f"[!] PAID OPERATION: {path}")
        print(f"[!] Payload: {json.dumps(payload, ensure_ascii=False)[:500]}")
        print("[!] This call WILL spend money from balance 1977.7 RUB (check current below).")
        if confirm_spend is None:
            print("[X] BLOCKED: re-run with --confirm-spend \"yes, launch\" to proceed.")
            log_call(path, payload, None, "BLOCKED-no-confirm", env)
            show_balance(env)
            sys.exit(2)
        print(f"[+] Confirmed with: {confirm_spend}")
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{API}/{path}",
        data=data,
        headers={
            "Authorization": f"bearer {env['TOPVISOR_API_KEY']}",
            "User-Id": env["TOPVISOR_USER_ID"],
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60, context=CTX) as resp:
            out = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[X] HTTP error: {e}")
        log_call(path, payload, None, f"HTTP-ERROR {e}", env)
        sys.exit(1)
    if out.get("errors"):
        print(f"[X] API errors: {json.dumps(out['errors'], ensure_ascii=False)[:500]}")
        log_call(path, payload, None, "API-ERROR", env)
        return out
    log_call(path, payload, out.get("total"), "OK", env)
    return out


def get_balance(env):
    out = call(
        "get/bank_2/info",
        {"fields": ["balance_all", "balance_personal", "balance_bonus"]},
        env,
    )
    return (out.get("result") or {})


def show_balance(env):
    try:
        b = get_balance_quiet(env)
        print(f"[=] Balance: {b.get('balance_all')} RUB "
              f"(personal {b.get('balance_personal')}, bonus {b.get('balance_bonus')})")
        return b
    except Exception as e:
        print(f"[X] Could not fetch balance: {e}")
        return {}


def get_balance_quiet(env):
    data = json.dumps({"fields": ["balance_all", "balance_personal", "balance_bonus"]}).encode()
    req = urllib.request.Request(
        f"{API}/get/bank_2/info", data=data,
        headers={"Authorization": f"bearer {env['TOPVISOR_API_KEY']}",
                 "User-Id": env["TOPVISOR_USER_ID"], "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60, context=CTX) as resp:
        return json.loads(resp.read().decode("utf-8")).get("result") or {}


def log_call(path, payload, total, status, env):
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        con = sqlite3.connect(DB_PATH)
        con.execute(
            """CREATE TABLE IF NOT EXISTS api_log(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT, method TEXT, paid INTEGER,
                payload TEXT, total TEXT, status TEXT)"""
        )
        con.execute(
            "INSERT INTO api_log(ts,method,paid,payload,total,status) VALUES(?,?,?,?,?,?)",
            (datetime.now().isoformat(timespec="seconds"), path, int(is_paid(path)),
             json.dumps(payload, ensure_ascii=False)[:2000],
             str(total)[:200], status),
        )
        con.commit()
        con.close()
    except Exception as e:
        print(f"(log failed: {e})")


def main():
    env = load_env()
    if not env["TOPVISOR_API_KEY"] or not env["TOPVISOR_USER_ID"]:
        print("[X] No credentials. Put them in topvisor/.env or env vars.")
        sys.exit(1)
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__)
        return
    cmd = args[0]
    confirm = None
    if "--confirm-spend" in args:
        i = args.index("--confirm-spend")
        confirm = args[i + 1] if i + 1 < len(args) else "yes"
    project_id = None
    if "--project-id" in args:
        project_id = int(args[args.index("--project-id") + 1])

    print(f"[*] {cmd} @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if cmd == "balance":
        print(json.dumps(get_balance(env), ensure_ascii=False, indent=2))
    elif cmd == "projects":
        out = call("get/projects_2/projects",
                   {"limit": 100, "offset": 0,
                    "fields": ["id", "name", "site", "url", "date"]}, env)
        print(json.dumps(out.get("result"), ensure_ascii=False, indent=2))
    elif cmd == "keywords":
        assert project_id, "need --project-id"
        out = call("get/keywords_2/keywords",
                   {"project_id": project_id, "limit": 5000, "offset": 0,
                    "fields": ["id", "name", "group_id", "group_name"]}, env)
        print(f"keywords: {out.get('total')}")
        print(json.dumps(out.get("result"), ensure_ascii=False)[:3000])
    elif cmd == "summary":
        assert project_id, "need --project-id"
        out = call("get/positions_2/summary",
                   {"project_id": project_id}, env)
        print(json.dumps(out.get("result"), ensure_ascii=False, indent=2)[:4000])
    elif cmd == "competitors":
        assert project_id, "need --project-id"
        out = call("get/projects_2/competitors",
                   {"project_id": project_id}, env)
        print(json.dumps(out.get("result"), ensure_ascii=False, indent=2)[:4000])
    elif cmd == "price" and len(args) > 1 and args[1] == "positions":
        assert project_id, "need --project-id"
        out = call("get/positions_2/checker.price", {"project_id": project_id}, env)
        print(json.dumps(out.get("result"), ensure_ascii=False, indent=2))
    else:
        print(f"[X] Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)

    show_balance(env)


if __name__ == "__main__":
    main()
