#!/usr/bin/env python3
"""Sort loose media files into category folders.

Use case:
- User dropped images directly into one directory (not category folders).
- We need a quick test workflow for sorting/classification before full pipeline.

Modes:
1) Filename keyword heuristics (default, no API key required).
2) Optional Gemini vision classification if API key is provided.
"""

from __future__ import annotations

import argparse
import os
import shutil
from dataclasses import dataclass
from pathlib import Path


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

CATEGORY_RULES: dict[str, tuple[str, ...]] = {
    "ФЛЕШКИ": ("flash", "usb", "флеш", "флэ", "накоп"),
    "ПАУЭРБАНКИ": ("powerbank", "power-bank", "пауэр", "power bank", "pbank"),
}


@dataclass
class SortResult:
    moved: int = 0
    skipped: int = 0
    unknown: int = 0


def classify_by_filename(filename: str) -> str | None:
    lowered = filename.lower()
    for category, needles in CATEGORY_RULES.items():
        if any(n in lowered for n in needles):
            return category
    return None


def classify_with_gemini(image_path: Path, api_key: str) -> str | None:
    try:
        import google.generativeai as genai
    except ImportError:
        return None

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = (
        "Определи категорию сувенирной продукции на фото. "
        "Ответь ОДНИМ словом из списка: ФЛЕШКИ, ПАУЭРБАНКИ, НЕИЗВЕСТНО."
    )

    try:
        from PIL import Image
    except ImportError:
        return None

    with Image.open(image_path).convert("RGB") as img:
        resp = model.generate_content([prompt, img])

    text = (getattr(resp, "text", "") or "").strip().upper()
    if "ФЛЕШ" in text:
        return "ФЛЕШКИ"
    if "ПАУЭР" in text or "POWERBANK" in text or "POWER BANK" in text:
        return "ПАУЭРБАНКИ"
    return None


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def sort_loose_media(
    source_dir: Path,
    media_root: Path,
    use_gemini: bool,
    gemini_api_key: str | None,
    dry_run: bool,
) -> SortResult:
    result = SortResult()
    unknown_dir = media_root / "НЕРАЗОБРАННОЕ"

    for file_path in sorted(source_dir.iterdir()):
        if not file_path.is_file() or file_path.suffix.lower() not in IMAGE_EXTS:
            continue

        category = classify_by_filename(file_path.name)
        if not category and use_gemini and gemini_api_key:
            category = classify_with_gemini(file_path, gemini_api_key)

        if not category:
            category = "НЕРАЗОБРАННОЕ"
            result.unknown += 1

        target_dir = media_root / category
        ensure_dir(target_dir)

        target_path = target_dir / file_path.name
        if target_path.exists():
            stem = target_path.stem
            suffix = target_path.suffix
            i = 2
            while True:
                candidate = target_dir / f"{stem}-{i}{suffix}"
                if not candidate.exists():
                    target_path = candidate
                    break
                i += 1

        if dry_run:
            print(f"DRY-RUN: {file_path} -> {target_path}")
            result.moved += 1
            continue

        try:
            shutil.move(str(file_path), str(target_path))
            print(f"MOVED: {file_path.name} -> {target_dir.name}/")
            result.moved += 1
        except Exception as exc:
            print(f"SKIP: {file_path.name}: {exc}")
            result.skipped += 1

    ensure_dir(unknown_dir)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Sort loose media files into categories")
    parser.add_argument("--source-dir", type=Path, required=True, help="Directory with loose images")
    parser.add_argument("--media-root", type=Path, default=Path("media"), help="Destination media root")
    parser.add_argument("--use-gemini", action="store_true", help="Enable Gemini vision classification")
    parser.add_argument("--gemini-api-key", default=os.getenv("GEMINI_API_KEY"), help="Gemini API key")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, do not move files")
    args = parser.parse_args()

    if not args.source_dir.exists() or not args.source_dir.is_dir():
        raise SystemExit(f"Invalid --source-dir: {args.source_dir}")

    if args.use_gemini and not args.gemini_api_key:
        raise SystemExit("--use-gemini set, but no API key provided (--gemini-api-key or GEMINI_API_KEY)")

    res = sort_loose_media(
        source_dir=args.source_dir,
        media_root=args.media_root,
        use_gemini=args.use_gemini,
        gemini_api_key=args.gemini_api_key,
        dry_run=args.dry_run,
    )

    print("---")
    print(f"Moved: {res.moved}")
    print(f"Unknown category: {res.unknown}")
    print(f"Skipped: {res.skipped}")
    print(f"Media root: {args.media_root}")
    if not args.use_gemini:
        print("Mode: filename heuristics (no API key required)")
    else:
        print("Mode: Gemini + filename fallback")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
