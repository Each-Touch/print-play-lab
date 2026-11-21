#!/usr/bin/env python3
"""Fetch GitHub traffic metrics for Each-Touch/print-play-lab."""

from __future__ import annotations

import json
import subprocess

REPO = "Each-Touch/print-play-lab"


def _gh_api(endpoint: str) -> dict:
    res = subprocess.run(["gh", "api", endpoint], capture_output=True, text=True, timeout=20)
    if res.returncode != 0:
        return {"error": res.stderr.strip() or res.stdout.strip()}
    try:
        return json.loads(res.stdout or "{}")
    except json.JSONDecodeError:
        return {"raw": res.stdout.strip()}


def main() -> int:
    print(json.dumps({"repo": REPO, "views": _gh_api(f"repos/{REPO}/traffic/views"), "clones": _gh_api(f"repos/{REPO}/traffic/clones")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
