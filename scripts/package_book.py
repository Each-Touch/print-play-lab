#!/usr/bin/env python3
"""Verify rendered PDFs (%PDF header & exact page counts) and package Paid Full ZIP."""

from __future__ import annotations

import argparse
import re
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

BOOK_SPECS = {
    "pocket-dungeon-50": {
        "pages": 52,
        "demo_pages": 5,
        "prefix": "pocket_dungeon_50",
        "demo_name": "pocket-dungeon-free-3-maps-demo.pdf",
        "zip_name": "pocket-dungeon-50-maps-full-pnp.zip",
        "title": "POCKET DUNGEON",
        "count_label": "50-map",
    },
    "starship-salvage-40": {
        "pages": 42,
        "demo_pages": 5,
        "prefix": "starship_salvage_40",
        "demo_name": "starship-salvage-40-free-demo-3maps.pdf",
        "zip_name": "starship-salvage-40-full-pnp.zip",
        "title": "STARSHIP SALVAGE",
        "count_label": "40-deck",
    },
}


def verify_pdf(path: Path, expected_pages: int) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"Missing PDF: {path}")
    raw = path.read_bytes()
    assert raw.startswith(b"%PDF-1."), f"Invalid PDF header in {path}"
    assert len(raw) > 50_000, f"PDF suspiciously small ({len(raw)} bytes): {path}"
    pages_found = len(re.findall(rb"/Type\s*/Page(?![sA-Za-z])", raw))
    assert pages_found == expected_pages, f"{path.name}: expected {expected_pages} pages, found {pages_found}"
    print(f"Verified PDF {path.name}: {pages_found} pages, {len(raw)} bytes")


def package_slug(slug: str) -> int:
    if slug not in BOOK_SPECS:
        raise ValueError(f"Unknown book slug: {slug}")
    spec = BOOK_SPECS[slug]
    rel_dir = ROOT / "releases" / slug
    work_dir = rel_dir / "work_tmp"
    p = spec["prefix"]
    n_pages = spec["pages"]

    lc = work_dir / f"{p}_letter_color.pdf"
    lbw = work_dir / f"{p}_letter_bw.pdf"
    a4 = work_dir / f"{p}_a4_bw.pdf"
    demo = rel_dir / spec["demo_name"]

    verify_pdf(lc, n_pages)
    verify_pdf(lbw, n_pages)
    verify_pdf(a4, n_pages)
    verify_pdf(demo, spec["demo_pages"])

    docs_demo = ROOT / "docs" / "demos" / spec["demo_name"]
    docs_demo.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(demo, docs_demo)

    print_guide = f"""{spec['title']} — PRINTING & PLAY GUIDE (US LETTER + A4)

Included PDFs:
1. {lc.name}  — {n_pages} pages (Cover + Rules + Full Color Sheets, US Letter 8.5x11")
2. {lbw.name}     — {n_pages} pages (Ink-Saver Black & White, US Letter 8.5x11")
3. {a4.name}         — {n_pages} pages (Ink-Saver Black & White, Global A4 210x297mm)

Recommended Printing:
- Print at 100% scale ("Actual Size" / "Fit to Printable Area: Off").
- Slip your favorite sheets into clear sheet protectors and use dry-erase markers for endless solo replays!
"""

    personal_license = f"""Each-Touch Print-Play Lab — Personal Print & Play License
You are granted unlimited personal printing rights for home, solo, travel, and family tabletop play.
Please do not redistribute or resell the full {spec['count_label']} PDF bundle commercially.
Need a free sample to share with friends? Share the Free 3-Sheet Sample PDF at:
https://each-touch.github.io/print-play-lab/
"""

    full_zip = rel_dir / spec["zip_name"]
    with zipfile.ZipFile(full_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(lc, arcname=lc.name)
        zf.write(lbw, arcname=lbw.name)
        zf.write(a4, arcname=a4.name)
        zf.writestr("README_PRINT_GUIDE.txt", print_guide.encode("utf-8"))
        zf.writestr("LICENSE_PERSONAL_PRINT.txt", personal_license.encode("utf-8"))

    with zipfile.ZipFile(full_zip, "r") as zf:
        assert zf.testzip() is None
        names = zf.namelist()
        assert len(names) == 5, f"Expected 5 entries in ZIP, got {names}"
        print(f"ZIP contents: {names}")
    print(f"Packaged Paid Full ZIP -> {full_zip} ({full_zip.stat().st_size} bytes)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", default="starship-salvage-40")
    args = parser.parse_args()
    return package_slug(args.slug)


if __name__ == "__main__":
    raise SystemExit(main())
