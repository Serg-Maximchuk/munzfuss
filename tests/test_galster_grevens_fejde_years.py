"""Undated Grevens-Fejde coins take the Feud window, not the ruler's reign.

The Galster `c2g` volume holds two groups that share a ruler name and nothing
else. Christian II's own coins are of his reign, 1513-1523. The Grevens-Fejde
coins carry his name because his partisans struck them for his cause — while he
sat imprisoned at Sønderborg — during the Count's Feud of 1534-1536. Anchoring
an undated Feud coin to his regnal window dates it a decade before it existed.

Only the undated pages were affected: every Feud page that prints a year already
carried it (Galster 82 → 1534-1535, 85/86/87/91 → 1535, 84 → 1536). The three
that print «u.år» — Galster 88, 89 and 90 — fell through to the reign fallback,
and 89/90 are the first two Ungersk Gylden in the Danish record, which put the
denomination's Danish debut in the wrong decade.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from maintenance.build_galster_denmark_seed import (  # noqa: E402
    _GREVENS_FEJDE_WINDOW, _RULER_REIGN, build_entry,
)


def _page(**kw):
    """A minimal parsed-page dict; callers override what the test is about."""
    base = {
        "id": "c2g89",
        "ruler_volume": "c2g",
        "ruler": "Christian 2.",
        "nominal": "1 Ungersk gylden",
        "year_label": "u.år",
        "page_shape": "grevenfejde",
        "catalog_refs": {"Galster": ["89"], "Schou": ["2"], "Sieg": ["2"]},
        "mint": "Malmø eller København",
    }
    base.update(kw)
    return base


class TestTheFeudWindow(unittest.TestCase):
    def test_the_window_is_the_feud_not_a_reign(self):
        self.assertEqual(_GREVENS_FEJDE_WINDOW, (1534, 1536))
        self.assertNotEqual(_GREVENS_FEJDE_WINDOW, _RULER_REIGN["c2g"])

    def test_undated_feud_page_gets_the_feud_window(self):
        e = build_entry(_page())
        self.assertIsNotNone(e)
        self.assertEqual((e["year_first"], e["year_last"]), (1534, 1536))

    def test_it_stays_unverified(self):
        # The coin is undated; the window is an attribution, so the renderer
        # must still emit «(?)».
        e = build_entry(_page())
        self.assertIs(e.get("year_verified"), False)

    def test_a_dated_feud_page_keeps_its_own_year(self):
        e = build_entry(_page(id="c2g85", year_label="1535",
                              nominal="4 Skilling",
                              catalog_refs={"Galster": ["85"]}))
        self.assertEqual((e["year_first"], e["year_last"]), (1535, 1535))
        self.assertIs(e.get("year_verified"), True)

    def test_an_undated_NON_feud_page_still_uses_the_reign(self):
        # The fix must not widen: an ordinary undated Christian II page is
        # genuinely of his reign and keeps the regnal fallback.
        e = build_entry(_page(id="c2g40", page_shape="standard",
                              nominal="1 Hvid",
                              catalog_refs={"Galster": ["40"]}))
        self.assertEqual((e["year_first"], e["year_last"]), _RULER_REIGN["c2g"])

    def test_the_three_undated_feud_coins_all_move(self):
        for gid, nom in (("c2g88", "1 Hvid"),
                         ("c2g89", "1 Ungersk gylden"),
                         ("c2g90", "2 Ungersk gylden")):
            e = build_entry(_page(id=gid, nominal=nom,
                                  catalog_refs={"Galster": [gid[4:]]}))
            self.assertEqual((e["year_first"], e["year_last"]), (1534, 1536), gid)


if __name__ == "__main__":
    unittest.main()
