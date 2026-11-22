#!/usr/bin/env python3
"""Build Each-Touch Print-Play Lab public GitHub Pages storefront + per-book preview pages."""

from __future__ import annotations

import html
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
CATALOG_PATH = ROOT / "books-catalog.json"
BASE_URL = "https://each-touch.github.io/print-play-lab"

COMMON_CSS = """
    :root {
      --bg: #0b0f14; --surface: #131922; --panel: #19212c; --border: rgba(148,163,184,0.18);
      --text: #f1f5f9; --sec: #b6c4d6; --muted: #8b9bb4; --amber: #f59e0b; --cyan: #38bdf8; --green: #10b981;
      --font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      --mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    * { box-sizing: border-box; }
    html, body { margin: 0; padding: 0; background: var(--bg); color: var(--text); font-family: var(--font); font-size: 14px; line-height: 1.5; overflow-x: hidden; }
    a { color: var(--cyan); text-decoration: none; }
    a:hover { text-decoration: underline; }
    .topbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 10px 18px; background: var(--surface); border-bottom: 1px solid var(--border); flex-wrap: wrap; }
    .brand { display: inline-flex; align-items: center; gap: 10px; color: var(--text); font-weight: 800; font-size: 15px; }
    .mark { width: 28px; height: 28px; border-radius: 7px; background: linear-gradient(135deg, #f59e0b, #d97706); color: #0b0f14; display: inline-flex; align-items: center; justify-content: center; font-family: var(--mono); font-weight: 800; font-size: 13px; }
    .badges { display: flex; gap: 8px; flex-wrap: wrap; }
    .badge { padding: 3px 9px; border-radius: 999px; font-size: 11px; font-weight: 700; border: 1px solid var(--border); background: var(--panel); color: var(--sec); white-space: nowrap; }
    .badge-amber { background: rgba(245,158,11,0.14); border-color: rgba(245,158,11,0.38); color: var(--amber); }
    .badge-cyan { background: rgba(56,189,248,0.14); border-color: rgba(56,189,248,0.38); color: var(--cyan); }
    .badge-green { background: rgba(16,185,129,0.14); border-color: rgba(16,185,129,0.38); color: var(--green); }
    .wrap { max-width: 1180px; margin: 0 auto; padding: 18px 18px 28px; }
    .hero { background: radial-gradient(circle at 86% 18%, rgba(245,158,11,0.16), transparent 45%), var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 22px 24px; display: grid; grid-template-columns: 1.35fr 1fr; gap: 22px; align-items: center; }
    .hero h1 { margin: 8px 0 8px; font-size: clamp(22px, 3vw, 32px); line-height: 1.15; }
    .hero p { margin: 0 0 14px; color: var(--sec); font-size: 14.5px; }
    .btn { display: inline-flex; align-items: center; justify-content: center; padding: 9px 15px; border-radius: 7px; font-weight: 700; font-size: 13px; border: 1px solid rgba(148,163,184,0.3); background: var(--panel); color: var(--text); }
    .btn:hover { text-decoration: none; border-color: var(--cyan); }
    .btn-primary { background: var(--amber); border-color: var(--amber); color: #0b0f14; }
    .hero-stats { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .stat { background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 11px 13px; }
    .stat strong { display: block; color: var(--amber); font-size: 15px; }
    .stat span { font-size: 12px; color: var(--sec); }
    .section-title { margin: 22px 0 10px; font-size: 13px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted); font-weight: 700; }
    .catalog-stack { display: flex; flex-direction: column; gap: 16px; }
    .book-card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 18px; display: grid; grid-template-columns: 1.15fr 1fr; gap: 18px; align-items: center; }
    .book-card h2 { margin: 6px 0 8px; font-size: 20px; }
    .book-card p { margin: 0 0 10px; color: var(--sec); }
    .book-card ul { margin: 0 0 14px; padding-left: 18px; color: var(--sec); font-size: 13px; }
    .spread-img { width: 100%; height: auto; border-radius: 8px; border: 1px solid var(--border); display: block; }
    .ecosystem { margin-top: 22px; background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px; display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; font-size: 12.5px; color: var(--sec); }
    .eco-links { display: flex; gap: 12px; flex-wrap: wrap; }
    @media (max-width: 860px) {
      .hero, .book-card { grid-template-columns: 1fr; padding: 16px; }
    }
"""


def _esc(s: object) -> str:
    return html.escape(str(s or ""), quote=True)


def _sync_images(books: list[dict]) -> None:
    img_dir = DOCS / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    for b in books:
        spread_src = ROOT / "releases" / b["slug"] / "screenshots" / "preview_spread_1280x720.png"
        if spread_src.is_file():
            dest_name = Path(b.get("spreadImage") or f"images/{b['slug']}_spread.png").name
            shutil.copy2(spread_src, img_dir / dest_name)


