#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Заглушка Битрикс24 для проверки приёма заявок. Только для тестов.

Зачем. Настоящий портал Битрикс24 у заказчика закрытый коробочный, а
проверить надо не «сходилось ли в реальную CRM», а одну конкретную вещь:
доезжает ли город доставки и остальные поля до карточки лида. Для этого
реальная CRM не нужна, нужна точка, которая ведёт себя как вебхук
`crm.lead.add.json` и складывает лиды в файл.

Скрипт поднимает HTTP-сервер, эмулирующий входящий вебхук Битрикс24:
принимает POST с JSON, проверяет обязательные поля и дописывает лид в
`out/leads.json`. Дальше по нему можно смотреть глазами, что реально
пришло в CRM.

Это НЕ Битрикс24. Никакой совместимости с коробкой тут нет: настоящий
портл живёт на другой стороне и недоступен отсюда. Проверяется формат
вызова и то, что обработчик не теряет поля.

Запуск из корня проекта:
  python landings/php/_fake_b24.py --port 8322
"""
from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

OUT = Path(__file__).resolve().parent.parent / "_scrape" / "out"
LEADS = OUT / "leads.json"

REQUIRED = ("TITLE", "NAME", "PHONE")


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802  имя задано базовым классом
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception as e:
            self._send(200, {"error": "bad_json",
                             "error_description": str(e)})
            return

        fields = data.get("fields") or {}

        # Настоящий Битрикс24 молча игнорирует несуществующие имена
        # полей и лишние ключи, поэтому заглушка ведёт себя так же и
        # записывает всё, что пришло. Так видно, что обработчик не
        # присылает мусор.
        missing = [f for f in REQUIRED if not fields.get(f)]
        if missing:
            self._send(200, {
                "error": "VALIDATION",
                "error_description": "нет полей: " + ", ".join(missing),
            })
            return

        OUT.mkdir(parents=True, exist_ok=True)
        leads = []
        if LEADS.exists():
            try:
                leads = json.loads(LEADS.read_text(encoding="utf-8"))
            except Exception:
                leads = []
        lead_id = 1000 + len(leads) + 1
        leads.append({"id": lead_id, "fields": fields, "raw_top_level": {
            k: v for k, v in data.items() if k != "fields"
        }})
        LEADS.write_text(json.dumps(leads, ensure_ascii=False, indent=1),
                         encoding="utf-8")

        print(f"[fake-b24] лид #{lead_id}: {fields.get('TITLE')}", flush=True)
        self._send(200, {"result": lead_id})

    def do_GET(self) -> None:  # noqa: N802
        # Битрикс24 для чтения лида использует методы класса crm.*,
        # здесь один простой, чтобы можно было проверить глазом.
        leads = json.loads(LEADS.read_text(encoding="utf-8")) if LEADS.exists() else []
        self._send(200, {"result": leads})

    def log_message(self, fmt: str, *a) -> None:
        pass  # тихо, чтобы не мешать выводу теста


def main() -> int:
    ap = argparse.ArgumentParser(description="Заглушка вебхука Битрикс24 для тестов.")
    ap.add_argument("--port", type=int, default=8322)
    ap.add_argument("--reset", action="store_true",
                    help="очистить накопленные лиды перед стартом")
    args = ap.parse_args()

    if args.reset and LEADS.exists():
        LEADS.unlink()

    srv = HTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Заглушка Битрикс24 на http://127.0.0.1:{args.port}, "
          f"лиды пишутся в {LEADS}", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
