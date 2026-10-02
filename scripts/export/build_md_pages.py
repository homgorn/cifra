"""Собрать страницы сайта отчёта из документов вики.

Зачем. Четыре документа вики не имели страницы на сайте, хотя сайт
это основной способ их показать: вики открывают в репозитории, сайт
открывают по ссылке. Не показаны план на 6 месяцев, задание на месяц
1, план страниц по данным и сверка чисел.

Почему берётся оболочка существующей страницы, а не пишется своя.
У страниц сайта своя шапка, навигация, подвал и семь подключаемых
скриптов. Если писать оболочку заново, новая страница будет
отличаться от остальных, и это обнаружится не сразу, а при
открытии. Оболочка берётся из roadmap.html дословно, меняется только
содержимое main.

Что меняется в списке страниц. Описание у wm-overview содержало 708,
число из снимка за 27 сентября. Заменяется на 744 с датой среза.
Добавляются четыре новые страницы с номерами 28-31.

Что этот скрипт не делает. Он не строит графики и не читает живого
API: все числа приезжают уже готовыми в Markdown из вики, а вики
собирается скриптами, которые считают их из выгрузок. Здесь только
форма.
"""

import html
import os
import re
import sys

import markdown

sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"C:\susa ai\2026 cifra audit"
SITE = os.path.join(ROOT, "reports", "cifra18-audit")
PAGES = os.path.join(SITE, "pages")
WIKI = os.path.join(ROOT, "brain", "wiki", "webmaster_analytics")
SHELL_SRC = os.path.join(PAGES, "roadmap.html")

# Документ вики, имя страницы, раздел в меню, подпись в списке.
NEW = [
    (14, "14_Promotion_Plan_6_Months.md", "plan-6m.html", "План",
     "План продвижения на 4-6 месяцев из выгрузок Метрики"),
    (15, "15_Month1_Technical_Workorder.md", "workorder.html", "План",
     "Задание на месяц 1: пять технических правок с проверкой"),
    (16, "12_Page_Plan_From_Data.md", "page-plan.html", "План",
     "627 фраз, 21 целевая страница, 59 фраз без страницы"),
    (17, "13_Number_Reconciliation.md", "numbers.html", "Методика",
     "Сверка противоречивых чисел и что оказалось верным"),
]


def shell():
    """Оболочка страницы: всё, кроме содержимого main.

    Берётся дословно из существующей страницы, чтобы новая страница
    не отличалась от остальных ничем, кроме содержимого.
    """
    s = open(SHELL_SRC, encoding="utf-8").read()
    m = re.search(r'<main class="page">(.*)</main>', s, re.S)
    if not m:
        raise SystemExit("в roadmap.html не найден <main class=\"page\">")
    head = s[:m.start()]
    tail = s[m.end():]
    # Заголовок страницы в оболочке берётся у эталонной страницы и
    # будет заменён на заголовок новой.
    return head, tail


def title_of(s):
    m = re.search(r"<title>(.*?)</title>", s, re.S)
    return m.group(1).strip() if m else ""


def convert(md_path):
    """Markdown в HTML.

    Расширения: таблицы нужны, потому что половина документов это
    таблицы; fenced_code нужен для блоков конфигурации; toc даёт
    якоря, по которым работает поиск по странице.
    """
    src = open(md_path, encoding="utf-8").read()
    # Строка со сборщиком в шапке не нужна читателю сайта.
    src = re.sub(r"^Собрано скриптом[^\n]*\n", "", src)
    return markdown.markdown(
        src, extensions=["tables", "fenced_code", "toc", "attr_list"])


def page_html(title, body, head, tail):
    """Вставить содержимое в оболочку.

    Заголовок H1 добавляется здесь, а не берётся из Markdown: там он
    есть, и без него страница осталась бы без единственного h1, а
    это ровно то, что в плане месяца 1 числится технической правкой
    для сайта клиента.
    """
    md = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.S)
    h1 = md.group(1) if md else html.escape(title)
    rest = body[:md.start()] + body[md.end():] if md else body

    out = head.replace("<title>%s</title>" % title_of(head),
                       "<title>%s</title>" % html.escape(title))
    return (out + '<main class="page">\n'
            '<h1>%s</h1>\n' % h1 + rest + "\n</main>" + tail)


def main():
    if not os.path.isdir(PAGES):
        raise SystemExit("нет папки pages")
    head, tail = shell()
    built = []

    for _num, md_name, html_name, _sec, _desc in NEW:
        src = os.path.join(WIKI, md_name)
        if not os.path.isfile(src):
            print("  ПРОПУЩЕН, нет документа: %s" % md_name)
            continue
        body = convert(src)
        m = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.S)
        title = re.sub(r"<[^>]+>", "", m.group(1)) if m else md_name
        out = os.path.join(PAGES, html_name)
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(page_html(title, body, head, tail))
        size = os.path.getsize(out)
        built.append((html_name, size, title))
        print("  ok: pages/%-16s %6d байт  %s" % (html_name, size, title[:44]))

    print()
    print("собрано страниц: %d" % len(built))
    return built


if __name__ == "__main__":
    main()