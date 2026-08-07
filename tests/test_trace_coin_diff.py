"""Tests for trace_coin's snapshot diff classifier.

WHY THIS EXISTS
---------------
`trace_coin.py diff` is a verification instrument — it is what a re-flow is
measured with (CLAUDE.md §9b). It had no tests, and it reported a loss that
was not one on two separate occasions:

  * 2026-08-02, the «13 KMM URLs» report: a dissolved class's citations split
    between two survivors.
  * 2026-08-04, the Christiania 3-Dukat re-grouping:
    denmark-numismaster-110811 and dk-tid-145797 moved from a 4-source class
    to a 3-source one and were reported as «2 real losses», while
    audit_lost_citations said 0 and the entity's whole URL set was unchanged
    at 3691 before and after.

Both are the same mistake: `sources` is the count on the FINAL a seed belongs
to, so a seed that MOVES to a smaller class looks like it lost data when all
that changed is its neighbours. The fix mirrors the split the file already
draws for fuss/phase — same class vs different class — and these tests pin it
from both sides, so the informational bucket can never quietly swallow a real
loss either.
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "trace_coin",
    Path(__file__).resolve().parent.parent / "scripts" / "maintenance" / "trace_coin.py",
)
TC = importlib.util.module_from_spec(_spec)
sys.modules["trace_coin"] = TC
_spec.loader.exec_module(TC)


def rec(final=None, fuss=None, phase=None, sources=None, entity="danish_norway"):
    return {"source": "numista", "seed_entity": entity, "unified": None,
            "final": final, "final_entity": entity if final else None,
            "fuss": fuss, "phase": phase, "sources": sources}


class TestSourceCountSplit(unittest.TestCase):
    """The 2026-08-04 false positive and its mirror image."""

    def test_moved_to_smaller_class_is_not_a_loss(self):
        r = TC.classify_diff(
            {"s": rec(final="unified-A", fuss="reichsdukatenfuss", phase="II", sources=4)},
            {"s": rec(final="unified-B", fuss="reichsdukatenfuss", phase="II", sources=3)})
        self.assertEqual(r["fewer_sources"], [])
        self.assertEqual(len(r["smaller_host"]), 1)
        self.assertEqual(r["losses"], 0)

    def test_same_class_losing_sources_is_still_a_loss(self):
        r = TC.classify_diff(
            {"s": rec(final="unified-A", fuss="reichsdukatenfuss", phase="II", sources=4)},
            {"s": rec(final="unified-A", fuss="reichsdukatenfuss", phase="II", sources=3)})
        self.assertEqual(len(r["fewer_sources"]), 1)
        self.assertEqual(r["smaller_host"], [])
        self.assertEqual(r["losses"], 1)

    def test_moving_to_a_larger_class_reports_nothing(self):
        r = TC.classify_diff(
            {"s": rec(final="unified-A", fuss="x", phase="I", sources=2)},
            {"s": rec(final="unified-B", fuss="x", phase="I", sources=5)})
        self.assertEqual(r["fewer_sources"], [])
        self.assertEqual(r["smaller_host"], [])
        self.assertEqual(r["losses"], 0)

    def test_a_seed_that_lost_its_final_is_not_masked_by_the_move_branch(self):
        # No destination at all — the move branch must not swallow this.
        r = TC.classify_diff(
            {"s": rec(final="unified-A", fuss="x", phase="I", sources=4)},
            {"s": rec(final=None, fuss=None, phase=None, sources=None)})
        self.assertEqual(len(r["lost_final"]), 1)
        self.assertEqual(r["smaller_host"], [])
        self.assertGreaterEqual(r["losses"], 1)


class TestRealLossesStillBlock(unittest.TestCase):
    def test_seed_vanished(self):
        r = TC.classify_diff({"s": rec(final="unified-A", sources=1)}, {})
        self.assertEqual(r["gone"], ["s"])
        self.assertEqual(r["losses"], 1)

    def test_reclassified_in_place(self):
        r = TC.classify_diff(
            {"s": rec(final="unified-A", fuss="reichsdukatenfuss", phase="II", sources=1)},
            {"s": rec(final="unified-A", fuss="seed_unsorted", phase="numista", sources=1)})
        self.assertEqual(len(r["reclassified"]), 1)
        self.assertEqual(r["losses"], 1)


class TestExpectedChurnIsNotALoss(unittest.TestCase):
    def test_promotion_out_of_seed_unsorted(self):
        r = TC.classify_diff(
            {"s": rec(final="unified-A", fuss="seed_unsorted", phase="numista", sources=1)},
            {"s": rec(final="unified-B", fuss="reichsdukatenfuss", phase="II", sources=1)})
        self.assertEqual(len(r["promoted"]), 1)
        self.assertEqual(r["losses"], 0)

    def test_class_rename_alone(self):
        r = TC.classify_diff(
            {"s": rec(final="unified-dk-bruun-7749", fuss="x", phase="I", sources=3)},
            {"s": rec(final="unified-dk-hede-c7h8", fuss="x", phase="I", sources=3)})
        self.assertEqual(len(r["renamed_class"]), 1)
        self.assertEqual(r["losses"], 0)

    def test_adopting_the_host_classification_is_reported_but_not_a_loss(self):
        r = TC.classify_diff(
            {"s": rec(final="unified-A", fuss="9_25_thaler", phase="I", sources=2)},
            {"s": rec(final="unified-B", fuss="reichsdukatenfuss", phase="II", sources=2)})
        self.assertEqual(len(r["adopted"]), 1)
        self.assertEqual(r["losses"], 0)


if __name__ == "__main__":
    unittest.main()
