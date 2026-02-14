#!/usr/bin/env python3
"""Run a practical smoke test for current tooling.

- Verifies whether real images exist in repo.
- Always runs synthetic tests for sorter + dataset prep + CSV validator.
- Optionally can test a provided real directory with loose images.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path


def run(cmd: list[str]) -> None:
    print("$", " ".join(cmd))
    subprocess.run(cmd, check=True)


def create_dummy(path: Path, kb: int = 4) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\0" * kb * 1024)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run smoke tests for media pipeline scripts")
    parser.add_argument(
        "--real-loose-dir",
        type=Path,
        default=None,
        help="Optional directory with real loose images for dry-run sorting test",
    )
    args = parser.parse_args()

    # 1) Check if repo has real images
    repo = Path(".").resolve()
    images = list(repo.glob("*.jpg")) + list(repo.glob("*.jpeg")) + list(repo.glob("*.png"))
    print(f"Repo root images found: {len(images)}")

    with tempfile.TemporaryDirectory(prefix="cifra_smoke_") as tmp:
        t = Path(tmp)
        loose = t / "loose"
        create_dummy(loose / "usb_flash_01.jpg")
        create_dummy(loose / "powerbank_black.jpeg")
        create_dummy(loose / "random_item.png")

        media = t / "media"
        sample_src = t / "sample_src"
        (sample_src / "A").mkdir(parents=True)
        (sample_src / "B").mkdir(parents=True)
        create_dummy(sample_src / "A" / "a.jpg", kb=16)
        create_dummy(sample_src / "A" / "b.jpg", kb=12)
        create_dummy(sample_src / "B" / "c.jpg", kb=8)

        # 2) Sorter dry-run + real run (synthetic)
        run(["python3", "scripts/sort_loose_media.py", "--source-dir", str(loose), "--media-root", str(media), "--dry-run"])
        run(["python3", "scripts/sort_loose_media.py", "--source-dir", str(loose), "--media-root", str(media)])

        # 3) Prepare dataset
        sample_out = t / "sample_data"
        run(
            [
                "python3",
                "scripts/prepare_test_dataset.py",
                "--source-root",
                str(sample_src),
                "--output-dir",
                str(sample_out),
                "--max-mb",
                "1",
                "--max-file-mb",
                "0.1",
                "--max-per-folder",
                "5",
            ]
        )

        # 4) Validator check
        run(["python3", "scripts/validate_portfolio_csv.py", "templates/wp_portfolio_template.csv"])

        # 5) Optional real-dir dry run
        if args.real_loose_dir:
            if args.real_loose_dir.exists() and args.real_loose_dir.is_dir():
                real_out = t / "real_media_preview"
                run(
                    [
                        "python3",
                        "scripts/sort_loose_media.py",
                        "--source-dir",
                        str(args.real_loose_dir),
                        "--media-root",
                        str(real_out),
                        "--dry-run",
                    ]
                )
            else:
                print(f"WARNING: --real-loose-dir not found: {args.real_loose_dir}")

        # keep tiny summary artifact path
        summary = t / "summary.txt"
        summary.write_text("smoketest passed\n", encoding="utf-8")
        print(f"Temp test dir: {t}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
