"""Regression: a reading a source-sanity gate refused is not a re-flow loss —
and excusing it must not excuse anything else.

`verify_reflow` blocks a shrinking measurement list, which is right: a weight or
a fineness that leaves a coin is normally data falling on the floor. But a value
the pipeline deliberately REFUSED is not that. NGC prints «Fineness: 35.5000» on
the Norwegian gold off-strikes struck from Speciedaler dies, 58.0 on two
different nominals and 40.7 on four; `parse_ngc.sift_fineness` declines the
number rather than guessing what it meant, and the finals lose it. Before this,
the gate reported that as a loss and hard-blocked the very commit that carried
the fix — the same trap that produced `data/v2/exclusions/` for coins and
`_retracted_refs.yml` for catalogue registers, arriving a third time for
measurements.

The excuse is deliberately narrow, and most of these tests exist to pin the
narrowness rather than the feature: one value, one field, the coins carrying one
seed. A second value in the same shrink still blocks, another field still
blocks, a citation still blocks. A ledger entry can never become a blanket
amnesty for a coin.

Added 2026-08-17.
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

_spec = importlib.util.spec_from_file_location(
    "verify_reflow", str(ROOT / "scripts" / "maintenance" / "verify_reflow.py"))
VR = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(VR)


def coin(cid, **over):
    base = {"id": cid, "nominal": "10 Ducat", "year_label": "1668",
            "metal": "gold", "fuss": "reichsdukatenfuss", "phase": "II",
            "composed_of": [cid],
            "sources": [{"type": "literature", "url": "https://example/1", "ref": "NGC"}]}
    base.update(over)
    return base


def fin(*pairs):
    return [{"source": s, "value": v} for s, v in pairs]


class TestSanityRetraction(unittest.TestCase):
    ENTITY = "test_entity"

    def _compare(self, head, cur, retracted=None):
        return VR.compare_coins(self.ENTITY, {c["id"]: c for c in head},
                                {c["id"]: c for c in cur},
                                retracted=retracted or {})

    # --- the feature ------------------------------------------------------
    def test_a_refused_reading_is_not_a_loss(self):
        head = [coin("x", fineness=fin(("ngc", 35.5)))]
        cur = [coin("x", fineness=[])]
        r = self._compare(head, cur,
                          {"fineness": {VR._key({"source": "ngc", "value": 35.5})}})
        self.assertEqual(r["losses"], [])
        self.assertEqual(len(r["retractions"]), 1)
        self.assertIn("parser retraction", r["retractions"][0])

    def test_without_a_ledger_entry_it_still_blocks(self):
        head = [coin("x", fineness=fin(("ngc", 35.5)))]
        cur = [coin("x", fineness=[])]
        r = self._compare(head, cur)
        self.assertTrue(any("LIST SHRANK" in x for x in r["losses"]))

    # --- the narrowness ---------------------------------------------------
    def test_a_second_value_in_the_same_shrink_still_blocks(self):
        head = [coin("x", fineness=fin(("ngc", 35.5), ("hede", 0.979)))]
        cur = [coin("x", fineness=[])]
        r = self._compare(head, cur,
                          {"fineness": {VR._key({"source": "ngc", "value": 35.5})}})
        self.assertTrue(any("LIST SHRANK" in x for x in r["losses"]),
                        msg="the genuine Hede reading must not ride along")
        self.assertEqual(len(r["retractions"]), 1)

    def test_the_excuse_does_not_cross_to_another_field(self):
        head = [coin("x", fineness=fin(("ngc", 35.5)),
                     weight_rough_g=fin(("ngc", 34.9)))]
        cur = [coin("x", fineness=[], weight_rough_g=[])]
        r = self._compare(head, cur,
                          {"fineness": {VR._key({"source": "ngc", "value": 35.5})}})
        self.assertTrue(any("weight_rough_g" in x for x in r["losses"]))
        self.assertFalse(any("LIST SHRANK  x.fineness" in x for x in r["losses"]))

    def test_the_excuse_does_not_cover_a_different_value_of_the_field(self):
        head = [coin("x", fineness=fin(("ngc", 58.0)))]
        cur = [coin("x", fineness=[])]
        r = self._compare(head, cur,
                          {"fineness": {VR._key({"source": "ngc", "value": 35.5})}})
        self.assertTrue(any("LIST SHRANK" in x for x in r["losses"]))

    def test_the_excuse_does_not_cover_the_same_value_from_another_source(self):
        head = [coin("x", fineness=fin(("hede", 35.5)))]
        cur = [coin("x", fineness=[])]
        r = self._compare(head, cur,
                          {"fineness": {VR._key({"source": "ngc", "value": 35.5})}})
        self.assertTrue(any("LIST SHRANK" in x for x in r["losses"]),
                        msg="the ledger names a source; another source is another reading")

    def test_a_vanished_coin_is_not_excused_by_a_value_ledger(self):
        head = [coin("x", fineness=fin(("ngc", 35.5)))]
        r = self._compare(head, [],
                          {"fineness": {VR._key({"source": "ngc", "value": 35.5})}})
        self.assertTrue(any("COIN GONE" in x for x in r["losses"]))

    def test_a_dropped_citation_is_not_excused(self):
        head = [coin("x", fineness=fin(("ngc", 35.5)))]
        cur = [coin("x", fineness=[], sources=[])]
        r = self._compare(head, cur,
                          {"fineness": {VR._key({"source": "ngc", "value": 35.5})}})
        self.assertTrue(any(".sources" in x for x in r["losses"]))


class TestLedgerLoader(unittest.TestCase):
    """Dict-form dropped values must be keyed the way the comparison keys them."""

    def test_dict_entries_are_keyed_through_key_not_str(self):
        got = VR._key({"source": "ngc", "value": 35.5})
        self.assertEqual(got, '{"source": "ngc", "value": 35.5}')
        self.assertNotEqual(got, str({"source": "ngc", "value": 35.5}))

    def test_both_ledgers_are_read(self):
        # the constants must differ, or one author silently overwrites the other
        self.assertNotEqual(VR.RETRACTED_REL, VR.SANITY_RETRACTED_REL)

    def test_the_live_ledger_covers_the_off_strike_family(self):
        fields = VR._retracted_refs("danish_norway")
        self.assertIn("fineness", fields)
        self.assertIn(VR._key({"source": "ngc", "value": 35.5}), fields["fineness"])


if __name__ == "__main__":
    unittest.main()
