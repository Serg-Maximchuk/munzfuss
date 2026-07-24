"""Regression test — EXTREME-weight hard gate in `match_pair`.

Guards the 2026-07-23 failure: a Numista-mis-tagged «Hede 39» on a
1 Portugaløser (34.47g, ~10 ducats of gold) let a SINGLE shared
authoritative Hede ref suppress BOTH the tier-1 weight disambiguator
AND the nominal discriminator at once — so the Portugaløser auto-merged
into a 6.98g 2-Dukat (dk-hede-f3h39). A ~5× weight difference must not
be overridable by one catalogue number.

The hard gate blocks any pair whose weight ratio (heavier / lighter)
exceeds 1.5, regardless of catalogue agreement. The threshold sits
safely above the wear / preservation envelope (~1.2) and far below the
different-denomination gap, so the legitimate wear-merge case
(KM 19 / Hede 56A, 28.8g vs 24.5g ≈ ratio 1.18) still merges.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import importlib.util
_spec = importlib.util.spec_from_file_location(
    "merge_seeds_cross_source",
    str(PROJECT_ROOT / "scripts" / "maintenance" / "merge_seeds_cross_source.py"),
)
_merger = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_merger)
match_pair = _merger.match_pair


class TestExtremeWeightGate(unittest.TestCase):

    def test_portugaloeser_vs_2dukat_no_match(self):
        """1 Portugaløser (34.47g, hede 39 mis-tag) vs 2 Dukat (6.98g,
        hede 39). Same shared authoritative Hede ref + same ruler + gold,
        but a 4.9× weight gap → must be no_match."""
        portugaloeser = {
            "nominal": "1 Portugaløser",
            "metal": "gold", "metal_verified": True,
            "ruler": "Frederik III",
            "weight_rough_g": 34.47,
            "catalog": {"hede": "39", "numista": "421408"},
        }
        two_dukat = {
            "nominal": "2 Dukat",
            "metal": "gold", "metal_verified": True,
            "ruler": "Frederik III",
            "weight_rough_g": 6.98,
            "catalog": {"hede": "39"},
        }
        res = match_pair(portugaloeser, two_dukat, entity_id="danish_norway")
        self.assertEqual(res["decision"], "no_match", res["why"])

    def test_wear_merge_still_allowed(self):
        """KM 19 / Hede 56A wear pair — 28.8g vs 24.5g (ratio ≈ 1.18) —
        stays UNDER the 1.5 gate, so the extreme-weight hard gate must NOT
        fire; the pair still merges per §9a multi-specimen merge."""
        a = {
            "nominal": "1 Speciedaler",
            "metal": "silver", "metal_verified": True,
            "ruler": "Frederik III",
            "weight_rough_g": 28.8,
            "mint": "Kopenhagen",
            "year_first": 1651, "year_last": 1651,
            "catalog": {"km": "19", "hede": "56A"},
        }
        b = {
            "nominal": "1 Speciedaler",
            "metal": "silver", "metal_verified": True,
            "ruler": "Frederik III",
            "weight_rough_g": 24.5,
            "mint": "Kopenhagen",
            "year_first": 1651, "year_last": 1651,
            "catalog": {"km": "19", "hede": "56A"},
        }
        res = match_pair(a, b, entity_id="danish_norway")
        self.assertNotEqual(res["decision"], "no_match", res["why"])
        # And specifically: the extreme-weight hard gate must NOT be the
        # reason for any block — the ~1.18 ratio is under the 1.5 threshold.
        self.assertFalse(
            any("ratio" in w and "hard gate" in w for w in res["why"]),
            res["why"],
        )


if __name__ == "__main__":
    unittest.main()
