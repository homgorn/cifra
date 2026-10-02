"""Новейшая выгрузка Яндекса, а не заданная и не сегодняшняя.

Зачем отдельный файл. Три сборщика получали дату тремя разными
способами, и все три способа ломались по-разному. Один был намертво
зашит на 2026-09-27, из-за чего пересборка месяцами выдавала числа
трёхдневной давности и выглядела исправной. Второй брал сегодняшнюю
дату, из-за чего запуск в любой день, кроме дня выгрузки, молча
давал нули вместо данных. Третий читал результат пересборки как
источник, то есть вывод принимал за вход.

Здесь одна функция на всех: берётся новейшая папка, в которой лежит
нужный маркерный файл, и она же возвращается вместе с датой, чтобы
дата уезжала с числами в отчёт.

Использование:

    from wm_latest import latest_export
    day = latest_export(WM_BASE)          # newest with summary.json
    api = latest_export(WM_BASE, "indexing_samples.json")
    print(day.name)
"""

import os


def latest_export(base, marker="summary.json"):
    """Новейшая папка выгрузок, в которой есть маркерный файл.

    Папки сортируются по имени, а не по времени изменения файла: имя
    это дата в формате ГГГГ-ММ-ДД и оно единственное, что здесь
    надёжно. Если подходящей папки нет, возвращается None, и вызывающий
    код обязан это развидеть, а не работать с пустым путём.
    """
    if not os.path.isdir(base):
        return None
    names = sorted(n for n in os.listdir(base)
                   if os.path.isdir(os.path.join(base, n)))
    for name in reversed(names):
        p = os.path.join(base, name)
        if os.path.isfile(os.path.join(p, marker)):
            return p
    return None


def latest_day(base, marker="summary.json"):
    """То же, но только имя папки, для подстановки в путь."""
    p = latest_export(base, marker)
    return os.path.basename(p) if p else None
