#!/usr/bin/env python3
"""Prepare a small test dataset bundle (size-capped) from a large photo catalog.

Use this before committing sample data to git.
"""

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from pathlib import Path

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


@dataclass
class PickedFile:
    source: Path
    relative: Path
    size_bytes: int


def bytes_to_mb(value: int) -> float:
    return value / (1024 * 1024)


def collect_images(source_root: Path, include_folders: list[str] | None) -> list[Path]:
    selected_roots: list[Path]
    if include_folders:
        selected_roots = [source_root / folder for folder in include_folders]
    else:
        selected_roots = [p for p in source_root.iterdir() if p.is_dir()]

    images: list[Path] = []
    for root in selected_roots:
        if not root.exists() or not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.suffix.lower() in IMAGE_EXTS:
                images.append(path)
    return images


def pick_with_limits(
    source_root: Path,
    images: list[Path],
    max_total_bytes: int,
    max_per_folder: int,
) -> list[PickedFile]:
    picked: list[PickedFile] = []
    folder_counters: dict[str, int] = {}
    used_bytes = 0

    for img in images:
        rel = img.relative_to(source_root)
        top_folder = rel.parts[0] if rel.parts else ""

        count = folder_counters.get(top_folder, 0)
        if max_per_folder and count >= max_per_folder:
            continue

        size = img.stat().st_size
        if used_bytes + size > max_total_bytes:
            continue

        picked.append(PickedFile(source=img, relative=rel, size_bytes=size))
        folder_counters[top_folder] = count + 1
        used_bytes += size

    return picked


def write_output(picked: list[PickedFile], source_root: Path, output_dir: Path) -> None:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for item in picked:
        dest = output_dir / item.relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item.source, dest)

    manifest = {
        "files": [
            {
                "source": str(item.source),
                "relative": str(item.relative),
                "size_bytes": item.size_bytes,
            }
            for item in picked
        ],
        "file_count": len(picked),
        "total_size_bytes": sum(f.size_bytes for f in picked),
    }

    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a capped-size test dataset")
    parser.add_argument("--source-root", type=Path, required=True, help="Root with original category folders")
    parser.add_argument("--output-dir", type=Path, default=Path("sample_data"), help="Where to place copied sample")
    parser.add_argument("--max-mb", type=float, default=50.0, help="Max total size in MB (default: 50)")
    parser.add_argument("--max-per-folder", type=int, default=20, help="Max files per top-level folder (default: 20)")
    parser.add_argument(
        "--include-folders",
        nargs="*",
        default=None,
        help="Optional list of top-level folders to sample from",
    )
    args = parser.parse_args()

    if not args.source_root.exists() or not args.source_root.is_dir():
        raise SystemExit(f"Source root does not exist or is not a directory: {args.source_root}")

    images = collect_images(args.source_root, args.include_folders)
    if not images:
        raise SystemExit("No images found with supported extensions.")

    max_total_bytes = int(args.max_mb * 1024 * 1024)
    picked = pick_with_limits(
        source_root=args.source_root,
        images=images,
        max_total_bytes=max_total_bytes,
        max_per_folder=args.max_per_folder,
    )

    if not picked:
        raise SystemExit("No files selected. Increase --max-mb or adjust folder filters.")

    write_output(picked=picked, source_root=args.source_root, output_dir=args.output_dir)

    total = sum(p.size_bytes for p in picked)
    print(f"Selected files: {len(picked)}")
    print(f"Total size: {bytes_to_mb(total):.2f} MB")
    print(f"Output dir: {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
