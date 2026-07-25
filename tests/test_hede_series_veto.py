"""Regression: the Danish and Norwegian Hede volumes number independently,
and the matcher must not fuse them on a shared bare index.

danskmoent.dk prints the Danish volumes as «Hede 39» and the Norwegian ones as
«Hede Norge 39» — two separate series. `_catalog_refs` scopes the Hede key by
RULER, which both series share, so «hede/frederik iii = 39» collides by
construction. Within one entity the two never meet, but a cross-entity curator
pull puts a Danish-bucket record into the Norwegian run, where the collision is
reachable: `dk-hede-f3h39` (2 Dukat, gold) and `dk-hede-nf3h39` (1 Speciedaler,
silver) are different coins sharing the bare index 39.

The gate is a VETO on `catalog.hede_volume`, not a key component — it fires only
when BOTH sides know their series. Bruun / KMK / Numista / IKMK cite a bare
«Hede-4» with no volume; requiring the series on both sides would strand the
1614 volume-less Hede records in `danish_norway` against the 259 that have it.
An unknown series is «inherit», never a mismatch (same convention as the
`*_verified` comparisons and `KMRef.register = None`).

Added 2026-07-25 after the collision was measured across the live seeds.

Run:
    .venv/bin/python -m unittest tests.test_hede_series_veto -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "maintenance"))

import merge_seeds_cross_source as M  # noqa: E402


def _coin(cid, volume, hede, nominal, metal):
    return {
        "id": cid,
        "nominal": nominal,
        "metal": metal,
        "ruler": "Frederik III.",
        "year_first": 1665,
        "year_last": 1665,
        "mint": "Christiania",
        "catalog": {"hede": hede, "hede_volume": volume},
    }


class TestHedeSeriesDerivation(unittest.TestCase):
    def test_norwegian_volume_reads_as_no(self):
        self.assertEqual(M._hede_series(_coin("a", "nf3h", "39", "x", "silver")), "no")

    def test_danish_volume_reads_as_dk(self):
        self.assertEqual(M._hede_series(_coin("a", "f3h", "39", "x", "gold")), "dk")

    def test_absent_volume_is_unknown_not_danish(self):
        """A bare Bruun/Numista «Hede-4» must be None — «unknown», so it can
        still merge with either series. Returning «dk» here would silently
        break the Bruun ↔ Hede Norge links."""
        bare = {"id": "b", "nominal": "x", "metal": "gold",
                "catalog": {"hede": "4"}}
        self.assertIsNone(M._hede_series(bare))
        self.assertIsNone(M._hede_series({"id": "c", "catalog": {}}))


class TestHedeSeriesVeto(unittest.TestCase):
    def test_cross_series_pair_is_vetoed(self):
        """The real Hede-39 pair: same ruler, same bare index, different series."""
        a = _coin("dk-hede-nf3h39", "nf3h", "39", "1 Speciedaler", "silver")
        b = _coin("dk-hede-f3h39", "f3h", "39", "2 Dukat", "gold")
        r = M.match_pair(a, b, "danish_norway")
        self.assertEqual(r["decision"], "no_match")
        self.assertTrue(any("hede series differs" in w for w in r["why"]))

    def test_veto_fires_even_when_every_other_signal_agrees(self):
        """The point of the gate: without it, a cross-series pair agreeing on
        metal + nominal + ruler + index would auto-merge. Other signals must
        not be what saves us."""
        a = _coin("dk-hede-nf3h39", "nf3h", "39", "1 Speciedaler", "silver")
        b = _coin("dk-hede-f3h39", "f3h", "39", "1 Speciedaler", "silver")
        self.assertEqual(M.match_pair(a, b, "danish_norway")["decision"], "no_match")

    def test_same_series_pair_is_not_vetoed(self):
        """Two Norwegian records must stay eligible — the veto is cross-series
        only, never a blanket block on Hede volumes."""
        a = _coin("dk-hede-nf3h39", "nf3h", "39", "1 Speciedaler", "silver")
        b = _coin("dk-hede-nf3h39x", "nf3h", "39", "1 Speciedaler", "silver")
        self.assertNotEqual(M.match_pair(a, b, "danish_norway")["decision"], "no_match")

    def test_unknown_series_side_is_not_vetoed(self):
        """A volume-less Bruun record must remain mergeable with Hede Norge —
        this is the 435-pair class the gate must not touch."""
        norge = _coin("dk-hede-nf3h39", "nf3h", "39", "1 Speciedaler", "silver")
        bruun = {"id": "dk-bruun-1", "nominal": "1 Speciedaler", "metal": "silver",
                 "ruler": "Frederik III.", "year_first": 1665, "year_last": 1665,
                 "mint": "Christiania", "catalog": {"hede": "39"}}
        self.assertNotEqual(
            M.match_pair(norge, bruun, "danish_norway")["decision"], "no_match")


if __name__ == "__main__":
    unittest.main()
