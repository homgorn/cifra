#!/usr/bin/env python3
"""Деплой отчёта на Cloudflare Worker cifra18-audit-report.

Пересобирает воркер (build_report_worker.py), валидирует
(validate_worker.py) и заливает через Cloudflare API.

Нужны переменные окружения:
  CLOUDFLARE_API_TOKEN    — токен с правом Workers Scripts:Edit
  CLOUDFLARE_ACCOUNT_ID   — ID аккаунта

Запуск из корня проекта:
  set CLOUDFLARE_API_TOKEN=... & set CLOUDFLARE_ACCOUNT_ID=... & python scripts/export/deploy_worker.py
"""
import json
import os
import subprocess
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORKER = os.path.join(ROOT, "reports", "cifra18-audit-worker.js")
SCRIPT_NAME = "cifra18-audit-report"

token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
account = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
if not token or not account:
    print("Нужны CLOUDFLARE_API_TOKEN и CLOUDFLARE_ACCOUNT_ID в окружении.")
    print("Токен создаётся: Cloudflare Dashboard → My Profile → API Tokens → "
          "Template 'Edit Cloudflare Workers'.")
    sys.exit(2)

for script in ("scripts/export/build_report_worker.py",
               "scripts/export/validate_worker.py"):
    r = subprocess.run([sys.executable, script], cwd=ROOT)
    if r.returncode != 0:
        print("Остановлено: %s завершился с ошибкой" % script)
        sys.exit(1)

with open(WORKER, "r", encoding="utf-8") as f:
    code = f.read()

url = ("https://api.cloudflare.com/client/v4/accounts/%s/workers/scripts/%s"
       % (account, SCRIPT_NAME))
req = urllib.request.Request(
    url, data=code.encode("utf-8"), method="PUT",
    headers={"Authorization": "Bearer " + token,
             "Content-Type": "application/javascript"})
try:
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read().decode("utf-8"))
except Exception as e:
    print("Ошибка API: %s" % e)
    sys.exit(1)

if not body.get("success"):
    print("Cloudflare отклонил деплой: %s" % json.dumps(body.get("errors"), ensure_ascii=False))
    sys.exit(1)
print("Деплой успешен: воркер %s обновлён (%.1f КБ)." % (SCRIPT_NAME, len(code) / 1024))
print("Проверка: https://%s.<ваш-домен>/ и /wm-overview.html" % SCRIPT_NAME)
