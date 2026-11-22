#!/usr/bin/env python3
"""Render vector PDFs via Chromium CDP Page.printToPDF and capture cover/spread PNGs."""

from __future__ import annotations

import base64
import re
from pathlib import Path
import fitz
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SLUG = "starship-salvage-40"
REL_DIR = ROOT / "releases" / SLUG
WORK_DIR = REL_DIR / "work_tmp"
SHOTS_DIR = REL_DIR / "screenshots"
CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def print_pdf_cdp(cdp, html_path: Path, pdf_path: Path, expected_pages: int) -> None:
    page_url = html_path.resolve().as_uri()
    cdp.send("Page.navigate", {"url": page_url})
    # Wait briefly for layout & SVG paint
    import time
    time.sleep(0.9)
    res = cdp.send("Page.printToPDF", {
        "preferCSSPageSize": True,
        "printBackground": True,
        "marginTop": 0,
        "marginBottom": 0,
        "marginLeft": 0,
        "marginRight": 0,
    })
    raw = base64.b64decode(res["data"])
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.write_bytes(raw)
    assert raw.startswith(b"%PDF-1."), f"Invalid PDF header in {pdf_path}"
    doc = fitz.open(pdf_path)
    actual_pages = doc.page_count
    regex_pages = len(re.findall(rb"/Type\s*/Page(?![sA-Za-z])", raw))
    doc.close()
    assert actual_pages == expected_pages, f"{pdf_path.name}: expected {expected_pages} pages, got {actual_pages}"
    assert regex_pages == expected_pages, f"{pdf_path.name}: regex /Type /Page count {regex_pages} != {expected_pages}"
    print(f"Rendered {pdf_path.name}: {actual_pages} pages, {len(raw)} bytes")


def main() -> int:
    SHOTS_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME_PATH, headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720}, device_scale_factor=1)
        page = context.new_page()
        cdp = context.new_cdp_session(page)
        cdp.send("Page.enable")

        jobs = [
            (WORK_DIR / "full_letter_color.html", WORK_DIR / "starship_salvage_40_letter_color.pdf", 42),
            (WORK_DIR / "full_letter_bw.html", WORK_DIR / "starship_salvage_40_letter_bw.pdf", 42),
            (WORK_DIR / "full_a4_bw.html", WORK_DIR / "starship_salvage_40_a4_bw.pdf", 42),
            (WORK_DIR / "demo_3maps_letter.html", REL_DIR / "starship-salvage-40-free-demo-3maps.pdf", 5),
        ]
        for hpath, ppath, exp in jobs:
            print_pdf_cdp(cdp, hpath, ppath, exp)

        # Capture 1280x720 spread preview
        page.goto((WORK_DIR / "sample_preview_spread.html").resolve().as_uri(), wait_until="load")
        page.set_viewport_size({"width": 1280, "height": 720})
        page.screenshot(path=str(SHOTS_DIR / "preview_spread_1280x720.png"))
        print(f"Captured {SHOTS_DIR / 'preview_spread_1280x720.png'}")

        # Capture 630x500 itch.io cover
        page.set_viewport_size({"width": 630, "height": 500})
        page.goto((ROOT / "scripts" / "render_cover_starship40.html").resolve().as_uri(), wait_until="load")
        page.screenshot(path=str(REL_DIR / "cover_630x500.png"))
        print(f"Captured {REL_DIR / 'cover_630x500.png'}")

        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