def _render_book_card(b: dict, prefix: str = "./", include_detail_link: bool = True) -> str:
    itch_url = b.get("itchUrl") or "https://each-touch.itch.io/"
    hl_html = "".join(f"<li>{_esc(h)}</li>" for h in b.get("highlights", []))
    unit_lbl = b.get("unitLabel") or "Maps"
    spread_rel = b.get("spreadImage") or f"images/{b['slug']}_spread.png"
    detail_btn = (
        f'<a class="btn" href="{prefix}{_esc(b["slug"])}/">Book Details</a>'
        if include_detail_link
        else f'<a class="btn" href="{prefix}">All Print &amp; Play Books</a>'
    )
    return f"""
    <section class="book-card">
      <div>
        <span class="badge badge-cyan">{_esc(b['category'])} · ${b['priceUsd']:.2f} USD</span>
        <h2>{_esc(b['shortTitle'])}</h2>
        <p>{_esc(b['tagline'])}</p>
        <ul>{hl_html}</ul>
        <div style="display:flex; gap:10px; flex-wrap:wrap;">
          <a class="btn btn-primary" href="{_esc(itch_url)}" target="_blank" rel="noopener noreferrer">Get Full {b['maps']}-{_esc(unit_lbl)} ZIP (${b['priceUsd']:.2f})</a>
          <a class="btn" href="{prefix}{_esc(b['demoFile'])}" target="_blank" rel="noopener noreferrer">Free {b['demoMaps']}-Sheet Sample PDF</a>
          {detail_btn}
        </div>
      </div>
      <div>
        <img class="spread-img" src="{prefix}{_esc(spread_rel)}" alt="{_esc(b['name'])} sample spread preview" />
      </div>
    </section>
    """


def _render_subpage(b: dict) -> str:
    itch_url = b.get("itchUrl") or "https://each-touch.itch.io/"
    ld_json = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": b["shortTitle"],
            "description": b["tagline"],
            "brand": {"@type": "Brand", "name": "Each-Touch Print-Play Lab"},
            "offers": {
                "@type": "Offer",
                "priceCurrency": "USD",
                "price": str(b["priceUsd"]),
                "availability": "https://schema.org/InStock",
                "url": itch_url,
            },
        },
        ensure_ascii=False,
    )
    card_html = _render_book_card(b, prefix="../", include_detail_link=False)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{_esc(b['name'])} — Each-Touch Print-Play Lab</title>
  <meta name="description" content="{_esc(b['tagline'])}" />
  <link rel="canonical" href="{BASE_URL}/{_esc(b['slug'])}/" />
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%23f59e0b'/%3E%3Ctext x='16' y='21' text-anchor='middle' font-family='monospace' font-weight='800' font-size='14' fill='%230b0f14'%3EPP%3C/text%3E%3C/svg%3E" />
  <script type="application/ld+json">{ld_json}</script>
  <style>{COMMON_CSS}</style>
</head>
<body>
  <header class="topbar">
    <a class="brand" href="../"><span class="mark">PP</span><span>Each-Touch Print-Play Lab</span></a>
    <div class="badges">
      <span class="badge badge-amber">US Letter + A4 PDFs</span>
      <span class="badge badge-green">Algorithm-Verified Solvable</span>
      <span class="badge badge-cyan">Zero Generative AI</span>
    </div>
  </header>
  <main class="wrap">
    <div class="section-title">Print &amp; Play Edition Preview · {_esc(b['pages'])} Vector Pages</div>
    {card_html}
    <footer class="ecosystem">
      <span>Each-Touch Print-Play Lab · <a href="../">Back to Full Catalog</a></span>
      <div class="eco-links">
        <a href="https://each-touch.github.io/forge-tools/" target="_blank" rel="noopener noreferrer">Forge Tools</a>
        <a href="https://each-touch.github.io/asset-lab/" target="_blank" rel="noopener noreferrer">Asset Lab</a>
        <a href="https://each-touch.github.io/dev-kits/" target="_blank" rel="noopener noreferrer">Dev Kits</a>
        <a href="https://each-touch.github.io/" target="_blank" rel="noopener noreferrer">Each-Touch Arcade</a>
      </div>
    </footer>
  </main>
