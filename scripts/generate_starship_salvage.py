#!/usr/bin/env python3
"""Generate 40 BFS-verified solvable solo sci-fi roll-and-write deck plans + print HTMLs."""

from __future__ import annotations

import html
import json
import random
from collections import deque
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
SLUG = "starship-salvage-40"
REL_DIR = ROOT / "releases" / SLUG
WORK_DIR = REL_DIR / "work_tmp"
ROWS = 10
COLS = 12

SHIP_CLASSES = [
    {
        "name": "Mining Frigate",
        "accent": "#0284c7",
        "accentSoft": "#e0f2fe",
        "rule": "Ore Blast: Whenever you roll doubles (e.g. 3+3), gain +1 Power OR clear 1 adjacent Hazard (!).",
        "prefixes": ["Aegis", "Cobalt", "Driller", "Ferrite", "Basalt", "Quarry", "Vein", "Pyrite", "Smelter", "Anvil"],
    },
    {
        "name": "Research Cruiser",
        "accent": "#059669",
        "accentSoft": "#d1fae5",
        "rule": "Bio-Lab Surge: First time entering an O2 Scrubber (O) also grants +1 Shield; Hazards deal +1 Hull dmg if Shields = 0.",
        "prefixes": ["Helix", "Nebula", "Kepler", "Pulse", "Spectra", "Darwin", "Aether", "Quanta", "Vector", "Horizon"],
    },
    {
        "name": "Dreadnought Hulk",
        "accent": "#dc2626",
        "accentSoft": "#fee2e2",
        "rule": "Reactor Leak: Every 4th Turn (4, 8, 12, 16), lose 1 Shield (or 1 Hull if Shields = 0) unless standing on a Relay (P).",
        "prefixes": ["Valkyrie", "Titan", "Bastion", "Ironclad", "Gorgon", "Nemesis", "Citadel", "Tempest", "Scythe", "Sovereign"],
    },
    {
        "name": "Colony Ark",
        "accent": "#7c3aed",
        "accentSoft": "#ede9fe",
        "rule": "Cryo-Lock: Stabilizing Reactor (R) requires Power >= 2 (spend 2 Power boxes OR roll Action Die >= Reactor Rating).",
        "prefixes": ["Genesis", "Exodus", "Odyssey", "Pioneer", "Vanguard", "Aurora", "Solstice", "Meridian", "Covenant", "Zenith"],
    },
]

DECK_NAMES = [
    "Cargo Deck", "Engineering Bay", "Command Spine", "Reactor Corridor", "Cryo Wing",
    "Sensor Array", "Hangar Deck", "Life Support", "Armory Ring", "Bridge Sector",
]


def bfs_distances(grid: list[list[str]], start: tuple[int, int], blocked: set[str]) -> dict[tuple[int, int], int]:
    q = deque([start])
    dist = {start: 0}
    while q:
        r, c = q.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                if (nr, nc) not in dist and grid[nr][nc] not in blocked:
                    dist[(nr, nc)] = dist[(r, c)] + 1
                    q.append((nr, nc))
    return dist


