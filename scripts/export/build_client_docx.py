#!/usr/bin/env python3
"""Сборка CLIENT_REPORT.docx из CLIENT_REPORT.md.

Зачем: docx раньше делали руками, и он разошёлся с md и с сайтом (в нём
стояли 717 URL вместо 708 и не было 55 ТОП-3, 134 ссылок, 257 000 ₽).
Теперь документ всегда собирается из md, поэтому расхождений быть не может.

Запуск из корня проекта:
  python scripts/export/build_client_docx.py
"""
import os
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SRC = ROOT / "CLIENT_REPORT.md"
OUT = ROOT / "CLIENT_REPORT.docx"

ACCENT = RGBColor(0x1F, 0x6F, 0xEB)
DARK = RGBColor(0x11, 0x18, 0x27)


def clean(text):
    return re.sub(r"[*`]", "", text).strip()


def add_inline(par, text):
    """Поддержка **жирного** внутри строки."""
    for i, part in enumerate(re.split(r"(\*\*[^*]+\*\*)", text)):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            r = par.add_run(part[2:-2])
            r.bold = True
        else:
            par.add_run(part)


def build():
    lines = SRC.read_text(encoding="utf-8").splitlines()
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10.5)

    i = 0
    tables = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            i += 1
            continue
        if line.startswith("|") and i + 1 < len(lines) and set(lines[i + 1].replace("|", "").replace(" ", "")) <= set("-:"):
            header = [clean(c) for c in line.strip("|").split("|")]
            i += 2
            body = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                body.append([clean(c) for c in lines[i].strip().strip("|").split("|")])
                i += 1
            t = doc.add_table(rows=1, cols=len(header))
            t.style = "Light Grid Accent 1"
            for j, h in enumerate(header):
                cell = t.rows[0].cells[j]
                cell.text = ""
                r = cell.paragraphs[0].add_run(h)
                r.bold = True
            for row in body:
                cells = t.add_row().cells
                for j, v in enumerate(row[:len(header)]):
                    cells[j].text = v
            doc.add_paragraph()
            tables += 1
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            level = len(m.group(1))
            text = clean(m.group(2))
            if level == 1:
                p = doc.add_heading(text, level=0)
            else:
                p = doc.add_heading(text, level=min(level - 1, 3))
            for r in p.runs:
                r.font.color.rgb = ACCENT if level <= 2 else DARK
            i += 1
            continue
        if line.strip() in ("---", "***", "___"):
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(2)
            i += 1
            continue
        if re.match(r"^\s*[-*]\s+", line) or re.match(r"^\s*\d+\.\s+", line):
            text = re.sub(r"^\s*([-*]|\d+\.)\s+", "", line)
            p = doc.add_paragraph(style="List Bullet" if re.match(r"^\s*[-*]\s+", line) else "List Number")
            add_inline(p, text)
            i += 1
            continue
        p = doc.add_paragraph()
        add_inline(p, clean(line))
        i += 1

    doc.save(OUT)
    size = OUT.stat().st_size
    print("Wrote %s (%d таблиц, %.1f KB)" % (OUT, tables, size / 1024))
    txt = OUT and docx_text()
    for probe in ("708", "55 запросов", "134", "257 000", "21 110", "SQI"):
        print("  содержит %-14s %s" % (probe, probe in txt))


def docx_text():
    from docx import Document as D
    d = D(str(OUT))
    parts = [p.text for p in d.paragraphs]
    for t in d.tables:
        for row in t.rows:
            for c in row.cells:
                parts.append(c.text)
    return "\n".join(parts)


if __name__ == "__main__":
    build()
