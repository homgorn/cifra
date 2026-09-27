#!/usr/bin/env python3
"""Пересобирает текст страницы кластеров из wm-data.js.

Зачем: 2026-09-27 на странице стояло «8 групп», «535 запросов» и
«худшее покрытие у кружек (33%)», хотя кластеров стало 22, запросов в
ядре 492, а метрика покрытия выродилась в 100%. Цифры в тексте разошлись
с графиками, которые строятся из данных. Текст теперь тоже строится
из wm-data.js: перезапуск скрипта не даст цифрам разойтись.

Запуск из корня проекта:
  python scripts/export/build_clusters_page.py
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WM_DATA = os.path.join(ROOT, "reports", "cifra18-audit", "js", "wm-data.js")
PAGE = os.path.join(ROOT, "reports", "cifra18-audit", "pages", "wm-clusters.html")

# Кластеры без своей посадочной: их запросы обслуживают общие разделы.
NO_TARGET = ("Локальные", "Общий спрос", "Информационные", "Сравнения")


def load():
    t = open(WM_DATA, encoding="utf-8").read()
    return json.loads(t[t.index("{"):].rstrip().rstrip(";"))


def plural(n, one, few, many):
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many


def intro(stats, clusters):
    total = stats["total"]
    groups = len(clusters)
    top = [c["name"] for c in clusters[:6]]
    return (
        ('<h1>Кластеры запросов: %d %s</h1>\n'
         '    <p class="page-lead">%d запросов ядра разложены по тем же группам '
         'по смыслу. Правила кластеризации живут в коде, таблица и графики '
         'строятся из тех же данных, поэтому текст и числа не расходятся.</p>'
         % (groups, plural(groups, "группа", "группы", "групп"), total))
        + ('\n    <p>Крупнейшие группы: %s. Остальные мельче, но это не значит, '
           'что они не нужны: у узкого кластера дешевле довести позицию, '
           'и он даёт запросы с высокой покупательской готовностью.</p>'
           % ", ".join(esc(t) for t in top))
    )


def coverage_section(clusters):
    """Раздел «страницы в поиске»: тонкие разделы и кластеры без страницы."""
    thin = [c for c in clusters if thin_score(c) is not None]
    thin.sort(key=lambda c: -thin_score(c))
    no_target = [c for c in clusters if c["name"] in NO_TARGET]
    no_target.sort(key=lambda c: -c["queries"])

    lines = []
    if thin:
        worst = thin[:4]
        parts = ", ".join(
            "%s (%d %s против %d)"
            % (esc(c["name"]), c["pages"],
               plural(c["pages"], "страница", "страницы", "страниц"),
               c["queries"]) for c in worst)
        lines.append(
            '<p>Тонкие места видно сразу: %s. Запросов много, страниц раздела '
            'в поиске почти нет, поэтому одна страница тянет на себя весь '
            'модификатор спроса.</p>' % parts)
    if no_target:
        names = ", ".join(esc(c["name"]) for c in no_target)
        lines.append(
            '<p>Отдельно: у %d %s (%s) нет своей посадочной страницы, их '
            'запросы уходят на главную и общие разделы каталога. Городской '
            'спрос в первую очередь: под него нужна страница с услугами '
            'и городом в заголовке, иначе он не виден и в геозапросах, '
            'и в обычной выдаче.</p>'
            % (len(no_target),
               plural(len(no_target), "группы", "групп", "групп"), names))
    return "    " + "\n    ".join(lines)


def thin_score(c):
    """Насколько раздел не покрыт страницами: больше число, хуже.

    None для кластеров без своего раздела каталога: у них нет страниц по
    построению, и сравнивать их с отделами каталога бессмысленно.
    Так же исключён «Бренд»: его цель корень сайта, а не раздел.
    """
    if c["name"] in NO_TARGET or c.get("target") in ("", "/"):
        return None
    if c["pages"] >= c["queries"] / 8:
        return None
    return c["queries"] - c["pages"] * 8


def coverage_inline(clusters):
    """Подпись под вторым графиком: коротко, без повтора раздела выше."""
    with_pages = sum(1 for c in clusters if c["pages"] > 0)
    empty = [c for c in clusters
             if c["pages"] == 0 and c["name"] not in NO_TARGET
             and c.get("target") not in ("", "/")]
    out = ("Красным отмечены разделы, которых в поиске нет вообще, "
           "жёлтым: страниц заметно меньше, чем запросов. "
           "Страницы у %d из %d разделов с целевой."
           % (with_pages, len([c for c in clusters
                               if c["name"] not in NO_TARGET])))
    if empty:
        out += (" Нет страниц в поиске у: %s."
                % ", ".join(esc(c["name"]) for c in empty))
    return out


def junk_section(stats):
    return (
        '<p>Из %d строк выгрузки %d оказались мусором: телефоны, длинные '
        'описания товаров и обрывки, их отсеяли. Ещё %d %s не попали '
        'ни в один кластер и ждут разбора: они не мусор, но и не ложатся '
        'под существующие правила. Список лежит в '
        '<code>topvisor/exports/review_queries.csv</code> вместе с причиной '
        'по каждой строке.</p>'
        % (stats["rows"], stats["junk"], stats.get("other", 0),
           plural(stats.get("other", 0), "запрос", "запроса", "запросов"))
    )


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def replace_block(html, pattern, new, label):
    """Заменяет первый блок по регулярке. new может быть строкой или функцией,
    которой передаётся match: это нужно, чтобы вставить текст, собранный
    из данных, и не сломать обратные ссылки в разметке."""
    repl = new if callable(new) else (lambda m: new)
    out, n = re.subn(pattern, repl, html, count=1, flags=re.DOTALL)
    if n == 0:
        print("  ВНИМАНИЕ: не найден блок %s" % label)
    return out


def main():
    d = load()
    clusters = d["clusters"]
    stats = d["queryStats"]
    html = open(PAGE, encoding="utf-8").read()
    before = html

    html = replace_block(html, r"<h1>Кластеры запросов:.*?</p>\s*</div>",
                         intro(stats, clusters) + "\n    </div>", "заголовок")

    # Секция «где тонко» целиком, по якорю. Ищем от h2 до следующего
    # закрывающего тега, чтобы повторный запуск переписывал и свой же
    # результат, а не только исходную разметку.
    html = replace_block(
        html,
        r'(<h2>(?:Покрытие страницами|Страницы разделов в поиске): где тонко</h2>)'
        r'(.*?)(?=\n\s*<div class="card">)',
        lambda m: (m.group(1) + "\n    " + coverage_section(clusters)),
        "секция «где тонко»")

    html = replace_block(
        html,
        r'\s*<p class="text-muted" style="font-size:0\.8125rem; margin-top:1rem; margin-bottom:0;">[^<]*</p>',
        '\n      <p class="text-muted" style="font-size:0.8125rem; margin-top:1rem; margin-bottom:0;">%s</p>'
        % coverage_inline(clusters),
        "подпись под графиком")
    html = replace_block(html, r"<p>[^<]*Из \d+ строк выгрузки.*?</p>",
                         junk_section(stats), "мусор")
    html = replace_block(
        html,
        r'<meta name="description" content="[^"]*">',
        '<meta name="description" content="%d %s запросов, %d запросов '
        'ядра, страницы разделов в поиске по данным цифра18.рф: визитки, '
        'широкоформат, сувенирка, ламинация, УФ-печать, ризография.">'
        % (len(clusters), plural(len(clusters), "группа", "группы", "групп"),
           stats["total"]),
        "meta description")

    # Заголовок и подпись графика описывали метрику покрытия, которой
    # больше нет: вместо неё реальные страницы из выгрузки панели.
    html = re.sub(r'<div class="card-title">[^<]*</div>'
                  r'<div class="card-subtitle">[^<]*</div>(?=\s*</div></div>\s*'
                  r'<div class="card-body"><div class="chart-container">'
                  r'<canvas id="wmCoverageBar">)',
                  '<div class="card-title">Страниц раздела в поиске</div>'
                  '<div class="card-subtitle">Считается по выгрузке статусов '
                  'Вебмастера, а не назначением цели по кластеру</div>',
                  html, count=1)
    # Название раздела в боковом меню и заголовок колонки таблицы.
    html = html.replace("Покрытие страницами", "Страницы в поиске")
    html = html.replace("<th>Покрытие</th>",
                        "<th>Состояние раздела</th>")

    if html != before:
        open(PAGE, "w", encoding="utf-8").write(html)
        print("страница кластеров пересобрана")
    else:
        print("страница кластеров уже совпадает с данными")
    print("групп: %d, запросов в ядре: %d, без кластера: %d"
          % (len(clusters), stats["total"], stats.get("other", 0)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