def generate_verified_deck(deck_idx: int) -> dict[str, Any]:
    class_idx = deck_idx // 10
    ship_cls = SHIP_CLASSES[class_idx]
    local_idx = deck_idx % 10
    difficulty = min(5, 1 + class_idx + (1 if local_idx >= 5 else 0))

    for attempt in range(80):
        rng = random.Random(91000 + deck_idx * 1009 + attempt * 37)
        grid = [["#" for _ in range(COLS)] for _ in range(ROWS)]

        # Carve a symmetrical/organic starship hull interior (bow on right, airlock stern-left)
        sr = rng.choice([4, 5])
        sc = 1
        grid[sr][sc] = "."

        # Carve 5-7 ship compartments (2x2 or 3x2) connected by corridors
        centers = [(sr, sc)]
        for _ in range(6 + (deck_idx % 3)):
            cr = rng.randint(1, ROWS - 3)
            cc = rng.randint(1, COLS - 4)
            rw = rng.randint(2, 3)
            rh = rng.randint(2, 3)
            for rr in range(cr, min(ROWS - 1, cr + rh)):
                for cc2 in range(cc, min(COLS - 1, cc + rw)):
                    grid[rr][cc2] = "."
            centers.append((cr, cc))

        # Ensure an escape bay near starboard bow
        bow_r = rng.choice([2, 3, 6, 7])
        bow_c = COLS - 2
        for rr in range(max(1, bow_r - 1), min(ROWS - 1, bow_r + 2)):
            for cc2 in range(COLS - 3, COLS - 1):
                grid[rr][cc2] = "."
        centers.append((bow_r, bow_c))

        # Connect compartments sequentially + cross-links for tactical choices
        for i in range(len(centers) - 1):
            r1, c1 = centers[i]
            r2, c2 = centers[i + 1]
            r, c = r1, c1
            if rng.random() < 0.5:
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

        for _ in range(2):
            a, b = rng.sample(centers, 2)
            r, c = a
            while c != b[1]:
                grid[r][c] = "."
                c += 1 if b[1] > c else -1
            while r != b[0]:
                grid[r][c] = "."
                r += 1 if b[0] > r else -1

        walkable = [(r, c) for r in range(ROWS) for c in range(COLS) if grid[r][c] == "."]
        if len(walkable) < 40:
            continue

        start = (sr, sc)
        d_all = bfs_distances(grid, start, {"#"})
        reachable = [pos for pos in walkable if pos in d_all]
        if len(reachable) < 38:
            continue

        # Escape Pod (E) at farthest reachable starboard tile
        reachable.sort(key=lambda p: (d_all[p], p[1]), reverse=True)
        escape_pos = reachable[0]
        if d_all[escape_pos] < 9:
            continue

        # Reactor Core (R) adjacent or 1-2 steps from Escape Pod (not equal to start)
        reactor_candidates = [
            p for p in reachable
            if p not in (start, escape_pos) and 1 <= abs(p[0] - escape_pos[0]) + abs(p[1] - escape_pos[1]) <= 2
        ]
        if not reactor_candidates:
            continue
        reactor_pos = reactor_candidates[0]

        grid[start[0]][start[1]] = "A"
        grid[escape_pos[0]][escape_pos[1]] = "E"
        grid[reactor_pos[0]][reactor_pos[1]] = "R"

        # Access Card (C) must be reachable from A without stepping on R or E
        d_before_reactor = bfs_distances(grid, start, {"#", "R", "E"})
        card_candidates = [p for p, dist in d_before_reactor.items() if dist >= 5 and grid[p[0]][p[1]] == "."]
        if not card_candidates:
            continue
        card_candidates.sort(key=lambda p: abs(p[0] - reactor_pos[0]) + abs(p[1] - reactor_pos[1]), reverse=True)
        card_pos = card_candidates[rng.randint(0, min(3, len(card_candidates) - 1))]
        grid[card_pos[0]][card_pos[1]] = "C"

        # Verify strict ordered solvability: A->C (no R/E), C->R (no E), R->E
        v1 = bfs_distances(grid, start, {"#", "R", "E"})
        if card_pos not in v1:
            continue
        v2 = bfs_distances(grid, card_pos, {"#", "E"})
        if reactor_pos not in v2:
            continue
        v3 = bfs_distances(grid, reactor_pos, {"#"})
        if escape_pos not in v3:
            continue
        total_opt_steps = v1[card_pos] + v2[reactor_pos] + v3[escape_pos]
        if not (11 <= total_opt_steps <= 32):
            continue

        # Populate Drones (X), Hazards (!), Salvage ($), Power Relays (P), O2 Scrubbers (O)
        free_tiles = [p for p in v1 if grid[p[0]][p[1]] == "."]
        rng.shuffle(free_tiles)
        if len(free_tiles) < 14:
            continue

        n_drones = min(5 + (difficulty // 2), len(free_tiles) // 3)
        n_hazards = min(3 + (difficulty // 2), 6)
        n_salvage = 3
        n_power = 2
        n_o2 = 2

        idx = 0
        for d_i in range(n_drones):
            p = free_tiles[idx]
            idx += 1
            pwr = min(6, max(2, 2 + (difficulty - 1) // 2 + (d_i % 3)))
            grid[p[0]][p[1]] = f"X{pwr}"
        for _ in range(n_hazards):
            p = free_tiles[idx]
            idx += 1
            grid[p[0]][p[1]] = "!"
        for _ in range(n_salvage):
            p = free_tiles[idx]
            idx += 1
            grid[p[0]][p[1]] = "$"
        for _ in range(n_power):
            p = free_tiles[idx]
            idx += 1
            grid[p[0]][p[1]] = "P"
        for _ in range(n_o2):
            p = free_tiles[idx]
            idx += 1
            grid[p[0]][p[1]] = "O"

        # Final programmatic assertion on every deck
        assert bfs_distances(grid, start, {"#", "R", "E"}).get(card_pos) is not None
        assert bfs_distances(grid, card_pos, {"#", "E"}).get(reactor_pos) is not None
        assert bfs_distances(grid, reactor_pos, {"#"}).get(escape_pos) is not None
        full_reach = bfs_distances(grid, start, {"#"})
        for rr in range(ROWS):
            for cc in range(COLS):
                if grid[rr][cc] != "#":
                    assert (rr, cc) in full_reach, f"Isolated deck tile at {(rr, cc)}"

        reactor_pwr = min(6, 3 + (difficulty + 1) // 2)
        ship_name = f"USS {ship_cls['prefixes'][local_idx]}"
        deck_title = f"{ship_name} — {DECK_NAMES[(deck_idx * 3 + local_idx) % len(DECK_NAMES)]}"
        return {
            "num": deck_idx + 1,
            "title": deck_title,
            "shipClass": ship_cls["name"],
            "accent": ship_cls["accent"],
            "accentSoft": ship_cls["accentSoft"],
            "rule": ship_cls["rule"],
            "difficulty": difficulty,
            "reactorPower": reactor_pwr,
            "optSteps": total_opt_steps,
            "grid": grid,
        }

    raise RuntimeError(f"Failed to generate verified deck #{deck_idx + 1}")


def render_deck_svg(m: dict[str, Any], bw: bool = False) -> str:
    cell = 44
    pad = 22
    w = pad * 2 + COLS * cell
    h = pad * 2 + ROWS * cell
    accent = "#111111" if bw else m["accent"]
    wall_fill = "#e5e7eb" if bw else "#1e293b"
    wall_hatch = "#cbd5e1" if bw else "#334155"
    stroke_col = "#111111" if bw else "#475569"

    parts = [f'<svg viewBox="0 0 {w} {h}" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">']
    parts.append(f'<rect x="0" y="0" width="{w}" height="{h}" fill="#ffffff"/>')

    cols_lbl = "ABCDEFGHIJKL"
    for c in range(COLS):
        cx = pad + c * cell + cell / 2
        parts.append(f'<text x="{cx}" y="15" text-anchor="middle" font-family="ui-monospace, Menlo, monospace" font-size="11" font-weight="700" fill="#64748b">{cols_lbl[c]}</text>')
    for r in range(ROWS):
        cy = pad + r * cell + cell / 2 + 4
        parts.append(f'<text x="11" y="{cy}" text-anchor="middle" font-family="ui-monospace, Menlo, monospace" font-size="11" font-weight="700" fill="#64748b">{r + 1}</text>')

    grid = m["grid"]
    for r in range(ROWS):
        for c in range(COLS):
            x = pad + c * cell
            y = pad + r * cell
            val = grid[r][c]
            if val == "#":
                parts.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" fill="{wall_fill}" stroke="{stroke_col}" stroke-width="1"/>')
                parts.append(f'<line x1="{x+4}" y1="{y+cell-4}" x2="{x+cell-4}" y2="{y+4}" stroke="{wall_hatch}" stroke-width="1.2"/>')
            else:
                fill = "#ffffff"
                if not bw:
                    if val == "A":
                        fill = "#dcfce7"
                    elif val == "C":
                        fill = "#fef9c3"
                    elif val == "R":
                        fill = "#fee2e2"
                    elif val == "E":
                        fill = "#dbeafe"
                parts.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" fill="{fill}" stroke="{stroke_col}" stroke-width="1.2"/>')
                cx = x + cell / 2
                cy = y + cell / 2 + 6
                if val == "A":
                    parts.append(f'<circle cx="{cx}" cy="{y+cell/2}" r="14" fill="none" stroke="{accent}" stroke-width="2.2"/>')
                    parts.append(f'<text x="{cx}" y="{cy}" text-anchor="middle" font-family="sans-serif" font-size="16" font-weight="900" fill="{accent}">A</text>')
                elif val == "C":
                    parts.append(f'<text x="{cx}" y="{cy-1}" text-anchor="middle" font-family="sans-serif" font-size="17" font-weight="900" fill="{"#111111" if bw else "#b45309"}">C</text>')
                    parts.append(f'<text x="{cx}" y="{y+cell-4}" text-anchor="middle" font-family="sans-serif" font-size="7.5" font-weight="800" fill="#475569">CARD</text>')
                elif val == "R":
                    parts.append(f'<rect x="{x+5}" y="{y+5}" width="{cell-10}" height="{cell-10}" rx="4" fill="{"#111111" if bw else "#991b1b"}"/>')
                    parts.append(f'<text x="{cx}" y="{cy-2}" text-anchor="middle" font-family="sans-serif" font-size="14" font-weight="900" fill="#ffffff">R{m["reactorPower"]}</text>')
                elif val == "E":
                    parts.append(f'<polygon points="{cx},{y+6} {x+cell-6},{y+cell/2} {cx},{y+cell-6} {x+6},{y+cell/2}" fill="none" stroke="{"#111111" if bw else "#1d4ed8"}" stroke-width="2.2"/>')
                    parts.append(f'<text x="{cx}" y="{cy-1}" text-anchor="middle" font-family="sans-serif" font-size="14" font-weight="900" fill="{"#111111" if bw else "#1d4ed8"}">E</text>')
                elif val.startswith("X"):
                    pwr = val[1:]
                    parts.append(f'<circle cx="{cx}" cy="{y+cell/2}" r="14" fill="{"#f3f4f6" if bw else "#f1f5f9"}" stroke="#111827" stroke-width="1.6"/>')
                    parts.append(f'<text x="{cx}" y="{cy-1}" text-anchor="middle" font-family="ui-monospace, monospace" font-size="13.5" font-weight="900" fill="#111827">X{pwr}</text>')
                elif val == "!":
                    parts.append(f'<polygon points="{cx},{y+9} {x+cell-9},{y+cell-9} {x+9},{y+cell-9}" fill="none" stroke="#111827" stroke-width="2"/>')
                    parts.append(f'<text x="{cx}" y="{y+cell-12}" text-anchor="middle" font-family="sans-serif" font-size="11" font-weight="900" fill="#111827">!</text>')
                elif val == "$":
                    parts.append(f'<rect x="{x+10}" y="{y+11}" width="{cell-20}" height="{cell-22}" rx="3" fill="{"#ffffff" if bw else "#fef08a"}" stroke="#111827" stroke-width="1.8"/>')
                    parts.append(f'<text x="{cx}" y="{cy-1}" text-anchor="middle" font-family="sans-serif" font-size="15" font-weight="900" fill="#111827">$</text>')
                elif val == "P":
                    parts.append(f'<rect x="{x+9}" y="{y+9}" width="{cell-18}" height="{cell-18}" rx="99" fill="{"#ffffff" if bw else "#e0f2fe"}" stroke="{"#111111" if bw else "#0284c7"}" stroke-width="1.8"/>')
                    parts.append(f'<text x="{cx}" y="{cy-1}" text-anchor="middle" font-family="sans-serif" font-size="14" font-weight="900" fill="{"#111111" if bw else "#0369a1"}">P</text>')
                elif val == "O":
                    parts.append(f'<rect x="{x+9}" y="{y+9}" width="{cell-18}" height="{cell-18}" rx="4" fill="{"#ffffff" if bw else "#dcfce7"}" stroke="{"#111111" if bw else "#059669"}" stroke-width="1.8"/>')
                    parts.append(f'<text x="{cx}" y="{cy-1}" text-anchor="middle" font-family="sans-serif" font-size="14" font-weight="900" fill="{"#111111" if bw else "#047857"}">O₂</text>')

    parts.append("</svg>")
    return "".join(parts)


def render_cover_page(paper: str, bw: bool, total_decks: int) -> str:
    accent = "#111111" if bw else "#0284c7"
    soft = "#f3f4f6" if bw else "#e0f2fe"
    return f"""
    <section class="sheet cover-sheet">
      <div class="cover-border" style="border-color:{accent};">
        <div class="cover-top">
          <span class="tag" style="background:{soft}; color:{accent}; border-color:{accent};">SOLO ROLL &amp; WRITE · 2D6 + PENCIL</span>
          <span class="tag">{paper} · {"INK-SAVER B&amp;W" if bw else "FULL COLOR"}</span>
        </div>
        <div class="cover-center">
          <div class="cover-kicker">EACH-TOUCH PRINT-PLAY LAB PRESENTS</div>
          <h1 class="cover-title">STARSHIP<br/><span style="color:{accent};">SALVAGE</span></h1>
          <p class="cover-sub">{total_decks} Mathematically Verified Sci-Fi Derelict Deck Plans</p>
          <div class="class-pills">
            <div><strong>01–10</strong> Mining Frigate</div>
            <div><strong>11–20</strong> Research Cruiser</div>
            <div><strong>21–30</strong> Dreadnought Hulk</div>
            <div><strong>31–40</strong> Colony Ark</div>
          </div>
        </div>
        <div class="cover-bottom">
          <div>15-Minute Sessions · O2 / Power / Shield Management · 100% Zero Generative AI</div>
          <div>each-touch.github.io/print-play-lab</div>
        </div>
      </div>
    </section>
    """


def render_rulebook_page(bw: bool) -> str:
    accent = "#111111" if bw else "#0284c7"
    soft = "#f3f4f6" if bw else "#e0f2fe"
    return f"""
    <section class="sheet rule-sheet">
      <header class="sheet-head" style="border-bottom-color:{accent};">
        <div>
          <span class="kicker" style="color:{accent};">HOW TO PLAY · 1-PAGE ILLUSTRATED GUIDE</span>
          <h2>STARSHIP SALVAGE — SOLO ROLL &amp; WRITE RULES</h2>
        </div>
        <span class="pill" style="background:{soft}; color:{accent}; border:1px solid {accent};">PLAYERS: 1 · DICE: 2d6</span>
      </header>

      <div class="rule-grid">
        <div class="rule-box">
          <h3>1. Setup (30 Seconds)</h3>
          <p>Print any deck sheet and grab <strong>2 standard 6-sided dice (2d6)</strong> and a <strong>pencil</strong>. Circle <strong>Airlock (A)</strong>, check that <strong>8 Hull</strong>, <strong>8 O2</strong>, <strong>6 Shield</strong>, and <strong>6 Power</strong> boxes start empty, and read the Ship Class Rule at the top.</p>
        </div>
        <div class="rule-box">
          <h3>2. Turn Loop (Repeat up to 18 Turns)</h3>
          <ul>
            <li>Cross off <strong>1 Turn box</strong>. On every <strong>EVEN Turn (2, 4, 6...)</strong> cross off <strong>1 O2 box</strong> (if O2 is full/0 left, take 1 Hull dmg).</li>
            <li>Roll <strong>2d6</strong>. Assign <strong>1 die to Thrusters (Movement)</strong> and <strong>1 die to Systems (Action)</strong>:</li>
            <li><strong>Thrusters Die (1–6):</strong> Trace an orthogonal path up to that many Steps. Cannot cross bulkheads (<strong>#</strong>). Must stop on an active Drone (<strong>X</strong>).</li>
            <li><strong>Systems Die (1–6):</strong> Disable a Drone you stand on, seal a Hazard (4+), Stabilize Reactor (<strong>R</strong>), or vent <strong>+2 O2</strong> (roll 5–6) / charge <strong>+1 Shield</strong> (roll 4+).</li>
          </ul>
        </div>
        <div class="rule-box">
          <h3>3. Deck Symbols &amp; Encounters</h3>
          <table class="sym-table">
            <tr><td><strong>A</strong></td><td><strong>Airlock Start:</strong> Begin your EVA salvage run here.</td></tr>
            <tr><td><strong>C</strong></td><td><strong>Access Card:</strong> Step onto C to unlock Reactor Core (R) &amp; Escape Pod (E).</td></tr>
            <tr><td><strong>X2–X6</strong></td><td><strong>Security Drone:</strong> Systems Die &ge; Power disables it (+2 Salvage Pts). Else -1 Shield (or Hull).</td></tr>
            <tr><td><strong>▲ (!)</strong></td><td><strong>Hull Breach / Hazard:</strong> Entering triggers hazard (-1 Hull unless Systems Die &ge; 4).</td></tr>
            <tr><td><strong>$</strong></td><td><strong>Salvage Crate:</strong> First visit scores +5 Salvage Cr. &amp; +1 Shield.</td></tr>
            <tr><td><strong>P / O₂</strong></td><td><strong>Relay / Scrubber:</strong> First visit restores +2 Power (P) or +2 O2 (O₂).</td></tr>
            <tr><td><strong>R3–R6</strong></td><td><strong>Reactor Core:</strong> Requires Access Card! Systems Die &ge; Rating stabilizes it.</td></tr>
            <tr><td><strong>E</strong></td><td><strong>Escape Pod:</strong> Step on E after stabilizing Reactor (R) to win immediately!</td></tr>
          </table>
        </div>
        <div class="rule-box">
          <h3>4. Victory &amp; Salvage Score</h3>
          <p>Launch via <strong>Escape Pod (E)</strong> before Hull hits 0 or Turn 18 ends! Tally your Mission Score:</p>
          <ul>
            <li><strong>Successful Launch:</strong> +20 pts &nbsp;|&nbsp; <strong>Remaining Hull + O2:</strong> +1 pt each</li>
            <li><strong>Salvage Crates ($):</strong> +5 pts each &nbsp;|&nbsp; <strong>Disabled Drones (X):</strong> +2 pts each</li>
            <li><strong>Remaining Power/Shield:</strong> +1 pt each &nbsp;|&nbsp; <strong>32+ pts:</strong> Ace Salvager!</li>
          </ul>
        </div>
      </div>
      <div class="rule-footer">Tip: Slip printed decks into dry-erase sheet protectors for endless zero-waste solo runs!</div>
    </section>
    """


def render_deck_page(m: dict[str, Any], bw: bool) -> str:
    accent = "#111111" if bw else m["accent"]
    soft = "#f3f4f6" if bw else m["accentSoft"]
    stars = "★" * m["difficulty"] + "☆" * (5 - m["difficulty"])
    hull_boxes = "".join('<span class="chk"></span>' for _ in range(8))
    o2_boxes = "".join('<span class="chk"></span>' for _ in range(8))
    sh_boxes = "".join('<span class="chk"></span>' for _ in range(6))
    pw_boxes = "".join('<span class="chk"></span>' for _ in range(6))
    turn_boxes = "".join(f'<span class="turn-chk">{i}</span>' for i in range(1, 19))
    svg = render_deck_svg(m, bw=bw)
    return f"""
    <section class="sheet map-sheet">
      <header class="map-head" style="border-bottom-color:{accent};">
        <div>
          <div class="map-kicker" style="color:{accent};">DECK #{m['num']:02d} · {html.escape(m['shipClass']).upper()}</div>
          <h2>{html.escape(m['title'])}</h2>
        </div>
        <div class="map-meta">
          <div class="diff" style="color:{accent};">{stars}</div>
          <div class="boss-pill" style="background:{soft}; border-color:{accent}; color:{accent};">REACTOR: {m['reactorPower']}</div>
        </div>
      </header>

      <div class="biome-rule" style="background:{soft}; border-left:4px solid {accent};">
        <strong>CLASS RULE:</strong> {html.escape(m['rule'])}
      </div>

      <div class="map-canvas-wrap">
        {svg}
      </div>

      <div class="legend-strip">
        <span><strong>A</strong> Airlock</span>
        <span><strong>C</strong> Card</span>
        <span><strong>X#</strong> Drone</span>
        <span><strong>▲</strong> Hazard (4+)</span>
        <span><strong>$</strong> +5 Cr/+1 Sh</span>
        <span><strong>P</strong> +2 Pwr</span>
        <span><strong>O₂</strong> +2 O2</span>
        <span><strong>R#</strong> Reactor</span>
        <span><strong>E</strong> Escape</span>
      </div>

      <div class="tracker-grid">
        <div class="track-card">
          <div class="track-lbl">HULL INTEGRITY (MAX 8)</div>
          <div class="chk-row">{hull_boxes}</div>
        </div>
        <div class="track-card">
          <div class="track-lbl">OXYGEN (1 ON EVEN TURNS · MAX 8)</div>
          <div class="chk-row">{o2_boxes}</div>
        </div>
        <div class="track-card">
          <div class="track-lbl">SHIELDS (6) &amp; POWER (6)</div>
          <div class="chk-row" style="gap:4px;">
            <span style="font-size:9.5px;">SH:</span>{sh_boxes}
            <span style="font-size:9.5px; margin-left:6px;">PW:</span>{pw_boxes}
          </div>
        </div>
        <div class="track-card">
          <div class="track-lbl">MISSION OBJECTIVES</div>
          <div class="obj-row">
            <span><span class="chk inline"></span> Card (C)</span>
            <span><span class="chk inline"></span> Reactor (R)</span>
            <span>Score: ____</span>
          </div>
        </div>
        <div class="track-card track-turns">
          <div class="track-lbl">TURNS (MAX 18 · EVEN TURNS COST -1 O2)</div>
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
      width: {w}; height: {h}; padding: 0.38in 0.42in;
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
    .cover-title {{ margin: 0 0 14px; font-size: 66px; line-height: 0.96; font-weight: 900; letter-spacing: -0.03em; }}
    .cover-sub {{ margin: 0 0 26px; font-size: 20px; font-weight: 600; color: #334155; }}
    .class-pills {{
      display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; max-width: 480px; margin: 0 auto;
      text-align: left; font-size: 14px;
    }}
    .class-pills div {{ border: 1.5px solid #cbd5e1; border-radius: 8px; padding: 8px 12px; }}
    .cover-bottom {{ display: flex; justify-content: space-between; font-size: 11.5px; color: #475569; font-weight: 600; border-top: 1px solid #cbd5e1; padding-top: 10px; }}
    .sheet-head, .map-head {{
      display: flex; justify-content: space-between; align-items: flex-end; gap: 12px;
      border-bottom: 3px solid #111; padding-bottom: 6px;
    }}
    .kicker, .map-kicker {{ font-size: 10.5px; font-weight: 800; letter-spacing: 0.08em; }}
    h2 {{ margin: 2px 0 0; font-size: 20px; line-height: 1.1; font-weight: 900; }}
    .pill, .boss-pill {{ font-size: 11px; font-weight: 800; padding: 4px 10px; border-radius: 6px; border: 1.5px solid #111; white-space: nowrap; }}
    .map-meta {{ text-align: right; }}
    .diff {{ font-size: 15px; letter-spacing: 1px; margin-bottom: 2px; }}
    .rule-grid {{ display: grid; grid-template-columns: 1fr; gap: 11px; margin: 10px 0; flex: 1; }}
    .rule-box {{ border: 1.5px solid #cbd5e1; border-radius: 8px; padding: 10px 13px; }}
    .rule-box h3 {{ margin: 0 0 6px; font-size: 14px; font-weight: 800; }}
    .rule-box p, .rule-box li {{ margin: 0 0 5px; font-size: 12px; line-height: 1.4; }}
    .rule-box ul {{ margin: 0; padding-left: 18px; }}
    .sym-table {{ width: 100%; border-collapse: collapse; font-size: 11.8px; }}
    .sym-table td {{ padding: 3px 6px; border-bottom: 1px solid #e2e8f0; }}
    .sym-table td:first-child {{ width: 72px; font-family: ui-monospace, Menlo, monospace; }}
    .rule-footer {{ font-size: 11px; color: #475569; text-align: center; border-top: 1px solid #cbd5e1; padding-top: 8px; }}
    .biome-rule {{ padding: 6px 10px; font-size: 11.5px; border-radius: 6px; margin-top: 6px; }}
    .map-canvas-wrap {{
      width: 100%; max-height: 4.95in; aspect-ratio: 12 / 10; margin: 6px auto;
      display: flex; align-items: center; justify-content: center;
    }}
    .legend-strip {{
      display: flex; justify-content: space-between; flex-wrap: wrap; gap: 6px;
      font-size: 10px; border: 1px solid #cbd5e1; border-radius: 6px; padding: 5px 9px; background: #f8fafc;
    }}
    .tracker-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-top: 6px; }}
    .track-card {{ border: 1.5px solid #334155; border-radius: 6px; padding: 5px 8px; }}
    .track-turns {{ grid-column: 1 / -1; }}
    .track-lbl {{ font-size: 9px; font-weight: 800; letter-spacing: 0.05em; color: #334155; margin-bottom: 4px; }}
    .chk-row, .obj-row, .turn-row {{ display: flex; gap: 4px; align-items: center; flex-wrap: wrap; font-size: 10.5px; font-weight: 700; }}
    .chk {{ width: 15px; height: 15px; border: 1.5px solid #0f172a; border-radius: 3px; display: inline-block; }}
    .chk.inline {{ width: 12px; height: 12px; vertical-align: -2px; margin-right: 3px; }}
    .turn-chk {{
      width: 24px; height: 17px; border: 1.4px solid #334155; border-radius: 3px;
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
    decks = [generate_verified_deck(i) for i in range(40)]

    # 1. Full US Letter Color (42 pages)
    pages_lc = [render_cover_page("US LETTER", False, 40), render_rulebook_page(False)] + [render_deck_page(m, False) for m in decks]
    (WORK_DIR / "full_letter_color.html").write_text(build_doc("Starship Salvage 40 — US Letter Color", "letter", pages_lc), encoding="utf-8")

    # 2. Full US Letter Ink-Saver B&W (42 pages)
    pages_lbw = [render_cover_page("US LETTER", True, 40), render_rulebook_page(True)] + [render_deck_page(m, True) for m in decks]
    (WORK_DIR / "full_letter_bw.html").write_text(build_doc("Starship Salvage 40 — US Letter Ink-Saver B&W", "letter", pages_lbw), encoding="utf-8")

    # 3. Full A4 Ink-Saver B&W (42 pages)
    pages_a4 = [render_cover_page("A4", True, 40), render_rulebook_page(True)] + [render_deck_page(m, True) for m in decks]
    (WORK_DIR / "full_a4_bw.html").write_text(build_doc("Starship Salvage 40 — A4 Ink-Saver B&W", "A4", pages_a4), encoding="utf-8")

    # 4. Free 3-Deck Sample Demo (5 pages: Cover + Rulebook + Decks #1, #11, #21)
    sample_decks = [decks[0], decks[10], decks[20]]
    pages_demo = [render_cover_page("US LETTER FREE SAMPLE", False, 3), render_rulebook_page(False)] + [render_deck_page(m, False) for m in sample_decks]
    (WORK_DIR / "demo_3maps_letter.html").write_text(build_doc("Starship Salvage — Free 3-Deck Sample", "letter", pages_demo), encoding="utf-8")

    # 5. Side-by-side Rulebook + Deck #01 spread preview (1280x720)
    spread_html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<style>
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; padding: 0; width: 1280px; height: 720px; overflow: hidden; background: #0f172a; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; color: #0f172a; }}
  .wrap {{ width: 1280px; height: 720px; padding: 24px 30px; display: flex; flex-direction: column; gap: 12px; }}
  .bar {{ display: flex; justify-content: space-between; align-items: center; color: #f8fafc; }}
  .bar h1 {{ margin: 0; font-size: 21px; }}
  .bar span {{ font-family: ui-monospace, Menlo, monospace; font-size: 13px; color: #38bdf8; font-weight: 700; }}
  .cards {{ display: grid; grid-template-columns: 1fr 1fr; gap: 22px; flex: 1; min-height: 0; }}
  .paper {{ background: #ffffff; border-radius: 10px; padding: 15px 18px; overflow: hidden; box-shadow: 0 18px 40px rgba(0,0,0,0.45); display: flex; flex-direction: column; justify-content: space-between; }}
  .paper h2 {{ margin: 2px 0 0; font-size: 15.5px; }}
  .map-kicker, .kicker {{ font-size: 9.5px; font-weight: 800; letter-spacing: 0.08em; }}
  .sheet-head, .map-head {{ display: flex; justify-content: space-between; align-items: flex-end; border-bottom: 2.5px solid #111; padding-bottom: 4px; }}
  .pill, .boss-pill {{ font-size: 9.5px; font-weight: 800; padding: 3px 7px; border-radius: 5px; border: 1.5px solid #111; white-space: nowrap; }}
  .diff {{ font-size: 12px; margin-bottom: 2px; }}
  .rule-grid {{ display: grid; grid-template-columns: 1fr; gap: 6px; margin: 7px 0; }}
  .rule-box {{ border: 1.2px solid #cbd5e1; border-radius: 6px; padding: 6px 9px; }}
  .rule-box h3 {{ margin: 0 0 3px; font-size: 11.5px; }}
  .rule-box p, .rule-box li {{ margin: 0 0 2px; font-size: 10.2px; line-height: 1.3; }}
  .rule-box ul {{ margin: 0; padding-left: 15px; }}
  .sym-table {{ width: 100%; border-collapse: collapse; font-size: 9.8px; }}
  .sym-table td {{ padding: 1.5px 4px; border-bottom: 1px solid #e2e8f0; }}
  .rule-footer {{ font-size: 9.5px; color: #475569; text-align: center; border-top: 1px solid #cbd5e1; padding-top: 5px; }}
  .biome-rule {{ padding: 4px 8px; font-size: 10px; border-radius: 4px; margin-top: 4px; }}
  .map-canvas-wrap {{ width: 372px; height: 310px; margin: 4px auto; }}
  .legend-strip {{ display: flex; justify-content: space-between; flex-wrap: wrap; gap: 4px; font-size: 9px; border: 1px solid #cbd5e1; padding: 3.5px 7px; border-radius: 4px; }}
  .tracker-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 4px; margin-top: 4px; }}
  .track-card {{ border: 1.2px solid #334155; border-radius: 5px; padding: 3.5px 6px; }}
  .track-turns {{ grid-column: 1 / -1; }}
  .track-lbl {{ font-size: 8px; font-weight: 800; margin-bottom: 2px; }}
  .chk-row, .obj-row, .turn-row {{ display: flex; gap: 3px; flex-wrap: wrap; font-size: 9px; font-weight: 700; align-items: center; }}
  .chk {{ width: 11px; height: 11px; border: 1.3px solid #0f172a; border-radius: 2px; display: inline-block; }}
  .chk.inline {{ width: 9px; height: 9px; vertical-align: -1px; margin-right: 2px; }}
  .turn-chk {{ width: 19px; height: 13px; border: 1.1px solid #334155; border-radius: 2px; display: inline-flex; align-items: center; justify-content: center; font-size: 8px; }}
</style>
</head>
<body>
  <div class="wrap">
    <div class="bar">
      <h1>Starship Salvage — Sample Rulebook &amp; Deck #01 Preview (Print-Ready Vector PDF)</h1>
      <span>40 VERIFIED DECKS · US LETTER + A4 · COLOR + B&amp;W</span>
    </div>
    <div class="cards">
      <div class="paper">{render_rulebook_page(False).replace('<section class="sheet rule-sheet">', '').replace('</section>', '')}</div>
      <div class="paper">{render_deck_page(decks[0], False).replace('<section class="sheet map-sheet">', '').replace('</section>', '')}</div>
    </div>
  </div>
</body>
</html>"""
    (WORK_DIR / "sample_preview_spread.html").write_text(spread_html, encoding="utf-8")

    (WORK_DIR / "decks_summary.json").write_text(
        json.dumps([
            {"num": m["num"], "title": m["title"], "shipClass": m["shipClass"], "difficulty": m["difficulty"], "reactorPower": m["reactorPower"], "optSteps": m["optSteps"]}
            for m in decks
        ], indent=2),
        encoding="utf-8",
    )
    print("Generated & BFS-verified all 40 Starship Salvage deck plans + print HTMLs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
