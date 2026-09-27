#!/usr/bin/env python3
"""Проверка темы: токены цветов, запрет литералов в компонентах, контраст.

Зачем: 2026-09-27 отчёт открылся в светлой теме операционной системы, шапка
осталась тёмной (в ней был литерал `rgba(10, 14, 20, 0.9)`, а тело брало
`var(--color-bg)` из блока `prefers-color-scheme: light`), и логотип с пунктами
меню стали нечитаемыми. Второй симптом: оверлей поиска был почти чёрным поверх
светлой страницы.

Скрипт ловит это до выкладки:
1. Все цвета поверхностей и текста берутся из токенов `:root`.
2. В компонентах нет цветовых литералов (кроме блока печати и градиентов).
3. Нет блока `prefers-color-scheme`, который переопределяет токены: тема одна.
4. Контраст ключевых пар не ниже порогов WCAG AA.

Запуск из корня проекта:
  python scripts/export/validate_theme.py
"""
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CSS = os.path.join(ROOT, "reports", "cifra18-audit", "css")
FILES = ["main.css", "report.css", "nav.css"]

# (текст, фон, минимальный контраст, человеческое описание)
PAIRS = [
    ("--color-fg", "--color-bg", 4.5, "основной текст на фоне страницы"),
    ("--color-fg", "--color-bg-card", 4.5, "текст в карточке"),
    ("--color-fg-muted", "--color-bg", 4.5, "второстепенный текст"),
    ("--color-fg-muted", "--color-bg-elevated", 4.5, "пункты меню на фоне шапки"),
    ("--color-fg-subtle", "--color-bg", 3.0, "подписи моноширинным шрифтом"),
    ("--color-accent", "--color-bg", 3.0, "акцентные ссылки на фоне"),
    ("--color-accent", "--color-bg-card", 3.0, "акцентные ссылки в карточке"),
    ("--color-warn", "--color-bg", 3.0, "предупреждения"),
    ("--color-error", "--color-bg", 3.0, "ошибки"),
    ("--color-info", "--color-bg", 3.0, "информационные метки"),
]

fails = []
notes = []


def parse_hex(s):
    s = s.strip()
    if s.startswith("#"):
        s = s[1:]
        if len(s) == 3:
            s = "".join(c * 2 for c in s)
        if len(s) != 6:
            return None
        try:
            return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
        except ValueError:
            return None
    return None


def parse_rgba(s):
    m = re.match(r"rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)(?:[,\s]+([\d.]+))?\s*\)", s.strip())
    if not m:
        return None, 1.0
    r, g, b = (float(m.group(i)) for i in (1, 2, 3))
    a = float(m.group(4)) if m.group(4) else 1.0
    return (int(r), int(g), int(b)), a


def flatten(color, alpha, backdrop):
    """Склеивает полупрозрачный цвет с подложкой под ним."""
    if color is None:
        return None
    r, g, b = color
    br, bg, bb = backdrop
    return (round(r * alpha + br * (1 - alpha)),
            round(g * alpha + bg * (1 - alpha)),
            round(b * alpha + bb * (1 - alpha)))


def luminance(rgb):
    def ch(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(x) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def root_block(css):
    m = re.search(r":root\s*\{(.*?)\n\}", css, re.S)
    return m.group(1) if m else ""


def main():
    sources = {}
    for name in FILES:
        p = os.path.join(CSS, name)
        if not os.path.isfile(p):
            fails.append("нет файла %s" % name)
            continue
        sources[name] = open(p, encoding="utf-8").read()

    if not sources:
        print("VALIDATION FAILED: css не найден")
        return 1

    main_css = sources.get("main.css", "")

    # 1. Тема одна: блок prefers-color-scheme не переопределяет токены
    scheme_blocks = re.findall(r"@media\s*\(prefers-color-scheme:[^)]*\)\s*\{(.*?\n\})", main_css, re.S)
    redefining = [b for b in scheme_blocks if "--color-" in b]
    if redefining:
        fails.append("в main.css есть блок prefers-color-scheme с токенами: тема должна быть одна")
    else:
        notes.append("тема одна, prefers-color-scheme токены не переопределяет")

    # 2. Токены
    tokens = {}
    for line in root_block(main_css).splitlines():
        m = re.match(r"\s*(--[a-z0-9-]+)\s*:\s*([^;]+);", line)
        if m:
            tokens[m.group(1)] = m.group(2).strip()
    need = {"--color-bg", "--color-bg-elevated", "--color-bg-card", "--color-fg",
            "--color-fg-muted", "--color-fg-subtle", "--color-accent", "--color-warn",
            "--color-error", "--color-info", "--surface-header", "--overlay-bg"}
    missing = sorted(need - set(tokens))
    if missing:
        fails.append("нет токенов: %s" % missing)
    else:
        notes.append("токенов в :root: %d" % len(tokens))

    # 3. Литералы цветов в компонентах
    literal = re.compile(r"(?<![-\w])(#[0-9a-fA-F]{3,8}\b|rgba?\([^)]*\))")
    for name, css in sources.items():
        body = css
        # комментарии выкидываем: литерал в пояснении не нарушение
        body = re.sub(r"/\*.*?\*/", "", body, flags=re.S)
        # вырезаем блок токенов и блок печати: там литералы законны
        body = re.sub(r":root\s*\{.*?\n\}", "", body, flags=re.S)
        body = re.sub(r"@media\s*print\s*\{.*?\n\}", "", body, flags=re.S)
        for i, line in enumerate(body.splitlines(), 1):
            if literal.search(line) and "var(" not in line:
                fails.append("литерал цвета вне токенов: %s строка %d: %s"
                             % (name, i, line.strip()[:70]))
    if not any("литерал цвета" in f for f in fails):
        notes.append("в компонентах нет цветовых литералов")

    # 4. Контраст
    def resolve(name, seen=()):
        if name in seen:
            return None
        val = tokens.get(name, "")
        m = re.match(r"var\((--[a-z0-9-]+)\)", val)
        if m:
            return resolve(m.group(1), seen + (name,))
        rgb, a = parse_rgba(val)
        if rgb is None:
            rgb = parse_hex(val)
            a = 1.0
        return (rgb, a)

    page_bg = resolve("--color-bg")
    page_rgb = page_bg[0] if page_bg else (10, 14, 20)
    for fg_name, bg_name, need_ratio, desc in PAIRS:
        f = resolve(fg_name)
        b = resolve(bg_name)
        if not f or not b:
            continue
        bgb = flatten(b[0], b[1], page_rgb)
        fgc = flatten(f[0], f[1], bgb)
        r = contrast(fgc, bgb)
        if r < need_ratio:
            fails.append("контраст %.2f:1 ниже %.1f для %s (%s на %s)"
                         % (r, need_ratio, desc, fg_name, bg_name))
        else:
            notes.append("контраст %5.2f:1  %s" % (r, desc))

    print("--- Тема ---")
    for n in notes:
        print("ok: %s" % n)
    if fails:
        print("---")
        for f in fails:
            print("FAIL: %s" % f)
        print("THEME VALIDATION FAILED: %d" % len(fails))
        return 1
    print("---")
    print("THEME VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
