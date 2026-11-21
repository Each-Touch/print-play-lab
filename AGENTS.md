# Each-Touch Print-Play Lab — Autonomous Operating Manual (`AGENTS.md`)

> Scope: `/Users/zhaozixu/.gemini/antigravity/scratch/print-play-lab`
> Schedule: Wed/Sun 16:00 Asia/Shanghai
> Positioning: Printable Solo Roll-and-Write Tabletop Games & Mathematically Verified Logic Puzzle Books (US Letter + A4, Color & Ink-Saver B&W — ZERO Generative AI).

## Strict Red Lines
1. **Zero Collision**: NEVER touch `运营总台/`, `game-studio-ops/`, `each-touch-arcade/`, `forge-tools/`, `asset-lab/`, `dev-kits/`, or existing personal `ego-browser` spaces (`2, 3, 27, 31, 50, 51, 54, 61, 77`).
2. **Paywall Protection**: Paid full editions MUST match `releases/*/*-full-*` or `releases/*/paid_*` and `work_tmp/` MUST stay in `.gitignore` so paid PDFs NEVER enter public GitHub repos! Only showcase pages + lightweight 3-page free sample PDFs go to GitHub Pages; full PDF ZIPs upload ONLY to `itch.io` behind the Paid paywall (`$2.50–$2.99` + Free Sample Demo).
3. **Mathematical Verification + Exact Print Paging**: Every generated dungeon/puzzle MUST be programmatically solved/verified (`BFS` / SAT / backtracking) before rendering PDFs, and every PDF page count must match exact spec via Chromium CDP `Page.printToPDF`.
4. **Zero Generative AI & Zero External CDNs**: All art, icons, grids, and layouts are vector SVG/HTML/CSS; `Generative AI disclosure` on itch.io MUST be `No`.
5. **Browser & Visual Audit Gate**: Fresh temporary `taskSpace(...)`, close with `await task.finish({ keep: [] })`; never `read_file` PNGs in main conversation (`research` `Model: "pro"` only). Never submit personal tax/bank forms.

## 5-Stage Autonomous Production Loop
1. Run `python3 scripts/fetch_metrics.py` & inspect `https://itch.io/dashboard` (read-only); pick next `TODO` from `ops/01_海外可打印桌游与谜题排期池.md` (`IN_PROGRESS`).
2. Generate verified procedural game/puzzle HTML sheets → render US Letter Color, US Letter B&W, A4 B&W + 3-map Free Sample PDF via Chromium CDP `Page.printToPDF` → verify PDF headers & exact page counts (`package_book.py`) → build showcase (`build_showcase.py`).
3. Run temporary HTTP QA (`1280x800` & `390x844`) and `research` (`Model: "pro"`) visual audit on cover, spread preview, desktop & mobile showcase until `VERDICT: PASS`.
4. Verify `git status` excludes Paid Full ZIPs & `work_tmp/`, push `Each-Touch/print-play-lab` `main`, verify `https://each-touch.github.io/print-play-lab/` `HTTP 200`; publish to `itch.io` (`Classification: Physical games`, `Paid` `$2.50–$2.99`, Free Demo PDF checked Demo, `Generative AI: No`), publish `Public`, verify live Buy/Demo CTAs.
5. Update `books-catalog.json` with live `itchUrl`, rebuild showcase, mark `DONE`, log metrics & lessons in `ops/00..02`, commit & push.
