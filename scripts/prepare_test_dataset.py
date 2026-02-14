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


@dataclass
class SkipStats:
    skipped_by_file_size: int = 0
    skipped_by_total_size: int = 0
    skipped_by_folder_limit: int = 0


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
    max_file_bytes: int,
) -> tuple[list[PickedFile], SkipStats, list[dict[str, str]]]:
    picked: list[PickedFile] = []
    folder_counters: dict[str, int] = {}
    used_bytes = 0
    stats = SkipStats()
    skipped_examples: list[dict[str, str]] = []

    for img in images:
        rel = img.relative_to(source_root)
        top_folder = rel.parts[0] if rel.parts else ""
        size = img.stat().st_size

        count = folder_counters.get(top_folder, 0)
        if max_per_folder and count >= max_per_folder:
            stats.skipped_by_folder_limit += 1
            continue

        if max_file_bytes and size > max_file_bytes:
            stats.skipped_by_file_size += 1
            if len(skipped_examples) < 20:
                skipped_examples.append(
                    {
                        "relative": str(rel),
                        "reason": "file_too_large",
                        "size_mb": f"{bytes_to_mb(size):.2f}",
                    }
                )
            continue

        if used_bytes + size > max_total_bytes:
            stats.skipped_by_total_size += 1
            continue

        picked.append(PickedFile(source=img, relative=rel, size_bytes=size))
        folder_counters[top_folder] = count + 1
        used_bytes += size

    return picked, stats, skipped_examples


def write_output(
    picked: list[PickedFile],
    output_dir: Path,
    stats: SkipStats,
    skipped_examples: list[dict[str, str]],
    source_root: Path,
    max_file_bytes: int,
    max_total_bytes: int,
) -> None:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for item in picked:
        dest = output_dir / item.relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item.source, dest)

    manifest = {
        "source_root": str(source_root),
        "limits": {
            "max_total_mb": round(bytes_to_mb(max_total_bytes), 2),
            "max_file_mb": round(bytes_to_mb(max_file_bytes), 2),
        },
        "stats": {
            "file_count": len(picked),
            "total_size_bytes": sum(f.size_bytes for f in picked),
            "skipped_by_file_size": stats.skipped_by_file_size,
            "skipped_by_total_size": stats.skipped_by_total_size,
            "skipped_by_folder_limit": stats.skipped_by_folder_limit,
        },
        "skipped_examples": skipped_examples,
        "files": [
            {
                "source": str(item.source),
                "relative": str(item.relative),
                "size_bytes": item.size_bytes,
            }
            for item in picked
        ],
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
    parser.add_argument("--max-file-mb", type=float, default=8.0, help="Max single image size in MB (default: 8)")
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
    max_file_bytes = int(args.max_file_mb * 1024 * 1024)
    picked, stats, skipped_examples = pick_with_limits(
        source_root=args.source_root,
        images=images,
        max_total_bytes=max_total_bytes,
        max_per_folder=args.max_per_folder,
        max_file_bytes=max_file_bytes,
    )

    if not picked:
        raise SystemExit(
            "No files selected. Increase --max-mb/--max-file-mb, or adjust --include-folders/--max-per-folder."
        )

    write_output(
        picked=picked,
        output_dir=args.output_dir,
        stats=stats,
        skipped_examples=skipped_examples,
        source_root=args.source_root,
        max_file_bytes=max_file_bytes,
        max_total_bytes=max_total_bytes,
    )

    total = sum(p.size_bytes for p in picked)
    print(f"Selected files: {len(picked)}")
    print(f"Total size: {bytes_to_mb(total):.2f} MB")
    print(f"Skipped by file size: {stats.skipped_by_file_size}")
    print(f"Skipped by total size: {stats.skipped_by_total_size}")
    print(f"Output dir: {args.output_dir}")
    print(f"Manifest: {args.output_dir / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
