#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ужимает фотографии товаров для публикации на лендинге.

Зачем отдельный шаг, если есть fetch_images.py:
  оригиналы с сайта заказчика весят от 300 КБ до 9 МБ. Для календарей
  скачалось 16 файлов, 34 МБ на 14 позиций. В превью карточки товара
  показывается 1100 пикселей ширины, то есть исходник в 2-5 раз крупнее,
  чем нужно, и браузер тянет это на телефоне.

  Разделение по инструментам: fetch_images.py отвечает за «скачать», этот за
  «сделать пригодным для веба». Смешивать их в одном файле не стоит, потому
  что перекачать заново из-за смены ширины не нужно.

Запуск из корня проекта:
  python landings/_scrape/optimize_images.py \
      --src landings/kvartalnyy-kalendar-2027/assets \
      --dst landings/kvartalnyy-kalendar-2027/assets/web
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageOps

sys.stdout.reconfigure(encoding="utf-8")

# 1200 px против 1100 px в разметке карточки: запас на плотные экраны,
# при этом файл в разы легче оригинала.
DEFAULT_MAX_WIDTH = 1200
DEFAULT_QUALITY = 82


def human(n: int) -> str:
    return f"{n // 1024} КБ" if n < 1024 * 1024 else f"{n // 1024 // 1024} МБ"


def main() -> int:
    ap = argparse.ArgumentParser(description="Ужимает фотографии товаров для лендинга.")
    ap.add_argument("--src", required=True, help="папка с оригиналами")
    ap.add_argument("--dst", required=True, help="папка для веб-версий")
    ap.add_argument("--max-width", type=int, default=DEFAULT_MAX_WIDTH)
    ap.add_argument("--quality", type=int, default=DEFAULT_QUALITY)
    args = ap.parse_args()

    src = Path(args.src)
    dst = Path(args.dst)
    if not src.is_dir():
        print(f"Нет папки с оригиналами: {src}")
        return 1
    dst.mkdir(parents=True, exist_ok=True)

    # GIF включён намеренно. На сайте заказчика 14 снимков приходят
    # именно в GIF, и в прошлый раз они молча пропускались: расширение
    # не было в списке, исключения не возникало, скрипт отчитывался об
    # успехе, а в лендинге эти позиции остались с битой картинкой.
    # Молчаливый пропуск хуже падения: он выглядит как «всё обработано».
    sources = [p for p in sorted(src.iterdir()) if p.is_file() and p.suffix.lower() in
               (".jpg", ".jpeg", ".png", ".webp", ".gif")]

    # Всё, что лежит в папке, но не попало в обработку, обязано быть
    # названо. Молчаливый пропуск хуже падения: скрипт отчитывается об
    # успехе, а на лендинге картинка остаётся битой, и это видно только
    # человеку в браузере. Именно так пропали четырнадцать GIF, а потом
    # ещё файл с двойным расширением `.jpg.gif`.
    skipped = [p for p in sorted(src.iterdir())
               if p.is_file() and p not in sources]
    if skipped:
        print(f"  ! ПРОПУЩЕНО {len(skipped)} файлов, расширение не в списке:")
        for p in skipped[:10]:
            print(f"      {p.name}")
        if len(skipped) > 10:
            print(f"      и ещё {len(skipped) - 10}")
    if not sources:
        print(f"В {src} нет изображений.")
        return 1

    before = after = 0
    rows = []
    for p in sources:
        out = dst / (p.stem + ".jpg")
        try:
            with Image.open(p) as im:
                # Многорамочные анимации берутся первым кадром. На сайте
                # заказчика все GIF однорамочные, но если появится
                # анимация, сохранение второго кадра поверх первого
                # оставило бы в .jpg случайный кусок кадра.
                im.seek(0)
                im = ImageOps.exif_transpose(im)
                # Прозрачность в JPEG не переносится, белый фон вместо неё.
                # Фото товаров на сайте идут на белом, расхождение не видно.
                # Режим P это палитра, типичный для GIF, и альфа-канал у
                # него появляется только после перевода в RGBA.
                if im.mode in ("RGBA", "LA", "P"):
                    im = im.convert("RGBA")
                    canvas = Image.new("RGB", im.size, (255, 255, 255))
                    canvas.paste(im, mask=im.split()[-1])
                    im = canvas
                elif im.mode != "RGB":
                    im = im.convert("RGB")
                w, h = im.size
                if w > args.max_width:
                    im = im.resize((args.max_width, round(h * args.max_width / w)), Image.LANCZOS)
                im.save(out, "JPEG", quality=args.quality, optimize=True, progressive=True)
        except Exception as e:
            print(f"  ! {p.name}: {type(e).__name__} {e}")
            continue
        b, a = p.stat().st_size, out.stat().st_size
        before += b
        after += a
        rows.append((p.name, b, out.name, a))

    print(f"{'оригинал':<52} {'было':>9} {'стало':>9}  {'экономия':>8}")
    for name, b, outname, a in rows:
        ratio = f"{a / b * 100:.0f}%" if b else "-"
        print(f"{name[:50]:<52} {human(b):>9} {human(a):>9}  {ratio:>8}")
    print()
    print(f"Файлов: {len(rows)} | было {human(before)} | стало {human(after)} | "
          f"сокращение {before / after:.1f}x" if after else "ничего неOptimized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
