#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Собрать все лендинги по одной команде.

Зачем. Один лендинг это семь шагов в правильном порядке, и порядок важен:
фотографии должны быть скачаны и оптимизированы до генерации конфига,
потому что генератор смотрит, что локальный файл существует, и подставляет
локальный путь вместо адреса на сайте. Если поменять шаги местами,
страница соберётся, пройдёт все гейты, а фотографии на ней окажутся
битыми. Гейт 14 ловит это, но только если до него дойти.

Шаги на лендинг:
  1. конфиг из спецификации и выкачки
  2. скачать ровно те фото, на которые ссылаются карточки
  3. оптимизировать их в assets/web
  4. положить статичную карту
  5. пересобрать конфиг, теперь с локальными путями
  6. отрендерить через landing-blueprint-2/render.js
  7. прогнать validate_landing.py

Запуск из корня проекта:
  python landings/build_all.py                 все
  python landings/build_all.py upakovka nakleyki-i-plenki   выборочно
  python landings/build_all.py --skip-fetch    без скачивания, если фото уже есть
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent
SCRAPE = ROOT / "_scrape"
SPECS = SCRAPE / "category_specs.json"
BLUEPRINT = ROOT / "landing-blueprint-2"
CATALOG = SCRAPE / "out" / "catalog.json"

# Первые два лендинга сделаны отдельными генераторами, у них нет ключа в
# category_specs.json. Генератор у них свой, поэтому и собираются они
# своим же шагом 1. Раньше шаг 1 для них пропускался, и правки в их
# генераторах до конфигов не доходили: файл правился, а `config.json`
# оставался старым, и гейт 14c ругался на отсутствие поля `src`.
LEGACY = [
    ("kvartalnyy-kalendar-2027", "calendar"),
    ("merch-s-l-logotipom", "merch"),
]

GENERATORS = {
    "calendar": SCRAPE / "build_calendar_config.py",
    "merch": SCRAPE / "build_merch_config.py",
}

MAP_SOURCE = ROOT / "kvartalnyy-kalendar-2027" / "assets" / "web" / "map.png"


def run(cmd: list[str], cwd: Path | None = None) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def heading(text: str) -> None:
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70, flush=True)


def gen_config(spec_key: str) -> tuple[int, str]:
    """Шаг 1. Генератор выбирается по ключу спецификации.

    Ключи из category_specs.json идут в общий генератор, два особых
    значения это отдельные генераторы первых лендингов.
    """
    script = GENERATORS.get(spec_key)
    if script is None:
        script = SCRAPE / "build_category_config.py"
    return run([sys.executable, str(script), spec_key])


def build(slug: str, spec_key: str | None, skip_fetch: bool) -> bool:
    landing = ROOT / slug
    assets = landing / "assets"
    web = assets / "web"
    ok = True

    # 1. конфиг
    rc, out = gen_config(spec_key)
    if rc != 0:
        print(f"  ! сборка конфига не удалась:\n{out}")
        return False
    print("  1. конфиг собран")

    cfg_path = landing / "config.json"
    if not cfg_path.exists():
        print(f"  ! нет {cfg_path}")
        return False

    # 2. фото
    remote = count_remote(cfg_path)
    if remote == 0:
        print("  2. все фото уже локальные, скачивать нечего")
    elif skip_fetch:
        print(f"  2. ПРОПУЩЕНО по --skip-fetch, но {remote} фото удалённые")
        ok = False
    else:
        rc, out = run([sys.executable, str(SCRAPE / "fetch_images.py"),
                       "--section", "unused", "--out", str(assets),
                       "--config", str(cfg_path)])
        tail = [l for l in out.splitlines() if l.strip()][-2:]
        for l in tail:
            print("     " + l.strip())
        if rc != 0:
            print(f"  ! скачивание не удалось:\n{out[-600:]}")
            ok = False
        else:
            print(f"  2. скачано фото")

    # 3. оптимизация
    if assets.is_dir() and any(assets.iterdir()):
        rc, out = run([sys.executable, str(SCRAPE / "optimize_images.py"),
                       "--src", str(assets), "--dst", str(web)])
        summary = [l for l in out.splitlines() if l.startswith("Файлов")]
        print("  3. " + (summary[0] if summary else "оптимизация молчала"))
        if rc != 0:
            print(f"     ! {out[-400:]}")
            ok = False

    # 4. карта
    if MAP_SOURCE.exists() and not (web / "map.png").exists():
        web.mkdir(parents=True, exist_ok=True)
        shutil.copy2(MAP_SOURCE, web / "map.png")
        print("  4. карта скопирована")
    elif (web / "map.png").exists():
        print("  4. карта на месте")

    # 5. пересборка конфига с локальными путями
    rc, out = gen_config(spec_key)
    if rc != 0:
        print(f"  ! пересборка конфига не удалась:\n{out}")
        return False
    left = count_remote(cfg_path)
    print(f"  5. конфиг пересобран, удалённых фото осталось {left}")
    if left:
        ok = False

    # 6. рендер
    removed, freed = prune_unused(landing, cfg_path)
    if removed:
        print(f"  6. удалено неиспользуемых фото: {removed} "
              f"({freed / 1024 / 1024:.1f} МБ)")
    dist = landing / "dist"
    if dist.exists():
        shutil.rmtree(dist)
    rc, out = run(["node", "render.js", str(cfg_path), str(dist)], cwd=BLUEPRINT)
    if rc != 0:
        print(f"  ! рендер не удался:\n{out[-600:]}")
        return False
    warn = [l for l in out.splitlines() if "WARN" in l]
    print("  6. отрендерено" + (f" С ПРЕДУПРЕЖДЕНИЕМ: {warn}" if warn else ""))
    if warn:
        ok = False

    # 7. гейты
    rc, out = run([sys.executable, str(ROOT / "validate_landing.py"), str(landing)])
    fails = [l.strip() for l in out.splitlines() if l.strip().startswith("✗")]
    passed = [l for l in out.splitlines() if "гейтов пройдены" in l]
    print("  7. " + (passed[0].strip() if passed else "вердикт не найден"))
    for f in fails:
        print("     " + f)
    if rc != 0:
        ok = False

    size = sum(f.stat().st_size for f in dist.rglob("*") if f.is_file())
    print(f"     dist: {size / 1024 / 1024:.1f} МБ")
    return ok


