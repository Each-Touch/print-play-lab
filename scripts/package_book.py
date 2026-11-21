#!/usr/bin/env python3
"""Verify rendered PDFs (%PDF header & exact page counts) and package Paid Full ZIP."""

from __future__ import annotations

import re
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SLUG = "pocket-dungeon-50"
REL_DIR = ROOT / "releases" / SLUG
WORK_DIR = REL_DIR / "work_tmp"

PRINT_GUIDE = """POCKET DUNGEON — PRINTING & PLAY GUIDE (US LETTER + A4)

Included PDFs:
1. pocket_dungeon_50_letter_color.pdf  — 52 pages (Cover + Rules + 50 Color Maps, US Letter 8.5x11")
2. pocket_dungeon_50_letter_bw.pdf     — 52 pages (Ink-Saver Black & White, US Letter 8.5x11")
3. pocket_dungeon_50_a4_bw.pdf         — 52 pages (Ink-Saver Black & White, Global A4 210x297mm)

Recommended Printing:
- Print at 100% scale ("Actual Size" / "Fit to Printable Area: Off").
- Slip your favorite sheets into clear sheet protectors and use dry-erase markers for endless solo replays!
"""

PERSONAL_LICENSE = """Each-Touch Print-Play Lab — Personal Print & Play License
You are granted unlimited personal printing rights for home, solo, travel, and family tabletop play.
Please do not redistribute or resell the full 50-map PDF bundle commercially.
Need a free sample to share with friends? Share the Free 3-Map Sample PDF at:
https://each-touch.github.io/print-play-lab/
"""


def verify_pdf(path: Path, expected_pages: int) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"Missing PDF: {path}")
    raw = path.read_bytes()
    assert raw.startswith(b"%PDF-1."), f"Invalid PDF header in {path}"
    assert len(raw) > 50_000, f"PDF suspiciously small ({len(raw)} bytes): {path}"
    # Check /Type /Page occurrences cleanly (excluding /Type /Pages)
    pages_found = len(re.findall(rb"/Type\s*/Page(?![sA-Za-z])", raw))
    assert pages_found == expected_pages, f"{path.name}: expected {expected_pages} pages, found {pages_found}"
    print(f"Verified PDF {path.name}: {pages_found} pages, {len(raw)} bytes")


def main() -> int:
    lc = WORK_DIR / "pocket_dungeon_50_letter_color.pdf"
    lbw = WORK_DIR / "pocket_dungeon_50_letter_bw.pdf"
    a4 = WORK_DIR / "pocket_dungeon_50_a4_bw.pdf"
    demo = REL_DIR / "pocket-dungeon-free-3-maps-demo.pdf"

    verify_pdf(lc, 52)
    verify_pdf(lbw, 52)
    verify_pdf(a4, 52)
    verify_pdf(demo, 5)

    docs_demo = ROOT / "docs" / "demos" / "pocket-dungeon-free-3-maps-demo.pdf"
    docs_demo.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(demo, docs_demo)

    full_zip = REL_DIR / "pocket-dungeon-50-maps-full-pnp.zip"
    with zipfile.ZipFile(full_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(lc, arcname="pocket_dungeon_50_letter_color.pdf")
        zf.write(lbw, arcname="pocket_dungeon_50_letter_bw.pdf")
        zf.write(a4, arcname="pocket_dungeon_50_a4_bw.pdf")
        zf.writestr("README_PRINT_GUIDE.txt", PRINT_GUIDE.encode("utf-8"))
        zf.writestr("LICENSE_PERSONAL_PRINT.txt", PERSONAL_LICENSE.encode("utf-8"))

    with zipfile.ZipFile(full_zip, "r") as zf:
        assert zf.testzip() is None
        assert len(zf.namelist()) == 5
    print(f"Packaged Paid Full ZIP -> {full_zip} ({full_zip.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
