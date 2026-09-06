"""Regression test for `compute_hover_zones` — a layer whose span begins
BEFORE the timeline's `tl_year_from` must not emit zones with zero or
negative visible width.

Function under test:
    scripts/lib/timeline.py :: compute_hover_zones

The bug (caught 2026-09-06 on the Holstein Rhinskgyldenfod bar): the
circulation layers run from 1495 while the Holstein track opens at 1559.
The breakpoint zones covering 1495-1558 lie entirely left of the track,
so `raw_left` and `raw_right` are both negative; `cl` clamped to 0 but
`cr` stayed negative, giving a negative `zone_w`. Those zones then fed
`attach_visual_pieces`, whose `_merge_adjacent_pieces` summed the
negative width into the layer's solid piece — shrinking (or inverting)
the visible circulation body so the faded circulation-only tail read
STRONGER than the mint+circulation body before it. Off-track zones must
be dropped, not carried at negative width.

Run via:
    .venv/bin/python -m unittest tests.test_compute_hover_zones -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from lib.timeline import compute_hover_zones  # noqa: E402


def _layer(**kw) -> dict:
    return {
        "kind": kw.get("kind", "circulation"),
        "scope": kw.get("scope", "holstein"),
        "first": kw["first"],
        "last": kw["last"],
        # left_pct / width_pct are read for the cumulative-band centre only;
        # give already-clamped values as compute_bar_layers would.
        "left_pct": kw.get("left_pct", 0.0),
        "width_pct": kw.get("width_pct", 40.0),
    }


class TestComputeHoverZonesPreTrack(unittest.TestCase):
    def test_no_negative_or_zero_width_zones(self):
        # A circulation layer running 1495-1700 on a track that opens at
        # 1559: the pre-1559 breakpoints (1495, 1514, 1523) must not spawn
        # off-track zones with width <= 0.
        bars = {
            "b": [
                _layer(kind="status", first=1495, last=1602),
                _layer(kind="mint", first=1523, last=1664),
                _layer(kind="circulation", first=1495, last=1700),
            ]
        }
        zones = compute_hover_zones(bars, 1559, 1914)["b"]
        self.assertTrue(zones, "expected at least one on-track zone")
        for z in zones:
            self.assertGreater(
                z["width_pct"], 0.0,
                f"zone {z['first']}-{z['last']} has non-positive width "
                f"{z['width_pct']} — off-track sliver leaked through")
            self.assertGreaterEqual(z["left_pct"], 0.0)
            self.assertLessEqual(z["left_pct"] + z["width_pct"], 100.0 + 0.01)

    def test_first_zone_starts_at_track_open(self):
        # The earliest surviving zone must begin at the track's left edge
        # (left_pct == 0), i.e. year 1559 — never at a clamped-negative
        # remnant of the 1495 start.
        bars = {"b": [_layer(kind="circulation", first=1495, last=1700)]}
        zones = compute_hover_zones(bars, 1559, 1914)["b"]
        self.assertEqual(round(zones[0]["left_pct"], 2), 0.0)

    def test_fully_on_track_layer_unaffected(self):
        # A layer entirely inside the track keeps a single full-width zone.
        bars = {"b": [_layer(kind="mint", first=1600, last=1700,
                             left_pct=11.55, width_pct=28.45)]}
        zones = compute_hover_zones(bars, 1559, 1914)["b"]
        self.assertEqual(len(zones), 1)
        self.assertGreater(zones[0]["width_pct"], 0.0)


if __name__ == "__main__":
    unittest.main()