def count_remote(cfg_path: Path) -> int:
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    return sum(1 for g in cfg.get("catalog", {}).get("groups", [])
               for it in g.get("items", [])
               if not it.get("img", "").startswith("assets/"))


def prune_unused(landing: Path, cfg_path: Path) -> tuple[int, int]:
    """Удаляет из assets/web то, на что не ссылается ни одна карточка.

    Зачем. render.js копирует в dist всю папку ассетов целиком. У
    мерча скачано 84 фотографии, а используется 16, и шесть мегабайт
    лишнего веса уезжали на хостинг и в кэш посетителя. Ни одна из них
    на странице не показывается.

    Оригиналы в assets при этом остаются: они нужны, чтобы пересобрать
    лендинг без повторного скачивания.
    """
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    used = {it["img"].split("/")[-1]
            for g in cfg.get("catalog", {}).get("groups", [])
            for it in g.get("items", [])
            if it.get("img", "").startswith("assets/web/")}
    used.add(Path(cfg.get("contact", {}).get("mapImage", "")).name)
    web = landing / "assets" / "web"
    if not web.is_dir():
        return 0, 0
    removed = freed = 0
    for f in sorted(web.iterdir()):
        if f.is_file() and f.name not in used:
            freed += f.stat().st_size
            f.unlink()
            removed += 1
    return removed, freed


def main() -> int:
    ap = argparse.ArgumentParser(description="Собрать все лендинги.")
    ap.add_argument("slugs", nargs="*", help="что собирать. Пусто, значит всё")
    ap.add_argument("--skip-fetch", action="store_true",
                    help="не скачивать фото, только пересобрать")
    ap.add_argument("--no-registry", action="store_true",
                    help="не пересобирать lead_registrations.json. "
                         "Нужен редко: обработчик заявок без реестра "
                         "не отличит заявку с календарей от заявки с "
                         "мерча, поэтому гейт на это ругается.")
    args = ap.parse_args()

    if not CATALOG.exists():
        print("Нет out/catalog.json. Сначала fetch_catalog.py --parse-only")
        return 1

    specs = json.loads(SPECS.read_text(encoding="utf-8"))["landings"]
    plan: list[tuple[str, str | None]] = []
    known = {slug: key for slug, key in LEGACY}
    if args.slugs:
        for s in args.slugs:
            key = s if s in specs else known.get(s)
            if key is None and not (ROOT / s / "config.json").exists():
                print(f"Неизвестный лендинг: {s}")
                return 1
            plan.append((s, key))
    else:
        plan = list(LEGACY) + [(v["slug"], k) for k, v in specs.items()]

    results: list[tuple[str, bool]] = []
    for slug, key in plan:
        heading(slug + (f"  ({key})" if key else "  (отдельный генератор)"))
        try:
            ok = build(slug, key, args.skip_fetch)
        except Exception as e:  # noqa: BLE001
            print(f"  ! непойманная ошибка: {type(e).__name__}: {e}")
            ok = False
        results.append((slug, ok))

    heading("ИТОГ")
    for slug, ok in results:
        print(f"  {'собран' if ok else 'С ПРОБЛЕМАМИ':<14} {slug}")
    bad = [s for s, ok in results if not ok]
    print()
    print(f"собрано без замечаний: {len(results) - len(bad)} из {len(results)}")

    # Реестр собирается всегда, даже если часть лендингов не собралась:
    # обработчик заявок один на домен и читает его, чтобы отличить заявку
    # с календарей от заявки с мерча. Собирать его только при полном успехе
    # нельзя, тогда одна сломанная страница уронила бы идентификацию всех
    # остальных.
    if not args.no_registry:
        registry = {}
        for slug, _key in plan:
            cfg = ROOT / slug / "config.json"
            if not cfg.exists():
                continue
            data = json.loads(cfg.read_text(encoding="utf-8"))
            reg_slug = data.get("landing", {}).get("slug")
            title = data.get("landing", {}).get("title")
            if reg_slug and title:
                registry[reg_slug] = title
        reg_path = ROOT / "php" / "lead_registrations.json"
        reg_path.parent.mkdir(parents=True, exist_ok=True)
        reg_path.write_text(json.dumps(registry, ensure_ascii=False, indent=1)
                            + "\n", encoding="utf-8")
        print(f"\nреестр заявок: {reg_path.name}, {len(registry)} страниц")
        for k, v in sorted(registry.items()):
            print(f"  {k:<30} {v}")

    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())