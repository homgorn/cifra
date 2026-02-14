#!/usr/bin/env python3
"""List large tracked files from git index (helpful before push)."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def run(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, text=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check tracked files larger than threshold")
    parser.add_argument("--threshold-mb", type=float, default=20.0)
    parser.add_argument("--top", type=int, default=50)
    args = parser.parse_args()

    threshold_bytes = int(args.threshold_mb * 1024 * 1024)

    output = run(["git", "ls-files"]).splitlines()
    sizes: list[tuple[int, str]] = []
    for rel in output:
        p = Path(rel)
        if p.exists() and p.is_file():
            sizes.append((p.stat().st_size, rel))

    sizes.sort(reverse=True)
    large = [(s, p) for s, p in sizes if s >= threshold_bytes]

    print(f"Tracked files: {len(sizes)}")
    print(f"Threshold: {args.threshold_mb:.2f} MB")
    print(f"Large files found: {len(large)}")

    for size, rel in large[: args.top]:
        print(f"{size / (1024 * 1024):8.2f} MB  {rel}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
