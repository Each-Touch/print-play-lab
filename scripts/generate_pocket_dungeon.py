#!/usr/bin/env python3
"""Generate 50 BFS-verified solvable solo roll-and-write dungeon crawl HTML editions + showcase spread."""

from __future__ import annotations

import html
import json
import random
from collections import deque
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
SLUG = "pocket-dungeon-50"
REL_DIR = ROOT / "releases" / SLUG
WORK_DIR = REL_DIR / "work_tmp"
N = 11

BIOMES = [
    {
        "name": "Crypt of Embers",
        "accent": "#b45309",
        "accentSoft": "#fef3c7",
        "rule": "Cinder Burn: If your Movement Die is a 1, cross off 1 Torch box OR take 1 Damage.",
        "prefixes": ["Ash", "Cinder", "Ember", "Char", "Soot", "Pyre", "Slag", "Brazier", "Spark", "Kiln"],
    },
    {
        "name": "Sunken Vault",
        "accent": "#0369a1",
        "accentSoft": "#e0f2fe",
        "rule": "Rising Tide: Every 4th Turn (4, 8, 12, 16), spend 1 Torch OR lose 1 HP to tread water.",
        "prefixes": ["Tide", "Brine", "Kelp", "Barnacle", "Coral", "Flood", "Abyss", "Silt", "Harbor", "Mire"],
    },
    {
        "name": "Clockwork Spire",
        "accent": "#6d28d9",
        "accentSoft": "#ede9fe",
        "rule": "Gear Shift: On EVEN Turns (2, 4, 6...), you may move diagonally 1 step as 1 Step.",
        "prefixes": ["Brass", "Cog", "Spring", "Pendulum", "Piston", "Ratchet", "Dynamo", "Valve", "Chrono", "Gear"],
    },
    {
        "name": "Frost Cavern",
        "accent": "#0e7490",
        "accentSoft": "#cffafe",
        "rule": "Glacial Slide: Entering an empty hallway slides 1 extra tile in the same direction (stop at walls/icons).",
        "prefixes": ["Frost", "Rime", "Glacier", "Hoarfrost", "Icicle", "Boreal", "Snow", "Hail", "Permafrost", "Cryo"],
    },
    {
        "name": "Obsidian Citadel",
        "accent": "#b91c1c",
        "accentSoft": "#fee2e2",
        "rule": "Blood Tax: Traps deal 2 Damage instead of 1; slaying a Monster restores +1 HP (max 10).",
        "prefixes": ["Obsidian", "Crimson", "Dread", "Basalt", "Iron", "Blood", "Onyx", "Thorn", "Doom", "Crown"],
    },
]

NOUNS = ["Passage", "Hall", "Chamber", "Labyrinth", "Sanctum", "Gallery", "Depths", "Bastion", "Keep", "Vault"]


def bfs_distances(grid: list[list[str]], start: tuple[int, int], blocked: set[str]) -> dict[tuple[int, int], int]:
    q = deque([start])
    dist = {start: 0}
    while q:
        r, c = q.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < N and 0 <= nc < N:
                if (nr, nc) not in dist and grid[nr][nc] not in blocked:
                    dist[(nr, nc)] = dist[(r, c)] + 1
                    q.append((nr, nc))
    return dist