</body>
</html>
"""


def main() -> int:
    books = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / ".nojekyll").touch()
    _sync_images(books)

    featured = books[-1]
    featured_itch = featured.get("itchUrl") or "https://each-touch.itch.io/"
    total_sheets = sum(int(b.get("maps", 0)) for b in books)

    ordered_books = list(reversed(books))
    cards_html = "\n".join(_render_book_card(b, prefix="./", include_detail_link=True) for b in ordered_books)

    ld_items = []
    for b in ordered_books:
        ld_items.append({
            "@context": "https://schema.org",
            "@type": "Product",
            "name": b["shortTitle"],
            "description": b["tagline"],
            "brand": {"@type": "Brand", "name": "Each-Touch Print-Play Lab"},
            "offers": {
                "@type": "Offer",
                "priceCurrency": "USD",
                "price": str(b["priceUsd"]),
                "availability": "https://schema.org/InStock",
                "url": b.get("itchUrl") or "https://each-touch.itch.io/",
            },
        })
    ld_json = json.dumps(ld_items, ensure_ascii=False)

    page_html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Each-Touch Print-Play Lab — Solo Roll &amp; Write Tabletop Games &amp; Verified Puzzle PDFs</title>
  <meta name="description" content="Printable solo roll-and-write tabletop games and verified logic puzzle books (US Letter &amp; A4, Color &amp; Ink-Saver B&amp;W). Download free 3-sheet sample PDFs." />
  <link rel="canonical" href="{BASE_URL}/" />
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%23f59e0b'/%3E%3Ctext x='16' y='21' text-anchor='middle' font-family='monospace' font-weight='800' font-size='14' fill='%230b0f14'%3EPP%3C/text%3E%3C/svg%3E" />
  <script type="application/ld+json">{ld_json}</script>
  <style>{COMMON_CSS}</style>
</head>
<body>
  <header class="topbar">
    <a class="brand" href="./"><span class="mark">PP</span><span>Each-Touch Print-Play Lab</span></a>
    <div class="badges">
      <span class="badge badge-amber">US Letter + A4 PDFs</span>
      <span class="badge badge-green">Algorithm-Verified Solvable</span>
      <span class="badge badge-cyan">Zero Generative AI</span>
    </div>
  </header>

  <main class="wrap">
    <section class="hero">
      <div>
        <span class="badge badge-amber">Printable Solo Tabletop &amp; Logic Puzzle Books</span>
        <h1>Print, Grab 2d6 &amp; Play: Verified Solo Roll-and-Write PDFs</h1>
        <p>Every map, deck plan, and puzzle book is procedurally generated and mathematically verified solvable—bundled in Color + Ink-Saver B&amp;W for both US Letter and Global A4 printers.</p>
        <div style="display:flex; gap:10px; flex-wrap:wrap;">
          <a class="btn btn-primary" href="{_esc(featured_itch)}" target="_blank" rel="noopener noreferrer">New Release: {_esc(featured['name'].split(':')[0])} (${featured['priceUsd']:.2f})</a>
          <a class="btn" href="./{_esc(featured['demoFile'])}" download>Download Free 3-Sheet Sample PDF</a>
        </div>
      </div>
      <div class="hero-stats">
        <div class="stat"><strong>{len(books)} Books · {total_sheets} Sheets</strong><span>Dungeon &amp; Sci-Fi solo PnP lines</span></div>
        <div class="stat"><strong>3 Editions Each</strong><span>Letter Color, Letter B&amp;W, A4 B&amp;W</span></div>
        <div class="stat"><strong>BFS Verified</strong><span>100% guaranteed solvable paths</span></div>
        <div class="stat"><strong>Free Demos</strong><span>3 complete playable sheets per book</span></div>
      </div>
    </section>

    <div class="section-title">Print &amp; Play Catalog ({len(books)} Releases)</div>
    <div class="catalog-stack">
      {cards_html}
    </div>

    <footer class="ecosystem">
      <span>Each-Touch Creative Ecosystem · Printable Games, Dev Kits &amp; Tools</span>
      <div class="eco-links">
        <a href="https://each-touch.github.io/forge-tools/" target="_blank" rel="noopener noreferrer">Forge Tools</a>
        <a href="https://each-touch.github.io/asset-lab/" target="_blank" rel="noopener noreferrer">Asset Lab</a>
        <a href="https://each-touch.github.io/dev-kits/" target="_blank" rel="noopener noreferrer">Dev Kits</a>
        <a href="https://each-touch.github.io/" target="_blank" rel="noopener noreferrer">Each-Touch Arcade</a>
      </div>
    </footer>
  </main>
</body>
</html>
"""
    (DOCS / "index.html").write_text(page_html, encoding="utf-8")

    sitemap_urls = [f"{BASE_URL}/"]
    for b in books:
        sub_dir = DOCS / b["slug"]
        sub_dir.mkdir(parents=True, exist_ok=True)
        (sub_dir / "index.html").write_text(_render_subpage(b), encoding="utf-8")
        sitemap_urls.append(f"{BASE_URL}/{b['slug']}/")

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    url_entries = "\n".join(
        f"  <url>\n    <loc>{u}</loc>\n    <lastmod>{today}</lastmod>\n    <priority>{'1.0' if u == BASE_URL + '/' else '0.9'}</priority>\n  </url>"
        for u in sitemap_urls
    )
    (DOCS / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{url_entries}\n</urlset>\n',
        encoding="utf-8",
    )
    (DOCS / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {BASE_URL}/sitemap.xml\n", encoding="utf-8")
    print(f"Built Print-Play Lab showcase ({len(books)} books) -> {DOCS / 'index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
