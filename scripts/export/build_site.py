"""Собрать сайт отчёта целиком, в порядке, который нельзя перепутать.

Порядок здесь не оформление, а требование. Три скрипта пишут в
страницы целиком, а один только дописывает навигацию. Если
навигацию собрать раньше, её затрут те, кто пересобирает страницу
целиком.

Случай был реальный. Сначала отработал build_nav.py и вложил меню,
подвал и подшапку в 31 страницу. Потом отработали build_dash_pages.py
и build_plan3m.py и перезаписали шесть страниц, а меню на них не
попало. Проверка ругалась на 43 вещи, и все 43 были следствием
одной ошибки порядка, а не сорока тремя разными ошибками.

Поэтому порядок зафиксирован здесь и каждая команда проверяется на
код возврата. Раньше эти девять скриптов запускались вручную по
одному, и порядок зависел от того, в каком порядке я их вспомнил.

Запуск:

    python scripts/export/build_site.py
"""

import os
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"C:\susa ai\2026 cifra audit"
HERE = os.path.dirname(os.path.abspath(__file__))

# Данные и содержимое страниц. Ничего не трогает навигацию.
CONTENT = [
    "build_wm_data.py",
    "build_site_data.py",
    "build_dashboard_data.py",
    "build_md_pages.py",
    "build_clusters_page.py",
    "build_dash_pages.py",
    "build_plan3m.py",
    "build_client_report.py",
    "build_client_docx.py",
]

# Навигация. Идёт после всего, что перезаписывает страницы.
CHROME = ["build_nav.py"]

# Воркер собирает уже готовые файлы, поэтому идёт последним.
BUNDLE = ["build_report_worker.py"]

# Проверки.
CHECKS = ["validate_report.py", "number_truth.py"]


def run(name, args=None):
    path = os.path.join(HERE, name)
    if not os.path.isfile(path):
        return False, "нет файла"
    cmd = [sys.executable, path] + (args or [])
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    out = (p.stdout or "") + (p.stderr or "")
    tail = [l for l in out.splitlines() if l.strip()]
    tail = tail[-1] if tail else ""
    return p.returncode == 0, "%5.1fs  %s" % (time.time() - t0, tail[:88])


def main():
    steps = [("содержимое", CONTENT), ("навигация", CHROME),
             ("воркер", BUNDLE), ("проверки", CHECKS)]
    failed = []

    for label, names in steps:
        print("=" * 78)
        print(label.upper())
        print("=" * 78)
        for name in names:
            args = ["--gate"] if name == "number_truth.py" else None
            ok, info = run(name, args)
            print("  %-4s %-26s %s" % ("ok" if ok else "FAIL", name, info))
            if not ok:
                failed.append(name)
        print()

    print("=" * 78)
    if failed:
        print("НЕ СОБРАНО, сломалось: %s" % ", ".join(failed))
        print("Дальше идти нельзя: воркер собрался бы из непроверенных "
              "страниц, а проверка показала бы не то состояние сайта, "
              "которое увидит читатель.")
        return 1
    print("сайт собран целиком, все проверки зелёные")
    return 0


if __name__ == "__main__":
    sys.exit(main())