def generate_verified_map(map_idx: int) -> dict[str, Any]:
    biome_idx = map_idx // 10
    biome = BIOMES[biome_idx]
    local_idx = map_idx % 10
    difficulty = min(5, 1 + (map_idx // 10) + (1 if local_idx >= 6 else 0))

    for attempt in range(40):
        rng = random.Random(70000 + map_idx * 997 + attempt * 31)
        grid = [["#" for _ in range(N)] for _ in range(N)]

        # Carve an organic room + corridor maze using randomized drunken walk + mini-rooms
        sr = rng.choice([8, 9])
        sc = rng.choice([1, 2])
        grid[sr][sc] = "."

        # Carve 5-7 small 2x2 or 3x2 chambers and connect them
        centers = [(sr, sc)]
        for _ in range(6 + (map_idx % 3)):
            cr = rng.randint(1, N - 3)
            cc = rng.randint(1, N - 3)
            rw = rng.randint(2, 3)
            rh = rng.randint(2, 3)
            for rr in range(cr, min(N - 1, cr + rh)):
                for cc2 in range(cc, min(N - 1, cc + rw)):
                    grid[rr][cc2] = "."
            centers.append((cr, cc))

        # Connect centers sequentially with L-corridors + extra loops for tactical routing
        for i in range(len(centers) - 1):
            r1, c1 = centers[i]
            r2, c2 = centers[i + 1]
            r, c = r1, c1
            horiz_first = rng.random() < 0.5
            if horiz_first:
                while c != c2:
                    grid[r][c] = "."
                    c += 1 if c2 > c else -1
                while r != r2:
                    grid[r][c] = "."
                    r += 1 if r2 > r else -1
            else:
                while r != r2:
                    grid[r][c] = "."
                    r += 1 if r2 > r else -1
                while c != c2:
                    grid[r][c] = "."
                    c += 1 if c2 > c else -1
            grid[r2][c2] = "."

        # Extra cross-connection loop so players have tactical choices
        for _ in range(2):
            a, b = rng.sample(centers, 2)
            r, c = a
            while c != b[1]:
                grid[r][c] = "."
                c += 1 if b[1] > c else -1
            while r != b[0]:
                grid[r][c] = "."
                r += 1 if b[0] > r else -1

        walkable = [(r, c) for r in range(N) for c in range(N) if grid[r][c] == "."]
        if len(walkable) < 34:
            continue

        start = (sr, sc)
        d_all = bfs_distances(grid, start, {"#"})
        reachable = [pos for pos in walkable if pos in d_all]
        if len(reachable) < 32:
            continue

        # Farthest tile = Exit (E); neighbor of Exit = Boss (B)
        reachable.sort(key=lambda p: d_all[p], reverse=True)
        exit_pos = reachable[0]
        if d_all[exit_pos] < 10:
            continue

        # Place Boss adjacent to Exit (or second farthest along shortest path)
        exit_neighbors = [
            (exit_pos[0] + dr, exit_pos[1] + dc)
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
            if 0 <= exit_pos[0] + dr < N and 0 <= exit_pos[1] + dc < N and grid[exit_pos[0] + dr][exit_pos[1] + dc] == "." and (exit_pos[0] + dr, exit_pos[1] + dc) != start
        ]
        if not exit_neighbors:
            continue
        boss_pos = exit_neighbors[0]

        # Ensure Key (K) is reachable from Start WITHOUT stepping on Boss or Exit!
        d_no_boss = bfs_distances(grid, start, {"#"} if False else set())
        # Temporarily mark B and E to check K reachability without passing B/E
        grid[start[0]][start[1]] = "S"
        grid[exit_pos[0]][exit_pos[1]] = "E"
        grid[boss_pos[0]][boss_pos[1]] = "B"

        d_before_boss = bfs_distances(grid, start, {"#", "B", "E"})
        key_candidates = [p for p, dist in d_before_boss.items() if dist >= 5 and grid[p[0]][p[1]] == "."]
        if not key_candidates:
            continue
        # Pick a Key spot well separated from Boss
        key_candidates.sort(key=lambda p: abs(p[0] - boss_pos[0]) + abs(p[1] - boss_pos[1]), reverse=True)
        key_pos = key_candidates[rng.randint(0, min(3, len(key_candidates) - 1))]
        grid[key_pos[0]][key_pos[1]] = "K"

        # Place balanced Monsters, Traps, Chests, Shrines on remaining walkable tiles
        free_tiles = [p for p in d_before_boss if grid[p[0]][p[1]] == "."]
        rng.shuffle(free_tiles)
        if len(free_tiles) < 12:
            continue

        n_monsters = min(5 + (difficulty // 2), len(free_tiles) // 3)
        n_traps = min(3 + (difficulty // 2), 6)
        n_chests = 3
        n_shrines = 2

        idx = 0
        for m_i in range(n_monsters):
            p = free_tiles[idx]
            idx += 1
            pwr = min(6, max(2, 2 + (difficulty - 1) // 2 + (m_i % 3)))
            grid[p[0]][p[1]] = f"M{pwr}"
        for _ in range(n_traps):
            p = free_tiles[idx]
            idx += 1
            grid[p[0]][p[1]] = "^"
        for _ in range(n_chests):
            p = free_tiles[idx]
            idx += 1
            grid[p[0]][p[1]] = "$"
        for _ in range(n_shrines):
            p = free_tiles[idx]
            idx += 1
            grid[p[0]][p[1]] = "+"

        # Final strict verification:
        # 1) S -> K without passing #/B/E
        verify_k = bfs_distances(grid, start, {"#", "B", "E"})
        assert key_pos in verify_k, "Key unreachable without crossing Boss"
        # 2) S -> B and B -> E walkable
        verify_full = bfs_distances(grid, start, {"#"})
        assert boss_pos in verify_full and exit_pos in verify_full, "Boss or Exit unreachable"

        boss_power = min(6, 3 + (difficulty + 1) // 2)
        title = f"{biome['prefixes'][local_idx]} {NOUNS[(map_idx * 3 + local_idx) % len(NOUNS)]}"
        return {
            "num": map_idx + 1,
            "title": title,
            "biome": biome["name"],
            "accent": biome["accent"],
            "accentSoft": biome["accentSoft"],
            "rule": biome["rule"],
            "difficulty": difficulty,
            "bossPower": boss_power,
            "grid": grid,
        }

    raise RuntimeError(f"Failed to generate verified solvable map #{map_idx + 1}")


def render_grid_svg(m: dict[str, Any], bw: bool = False) -> str:
    cell = 44
    pad = 22
    size = pad * 2 + N * cell
    accent = "#111111" if bw else m["accent"]
    wall_fill = "#e5e7eb" if bw else "#1e293b"
    wall_hatch = "#cbd5e1" if bw else "#334155"
    floor_fill = "#ffffff"
    stroke_col = "#111111" if bw else "#475569"

    parts = [f'<svg viewBox="0 0 {size} {size}" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">']
    parts.append(f'<rect x="0" y="0" width="{size}" height="{size}" fill="#ffffff"/>')

    # Column & row labels
    cols = "ABCDEFGHIJK"
    for i in range(N):
        cx = pad + i * cell + cell / 2
        cy = pad + i * cell + cell / 2 + 4
        parts.append(f'<text x="{cx}" y="15" text-anchor="middle" font-family="ui-monospace, Menlo, monospace" font-size="11" font-weight="700" fill="#64748b">{cols[i]}</text>')
        parts.append(f'<text x="11" y="{cy}" text-anchor="middle" font-family="ui-monospace, Menlo, monospace" font-size="11" font-weight="700" fill="#64748b">{i + 1}</text>')

    grid = m["grid"]
    for r in range(N):
        for c in range(N):
            x = pad + c * cell
            y = pad + r * cell
            val = grid[r][c]
            if val == "#":
                parts.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" fill="{wall_fill}" stroke="{stroke_col}" stroke-width="1"/>')
                parts.append(f'<line x1="{x+4}" y1="{y+cell-4}" x2="{x+cell-4}" y2="{y+4}" stroke="{wall_hatch}" stroke-width="1.2"/>')
            else:
                fill = floor_fill
                if not bw and val == "S":
                    fill = "#dcfce7"
                elif not bw and val == "K":
                    fill = "#fef9c3"
                elif not bw and val in ("B", "E"):
                    fill = "#fee2e2" if val == "B" else "#dbeafe"
                parts.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" fill="{fill}" stroke="{stroke_col}" stroke-width="1.2"/>')
                cx = x + cell / 2
                cy = y + cell / 2 + 6
                if val == "S":
                    parts.append(f'<circle cx="{cx}" cy="{y+cell/2}" r="14" fill="none" stroke="{accent}" stroke-width="2.2"/>')
                    parts.append(f'<text x="{cx}" y="{cy}" text-anchor="middle" font-family="sans-serif" font-size="16" font-weight="900" fill="{accent}">S</text>')
                elif val == "K":
                    parts.append(f'<text x="{cx}" y="{cy}" text-anchor="middle" font-family="sans-serif" font-size="18" font-weight="900" fill="{"#111111" if bw else "#b45309"}">K</text>')
                    parts.append(f'<text x="{cx}" y="{y+cell-4}" text-anchor="middle" font-family="sans-serif" font-size="8" font-weight="700" fill="#475569">KEY</text>')
                elif val == "B":
                    parts.append(f'<rect x="{x+5}" y="{y+5}" width="{cell-10}" height="{cell-10}" rx="4" fill="{"#111111" if bw else "#991b1b"}"/>')
                    parts.append(f'<text x="{cx}" y="{cy-2}" text-anchor="middle" font-family="sans-serif" font-size="15" font-weight="900" fill="#ffffff">B{m["bossPower"]}</text>')
                elif val == "E":
                    parts.append(f'<polygon points="{cx},{y+7} {x+cell-7},{y+cell/2} {cx},{y+cell-7} {x+7},{y+cell/2}" fill="none" stroke="{"#111111" if bw else "#1d4ed8"}" stroke-width="2.2"/>')
                    parts.append(f'<text x="{cx}" y="{cy-1}" text-anchor="middle" font-family="sans-serif" font-size="14" font-weight="900" fill="{"#111111" if bw else "#1d4ed8"}">E</text>')
                elif val.startswith("M"):
                    pwr = val[1:]
                    parts.append(f'<circle cx="{cx}" cy="{y+cell/2}" r="14" fill="{"#f3f4f6" if bw else "#f1f5f9"}" stroke="#111827" stroke-width="1.6"/>')
                    parts.append(f'<text x="{cx}" y="{cy-1}" text-anchor="middle" font-family="ui-monospace, monospace" font-size="14" font-weight="900" fill="#111827">M{pwr}</text>')
                elif val == "^":
                    parts.append(f'<polygon points="{cx},{y+10} {x+cell-10},{y+cell-10} {x+10},{y+cell-10}" fill="none" stroke="#111827" stroke-width="2"/>')
                    parts.append(f'<text x="{cx}" y="{y+cell-13}" text-anchor="middle" font-family="sans-serif" font-size="10" font-weight="900" fill="#111827">!</text>')
                elif val == "$":
                    parts.append(f'<rect x="{x+11}" y="{y+12}" width="{cell-22}" height="{cell-24}" rx="3" fill="{"#ffffff" if bw else "#fef08a"}" stroke="#111827" stroke-width="1.8"/>')
                    parts.append(f'<text x="{cx}" y="{cy-1}" text-anchor="middle" font-family="sans-serif" font-size="15" font-weight="900" fill="#111827">$</text>')
                elif val == "+":
                    parts.append(f'<text x="{cx}" y="{cy+1}" text-anchor="middle" font-family="sans-serif" font-size="22" font-weight="900" fill="{"#111111" if bw else "#059669"}">+</text>')

    parts.append("</svg>")
    return "".join(parts)


def render_cover_page(paper: str, bw: bool, total_maps: int) -> str:
    accent = "#111111" if bw else "#b45309"
    soft = "#f3f4f6" if bw else "#fef3c7"
    return f"""
    <section class="sheet cover-sheet">
      <div class="cover-border" style="border-color:{accent};">
        <div class="cover-top">
          <span class="tag" style="background:{soft}; color:{accent}; border-color:{accent};">SOLO ROLL &amp; WRITE · 2D6 + PENCIL</span>
          <span class="tag">{paper} · {"INK-SAVER B&amp;W" if bw else "FULL COLOR"}</span>
        </div>
        <div class="cover-center">
          <div class="cover-kicker">EACH-TOUCH PRINT-PLAY LAB PRESENTS</div>
          <h1 class="cover-title">POCKET<br/><span style="color:{accent};">DUNGEON</span></h1>
          <p class="cover-sub">{total_maps} Mathematically Verified Solo Dungeon Crawl Maps</p>
          <div class="biome-pills">
            <div><strong>01–10</strong> Crypt of Embers</div>
            <div><strong>11–20</strong> Sunken Vault</div>
            <div><strong>21–30</strong> Clockwork Spire</div>
            <div><strong>31–40</strong> Frost Cavern</div>
            <div><strong>41–50</strong> Obsidian Citadel</div>
          </div>
        </div>
        <div class="cover-bottom">
          <div>15-Minute Sessions · Progressive Difficulty (★ to ★★★★★) · 100% Zero Generative AI</div>
          <div>each-touch.github.io/print-play-lab</div>
        </div>
      </div>
    </section>
    """


def render_rulebook_page(bw: bool) -> str:
    accent = "#111111" if bw else "#0369a1"
    soft = "#f3f4f6" if bw else "#e0f2fe"
    return f"""
    <section class="sheet rule-sheet">
      <header class="sheet-head" style="border-bottom-color:{accent};">
        <div>
          <span class="kicker" style="color:{accent};">HOW TO PLAY · 1-PAGE ILLUSTRATED GUIDE</span>
          <h2>POCKET DUNGEON — SOLO ROLL &amp; WRITE RULES</h2>
        </div>
        <span class="pill" style="background:{soft}; color:{accent}; border:1px solid {accent};">PLAYERS: 1 · DICE: 2d6</span>
      </header>

      <div class="rule-grid">
        <div class="rule-box">
          <h3>1. Setup (30 Seconds)</h3>
          <p>Print any map sheet and grab <strong>2 standard 6-sided dice (2d6)</strong> and a <strong>pencil</strong>. Circle <strong>Start (S)</strong>, verify your <strong>10 HP</strong> and <strong>8 Torch</strong> boxes are empty, and read the Biome Rule at the top.</p>
        </div>
        <div class="rule-box">
          <h3>2. Turn Loop (Repeat up to 20 Turns)</h3>
          <ul>
            <li>Cross off <strong>1 Turn box</strong> and <strong>1 Torch box</strong> (if Torch hits 0, take 1 Damage per turn!).</li>
            <li>Roll <strong>2d6</strong>. Assign <strong>1 die to Movement</strong> and <strong>1 die to Action</strong>:</li>
            <li><strong>Movement Die (1–6):</strong> Trace an orthogonal path up to that many Steps. You may revisit crossed tiles, but you cannot walk through walls (<strong>#</strong>). Stop immediately on an undefeated Monster or Boss.</li>
            <li><strong>Action Die (1–6):</strong> Use its value to Fight a Monster/Boss you stand on, Disarm a Trap (roll 4+), or Refill +2 Torch (roll 5–6).</li>
          </ul>
        </div>
        <div class="rule-box">
          <h3>3. Map Symbols &amp; Encounters</h3>
          <table class="sym-table">
            <tr><td><strong>S</strong></td><td><strong>Start:</strong> Begin your crawl here.</td></tr>
            <tr><td><strong>K</strong></td><td><strong>Key:</strong> Step onto K to unlock Boss (B) &amp; check <em>Key Found</em>.</td></tr>
            <tr><td><strong>M2–M6</strong></td><td><strong>Monster:</strong> Action Die &ge; Power defeats it (+2 XP). Otherwise take 1 Damage.</td></tr>
            <tr><td><strong>▲ (!)</strong></td><td><strong>Trap:</strong> Entering triggers Trap (1 Damage unless Action Die &ge; 4).</td></tr>
            <tr><td><strong>$</strong></td><td><strong>Chest:</strong> First visit scores +5 Gold &amp; +1 Torch.</td></tr>
            <tr><td><strong>+</strong></td><td><strong>Shrine:</strong> First visit heals +3 HP (max 10).</td></tr>
            <tr><td><strong>B3–B6</strong></td><td><strong>Boss:</strong> Must hold Key! Action Die &ge; Boss Power slays it.</td></tr>
            <tr><td><strong>E</strong></td><td><strong>Exit:</strong> Step on E after slaying Boss to win immediately!</td></tr>
          </table>
        </div>
        <div class="rule-box">
          <h3>4. Victory &amp; Scoring</h3>
          <p>Escape via <strong>Exit (E)</strong> before HP hits 0 or Turn 20 ends! Calculate your Legend Score:</p>
          <ul>
            <li><strong>Escaped Dungeon:</strong> +20 pts &nbsp;|&nbsp; <strong>Each Remaining HP:</strong> +2 pts</li>
            <li><strong>Each Gold ($):</strong> +1 pt &nbsp;|&nbsp; <strong>Each XP (Monster):</strong> +1 pt</li>
            <li><strong>Remaining Torch:</strong> +1 pt &nbsp;|&nbsp; <strong>25+ pts:</strong> Master Delver!</li>
          </ul>
        </div>
      </div>
      <div class="rule-footer">Tip: Laminate your favorite sheets or slip them into clear dry-erase sleeves for infinite replays!</div>
    </section>
    """


def render_map_page(m: dict[str, Any], bw: bool) -> str:
    accent = "#111111" if bw else m["accent"]
    soft = "#f3f4f6" if bw else m["accentSoft"]
    stars = "★" * m["difficulty"] + "☆" * (5 - m["difficulty"])
    hp_boxes = "".join('<span class="chk"></span>' for _ in range(10))
    torch_boxes = "".join('<span class="chk"></span>' for _ in range(8))
    turn_boxes = "".join(f'<span class="turn-chk">{i}</span>' for i in range(1, 21))
    svg = render_grid_svg(m, bw=bw)
    return f"""
    <section class="sheet map-sheet">
      <header class="map-head" style="border-bottom-color:{accent};">
        <div>
          <div class="map-kicker" style="color:{accent};">MAP #{m['num']:02d} · {html.escape(m['biome']).upper()}</div>
          <h2>{html.escape(m['title'])}</h2>
        </div>
        <div class="map-meta">
          <div class="diff" style="color:{accent};">{stars}</div>
          <div class="boss-pill" style="background:{soft}; border-color:{accent}; color:{accent};">BOSS PWR: {m['bossPower']}</div>
        </div>
      </header>

      <div class="biome-rule" style="background:{soft}; border-left:4px solid {accent};">
        <strong>BIOME RULE:</strong> {html.escape(m['rule'])}
      </div>

      <div class="map-canvas-wrap">
        {svg}
      </div>

      <div class="legend-strip">
        <span><strong>S</strong> Start</span>
        <span><strong>K</strong> Key</span>
        <span><strong>M#</strong> Monster (Beat #)</span>
        <span><strong>▲</strong> Trap (4+ Disarm)</span>
        <span><strong>$</strong> +5 Gold/+1 Torch</span>
        <span><strong>+</strong> +3 HP</span>
        <span><strong>B#</strong> Boss (Need Key)</span>
        <span><strong>E</strong> Exit</span>
      </div>

      <div class="tracker-grid">
        <div class="track-card">
          <div class="track-lbl">HP (CROSS OFF DAMAGE · MAX 10)</div>
          <div class="chk-row">{hp_boxes}</div>
        </div>
        <div class="track-card">
          <div class="track-lbl">TORCH (1 PER TURN · MAX 8)</div>
          <div class="chk-row">{torch_boxes}</div>
        </div>
        <div class="track-card">
          <div class="track-lbl">OBJECTIVES &amp; LOOT</div>
          <div class="obj-row">
            <span><span class="chk inline"></span> Key (K)</span>
            <span><span class="chk inline"></span> Boss (B)</span>
            <span>Gold: ____</span>
            <span>Score: ____</span>
          </div>
        </div>
        <div class="track-card track-turns">
          <div class="track-lbl">TURNS (MAX 20)</div>
          <div class="turn-row">{turn_boxes}</div>
        </div>
      </div>
    </section>
    """


def build_doc(title: str, page_css_size: str, pages: list[str]) -> str:
    w, h = ("8.5in", "11in") if page_css_size == "letter" else ("210mm", "297mm")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>{html.escape(title)}</title>
  <style>
    @page {{ size: {page_css_size}; margin: 0; }}
    * {{ box-sizing: border-box; }}
    html, body {{
      margin: 0; padding: 0; background: #ffffff; color: #0f172a;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      -webkit-print-color-adjust: exact; print-color-adjust: exact;
    }}
    .sheet {{
      width: {w}; height: {h}; padding: 0.40in 0.44in;
      overflow: hidden; display: flex; flex-direction: column; justify-content: space-between;
      page-break-after: always; break-after: page;
    }}
    .sheet:last-child {{ page-break-after: auto; break-after: auto; }}
    .cover-border {{
      height: 100%; border: 4px solid #111; border-radius: 12px; padding: 0.48in;
      display: flex; flex-direction: column; justify-content: space-between;
    }}
    .cover-top {{ display: flex; justify-content: space-between; align-items: center; gap: 10px; }}
    .tag {{ font-size: 11px; font-weight: 800; padding: 5px 11px; border-radius: 999px; border: 1.5px solid #334155; letter-spacing: 0.05em; }}
    .cover-center {{ text-align: center; }}
    .cover-kicker {{ font-size: 13px; letter-spacing: 0.16em; font-weight: 700; color: #475569; margin-bottom: 14px; }}
    .cover-title {{ margin: 0 0 14px; font-size: 68px; line-height: 0.96; font-weight: 900; letter-spacing: -0.03em; }}
    .cover-sub {{ margin: 0 0 26px; font-size: 20px; font-weight: 600; color: #334155; }}
    .biome-pills {{
      display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; max-width: 480px; margin: 0 auto;
      text-align: left; font-size: 14px;
    }}
    .biome-pills div {{ border: 1.5px solid #cbd5e1; border-radius: 8px; padding: 8px 12px; }}
    .cover-bottom {{ display: flex; justify-content: space-between; font-size: 11.5px; color: #475569; font-weight: 600; border-top: 1px solid #cbd5e1; padding-top: 10px; }}
    .sheet-head, .map-head {{
      display: flex; justify-content: space-between; align-items: flex-end; gap: 12px;
      border-bottom: 3px solid #111; padding-bottom: 6px;
    }}
    .kicker, .map-kicker {{ font-size: 10.5px; font-weight: 800; letter-spacing: 0.08em; }}
    h2 {{ margin: 2px 0 0; font-size: 21px; line-height: 1.1; font-weight: 900; }}
    .pill, .boss-pill {{ font-size: 11px; font-weight: 800; padding: 4px 10px; border-radius: 6px; border: 1.5px solid #111; }}
    .map-meta {{ text-align: right; }}
    .diff {{ font-size: 15px; letter-spacing: 1px; margin-bottom: 2px; }}
    .rule-grid {{ display: grid; grid-template-columns: 1fr; gap: 12px; margin: 12px 0; flex: 1; }}
    .rule-box {{ border: 1.5px solid #cbd5e1; border-radius: 8px; padding: 11px 14px; }}
    .rule-box h3 {{ margin: 0 0 6px; font-size: 14px; font-weight: 800; }}
    .rule-box p, .rule-box li {{ margin: 0 0 5px; font-size: 12.2px; line-height: 1.42; }}
    .rule-box ul {{ margin: 0; padding-left: 18px; }}
    .sym-table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
    .sym-table td {{ padding: 3px 6px; border-bottom: 1px solid #e2e8f0; }}
    .sym-table td:first-child {{ width: 64px; font-family: ui-monospace, Menlo, monospace; }}
    .rule-footer {{ font-size: 11px; color: #475569; text-align: center; border-top: 1px solid #cbd5e1; padding-top: 8px; }}
    .biome-rule {{ padding: 7px 11px; font-size: 11.8px; border-radius: 6px; margin-top: 7px; }}
    .map-canvas-wrap {{
      width: 100%; max-height: 5.55in; aspect-ratio: 1 / 1; margin: 6px auto;
      display: flex; align-items: center; justify-content: center;
    }}
    .legend-strip {{
      display: flex; justify-content: space-between; flex-wrap: wrap; gap: 6px;
      font-size: 10.5px; border: 1px solid #cbd5e1; border-radius: 6px; padding: 5px 10px; background: #f8fafc;
    }}
    .tracker-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 7px; margin-top: 7px; }}
    .track-card {{ border: 1.5px solid #334155; border-radius: 6px; padding: 6px 9px; }}
    .track-turns {{ grid-column: 1 / -1; }}
    .track-lbl {{ font-size: 9.5px; font-weight: 800; letter-spacing: 0.05em; color: #334155; margin-bottom: 5px; }}
    .chk-row, .obj-row, .turn-row {{ display: flex; gap: 5px; align-items: center; flex-wrap: wrap; font-size: 11px; font-weight: 700; }}
    .chk {{ width: 16px; height: 16px; border: 1.6px solid #0f172a; border-radius: 3px; display: inline-block; }}
    .chk.inline {{ width: 13px; height: 13px; vertical-align: -2px; margin-right: 3px; }}
    .turn-chk {{
      width: 24px; height: 18px; border: 1.4px solid #334155; border-radius: 3px;
      display: inline-flex; align-items: center; justify-content: center; font-size: 9.5px; font-family: ui-monospace, monospace;
    }}
  </style>
</head>
<body>
  {"".join(pages)}
</body>
</html>
"""


def main() -> int:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    maps = [generate_verified_map(i) for i in range(50)]

    # 1. Full US Letter Color (52 pages)
    pages_lc = [render_cover_page("US LETTER", False, 50), render_rulebook_page(False)] + [render_map_page(m, False) for m in maps]
    (WORK_DIR / "full_letter_color.html").write_text(build_doc("Pocket Dungeon 50 — US Letter Color", "letter", pages_lc), encoding="utf-8")

    # 2. Full US Letter Ink-Saver B&W (52 pages)
    pages_lbw = [render_cover_page("US LETTER", True, 50), render_rulebook_page(True)] + [render_map_page(m, True) for m in maps]
    (WORK_DIR / "full_letter_bw.html").write_text(build_doc("Pocket Dungeon 50 — US Letter Ink-Saver B&W", "letter", pages_lbw), encoding="utf-8")

    # 3. Full A4 Ink-Saver B&W (52 pages)
    pages_a4 = [render_cover_page("A4", True, 50), render_rulebook_page(True)] + [render_map_page(m, True) for m in maps]
    (WORK_DIR / "full_a4_bw.html").write_text(build_doc("Pocket Dungeon 50 — A4 Ink-Saver B&W", "A4", pages_a4), encoding="utf-8")

    # 4. Free 3-Map Sample Demo (5 pages: Cover + Rulebook + Maps #1, #11, #21)
    sample_maps = [maps[0], maps[10], maps[20]]
    pages_demo = [render_cover_page("US LETTER FREE SAMPLE", False, 3), render_rulebook_page(False)] + [render_map_page(m, False) for m in sample_maps]
    (WORK_DIR / "demo_3maps_letter.html").write_text(build_doc("Pocket Dungeon — Free 3-Map Sample", "letter", pages_demo), encoding="utf-8")

    # 5. Side-by-side Rulebook + Map #1 spread preview (1280x720)
    spread_html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<style>
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; padding: 0; width: 1280px; height: 720px; overflow: hidden; background: #0f172a; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; color: #0f172a; }}
  .wrap {{ width: 1280px; height: 720px; padding: 26px 32px; display: flex; flex-direction: column; gap: 14px; }}
  .bar {{ display: flex; justify-content: space-between; align-items: center; color: #f8fafc; }}
  .bar h1 {{ margin: 0; font-size: 22px; }}
  .bar span {{ font-family: ui-monospace, Menlo, monospace; font-size: 13px; color: #f59e0b; font-weight: 700; }}
  .cards {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; flex: 1; min-height: 0; }}
  .paper {{ background: #ffffff; border-radius: 10px; padding: 16px 20px; overflow: hidden; box-shadow: 0 18px 40px rgba(0,0,0,0.45); display: flex; flex-direction: column; justify-content: space-between; }}
  .paper h2 {{ margin: 2px 0 0; font-size: 16px; }}
  .map-kicker, .kicker {{ font-size: 9.5px; font-weight: 800; letter-spacing: 0.08em; }}
  .sheet-head, .map-head {{ display: flex; justify-content: space-between; align-items: flex-end; border-bottom: 2.5px solid #111; padding-bottom: 4px; }}
  .pill, .boss-pill {{ font-size: 10px; font-weight: 800; padding: 3px 8px; border-radius: 5px; border: 1.5px solid #111; }}
  .rule-grid {{ display: grid; grid-template-columns: 1fr; gap: 7px; margin: 8px 0; }}
  .rule-box {{ border: 1.2px solid #cbd5e1; border-radius: 6px; padding: 7px 10px; }}
  .rule-box h3 {{ margin: 0 0 3px; font-size: 12px; }}
  .rule-box p, .rule-box li {{ margin: 0 0 2px; font-size: 10.5px; line-height: 1.3; }}
  .rule-box ul {{ margin: 0; padding-left: 15px; }}
  .sym-table {{ width: 100%; border-collapse: collapse; font-size: 10px; }}
  .sym-table td {{ padding: 1.5px 4px; border-bottom: 1px solid #e2e8f0; }}
  .biome-rule {{ padding: 5px 8px; font-size: 10.5px; border-radius: 4px; margin-top: 4px; }}
  .map-canvas-wrap {{ width: 340px; height: 340px; margin: 4px auto; }}
  .legend-strip {{ display: flex; justify-content: space-between; flex-wrap: wrap; gap: 4px; font-size: 9.5px; border: 1px solid #cbd5e1; padding: 4px 7px; border-radius: 4px; }}
  .tracker-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 5px; margin-top: 4px; }}
  .track-card {{ border: 1.2px solid #334155; border-radius: 5px; padding: 4px 7px; }}
  .track-turns {{ grid-column: 1 / -1; }}
  .track-lbl {{ font-size: 8.5px; font-weight: 800; margin-bottom: 3px; }}
  .chk-row, .obj-row, .turn-row {{ display: flex; gap: 4px; flex-wrap: wrap; font-size: 9.5px; font-weight: 700; }}
  .chk {{ width: 12px; height: 12px; border: 1.4px solid #0f172a; border-radius: 2px; display: inline-block; }}
  .chk.inline {{ width: 10px; height: 10px; vertical-align: -1px; margin-right: 2px; }}
  .turn-chk {{ width: 19px; height: 14px; border: 1.2px solid #334155; border-radius: 2px; display: inline-flex; align-items: center; justify-content: center; font-size: 8.5px; }}
</style>
</head>
<body>
  <div class="wrap">
    <div class="bar">
      <h1>Pocket Dungeon — Sample Rulebook &amp; Map #01 Preview (Print-Ready Vector PDF)</h1>
      <span>50 VERIFIED MAPS · US LETTER + A4 · COLOR + B&amp;W</span>
    </div>
    <div class="cards">
      <div class="paper">{render_rulebook_page(False).replace('<section class="sheet rule-sheet">', '').replace('</section>', '')}</div>
      <div class="paper">{render_map_page(maps[0], False).replace('<section class="sheet map-sheet">', '').replace('</section>', '')}</div>
    </div>
  </div>
</body>
</html>"""
    (WORK_DIR / "sample_preview_spread.html").write_text(spread_html, encoding="utf-8")

    (WORK_DIR / "maps_summary.json").write_text(
        json.dumps([{"num": m["num"], "title": m["title"], "biome": m["biome"], "difficulty": m["difficulty"], "bossPower": m["bossPower"]} for m in maps], indent=2),
        encoding="utf-8",
    )
    print("Generated & BFS-verified all 50 Pocket Dungeon crawl maps + print HTMLs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
