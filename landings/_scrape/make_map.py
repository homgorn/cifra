#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Собирает статичную карту места из тайлов OpenStreetMap.

Зачем это нужно. В шаблоне лендинга карта стояла iframe'ом со ссылкой
на Яндекс.Карты, и она не работала: домен yandex.ru отдаёт 301 на
yandex.com, а у него в заголовке `X-Frame-Options: DENY`. Браузер
отказывается показывать страницу во фрейме, и на месте карты пустое
белое поле. Это не лечится подменой ссылки: запрет стоит на стороне
Яндекса, и сделать из iframe карту нельзя.

Варианты были три: оставить пустое поле, показать картинку-заглушку
или показать настоящую карту. Сделана настоящая, просто статичная.
Плюсы: работает везде, не грузит посторонний iframe на странице
лендинга, не отправляет посетителя стороннему домену, работает без
JavaScript. Минус один: карта не панорамируется и не масштабируется.
Для адреса типографии это приемлемо, а кнопка «Проложить маршрут»
ведёт на Яндекс.Карты, где интерактив есть.

Что здесь принципиально: картинка рисуется ДО публикации и кладётся
рядом с лендингом. Посетитель сайта не ходит к стороннему сервису
за каждым тайлом, а это требование 152-ФЗ к обработке персональных
данных и к согласию на cookie.

Условия использования тайлов OSM требуют корректной атрибуции,
поэтому в scriptmap.py она подставляется в скрипт и видна на странице.
Файл получен из стандартного обработчика OSM в `reference/`, ссылка
на источник данных тоже выводится в подписи.

Запуск из корня проекта:
  python landings/_scrape/make_map.py --lat 56.869771 --lon 53.189062 \
      --out landings/kvartalnyy-kalendar-2027/assets/web/map.png
"""
from __future__ import annotations

import argparse
import io
import math
import os
import sys
import time
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding="utf-8")

# Домен тайлов OpenStreetMap. Использование оформлено как «минимум для
# одной картинки», то есть это не массовая загрузка. Тем не менее
# атрибуция обязательна, и она подставляется на картинку.
TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
# С User-Agent, который прямо называет, кто запрашивает и зачем. OSM
# просит идентифицировать себя; браузерный User-Agent здесь не годится,
# потому что картинку собирает скрипт на нашей машине.
UA = ("CifraLandingBuilder/1.0 (build-time static map image for a landing page; "
      "contact: project owner)")
TILE_PX = 256


def lonlat_to_tile(lon: float, lat: float, zoom: int) -> tuple[int, int]:
    """Стандартный веб-меркатор, XYZ-схема."""
    lat = max(min(lat, 85.05112878), -85.05112878)
    n = 2 ** zoom
    xtile = int((lon + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n)
    return max(min(xtile, n - 1), 0), max(min(ytile, n - 1), 0)


def fetch_tile(x: int, y: int, zoom: int) -> Image.Image | None:
    url = TILE_URL.format(z=zoom, x=x, y=y)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=20) as resp:
            if resp.status != 200:
                return None
            return Image.open(io.BytesIO(resp.read())).convert("RGB")
    except Exception as e:
        print(f"  ! тайл {zoom}/{x}/{y}: {type(e).__name__} {e}")
        return None


# Шрифт для подписей на карте. Дефолтный шрифт Pillow это растровый
# ASCII, и кириллица в нём рисуется квадратами: «Типография Цифра»
# превращалась в «□□□□□□□□ □□□». Шрифт берётся из системной папки,
# при отсутствии остаётся ASCII-строка.
def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in ("segoeui.ttf", "arial.ttf", "tahoma.ttf", "verdana.ttf"):
        p = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts" / name
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except OSError:
                continue
    return ImageFont.load_default()


def build(lat: float, lon: float, zoom: int, cols: int, rows: int,
          marker_label: str) -> Image.Image | None:
    """Собирает полотно из тайлов и рисует метку в центре."""
    cx, cy = lonlat_to_tile(lon, lat, zoom)
    x0 = cx - cols // 2
    y0 = cy - rows // 2

    canvas = Image.new("RGB", (cols * TILE_PX, rows * TILE_PX), "#e8e6e1")
    missing = 0
    for dy in range(rows):
        for dx in range(cols):
            tile = fetch_tile(x0 + dx, y0 + dy, zoom)
            if tile is None:
                missing += 1
                continue
            canvas.paste(tile.resize((TILE_PX, TILE_PX), Image.LANCZOS),
                         (dx * TILE_PX, dy * TILE_PX))
            # Пауза между тайлами. Тут это не про вежливость к сервису:
            # без паузы несколько запросов подряд с одного адреса упираются
            # в rate limit и часть тайлов не приходит.
            time.sleep(0.4)

    if missing:
        print(f"  ! не скачано тайлов: {missing} из {cols * rows}. "
              "Пустые места на карте заменены фоном.")

    d = ImageDraw.Draw(canvas)
    font = load_font(19)
    px, py = (cols * TILE_PX) // 2, (rows * TILE_PX) // 2

    # Метка: круг с точкой и белой обводкой, иначе она теряется на
    # пёстрых тайлах. Размер скругления фиксирован, потому что это
    # условный знак, а не часть карты.
    r = 16
    d.ellipse([px - r, py - r, px + r, py + r], fill="#d21e33",
              outline="#ffffff", width=5)
    d.ellipse([px - 5, py - 5, px + 5, py + 5], fill="#ffffff")

    if marker_label:
        # Подпись под меткой, чтобы было видно, что именно тут.
        tw = d.textlength(marker_label, font=font)
        box_x0, box_x1 = px - tw / 2 - 12, px + tw / 2 + 12
        box_y0, box_y1 = py + r + 6, py + r + 36
        d.rectangle([box_x0, box_y0, box_x1, box_y1], fill=(255, 255, 255))
        d.rectangle([box_x0, box_y0, box_x1, box_y1], outline="#d21e33", width=2)
        d.text((px - tw / 2, box_y0 + 9), marker_label, fill="#1a1a1a", font=font)

    # Атрибуция OSM обязательна по условиям использования тайлов.
    attr = "© OpenStreetMap contributors"
    d.rectangle([0, rows * TILE_PX - 28, rows * TILE_PX, rows * TILE_PX],
                fill=(255, 255, 255))
    d.text((8, rows * TILE_PX - 21), attr, fill="#444", font=font)
    return canvas


def main() -> int:
    ap = argparse.ArgumentParser(description="Статичная карта места из тайлов OSM.")
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--out", required=True, help="путь к PNG")
    ap.add_argument("--zoom", type=int, default=14)
    ap.add_argument("--cols", type=int, default=3)
    ap.add_argument("--rows", type=int, default=2)
    ap.add_argument("--label", default="", help="подпись под меткой")
    ap.add_argument("--width", type=int, default=900,
                    help="ширина итоговой картинки в пикселях")
    args = ap.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists() and out.stat().st_size > 2000:
        print(f"Карта уже собрана: {out} ({out.stat().st_size // 1024} КБ)")
        return 0

    print(f"Собираю карту: {args.lat}, {args.lon}, зум {args.zoom}, "
          f"тайлов {args.cols}x{args.rows}")
    img = build(args.lat, args.lon, args.zoom, args.cols, args.rows, args.label)
    if img is None:
        return 1

    # Ужимаем: исходник 1536x1024 весит под мегабайт, а на лендинге
    # карта занимает ширину колонки около 600 пикселей.
    if args.width and img.width > args.width:
        h = round(img.height * args.width / img.width)
        img = img.resize((args.width, h), Image.LANCZOS)
    img.save(out, "PNG", optimize=True)
    # Размер берётся у образа, а не у пути: out это Path, и у него нет
    # ни width, ни height.
    print(f"OK: {out} ({img.width}x{img.height}, {out.stat().st_size // 1024} КБ)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
