"""`verify_reflow` must call a loss a loss, and never call a gain one.

The tool answers the one question no other auditor in this project answers: is
the working tree WORSE than what is committed? Everything else measures inside
the tree — `audit_curation_loss` compares a final against what the next absorb
would recompute, `audit_lost_citations` against its own current members,
`audit_v2` checks invariants within one state, and `trace_coin` diffs two
snapshots that a human took by hand.

That last one is where it kept going wrong. On 2026-08-01 four hand-built
baselines were each wrong differently: a truncated cache field, a resolution
scoped to one entity while cross-entity members live elsewhere, a snapshot of a
half-applied pipeline, and a diff nobody read. A committed baseline removes the
whole class — `git show HEAD:` cannot be half-applied or truncated.

These tests pin the classification, which is the part with judgement in it:

  GAIN, never blocks — a new coin, a new reading, a scalar filling in, a
  catalogue register gaining a value, and a coin removed because a survivor
  absorbed it (that is `dedup_final_foundations`' fold, and it is how six
  duplicate Rigsbanktegn finals were legitimately retired the same day).

  LOSS, always blocks — a coin gone with nothing absorbing it, a scalar
  emptied, a list or catalogue register that shrank, a fuss/phase demoted back
  to seed_unsorted.

Run:
    .venv/bin/python -m unittest tests.test_verify_reflow -v
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "verify_reflow", PROJECT_ROOT / "scripts" / "maintenance" / "verify_reflow.py")
VR = importlib.util.module_from_spec(_spec)
sys.modules["verify_reflow"] = VR
_spec.loader.exec_module(VR)


class _Base(unittest.TestCase):
    """Drive the classifier directly — no git tree, no filesystem, no stubs."""

    def run_case(self, head, cur):
        idx = lambda lst: {c["id"]: c for c in lst}
        return VR.compare_coins("stub", idx(head), idx(cur))


class TestLosses(_Base):
    def test_coin_gone_with_no_absorber(self):
        r = self.run_case([{"id": "a", "nominal": "1 Dukat",
                            "sources": [{"url": "u1"}]}], [])
        self.assertTrue(any("COIN GONE" in m for m in r["losses"]))

    def test_scalar_emptied(self):
        r = self.run_case([{"id": "a", "mint": "Kopenhagen"}],
                          [{"id": "a", "mint": None}])
        self.assertTrue(any("FIELD EMPTIED" in m for m in r["losses"]))

    def test_list_shrank(self):
        r = self.run_case(
            [{"id": "a", "sources": [{"url": "u1"}, {"url": "u2"}]}],
            [{"id": "a", "sources": [{"url": "u1"}]}])
        self.assertTrue(any("LIST SHRANK" in m for m in r["losses"]))

    def test_catalogue_register_shrank(self):
        r = self.run_case([{"id": "a", "catalog": {"km": ["1", "2"]}}],
                          [{"id": "a", "catalog": {"km": ["1"]}}])
        self.assertTrue(any("CATALOG SHRANK" in m for m in r["losses"]))

    def test_demoted_to_seed_unsorted(self):
        r = self.run_case([{"id": "a", "fuss": "reichsdukatenfuss"}],
                          [{"id": "a", "fuss": "seed_unsorted"}])
        self.assertTrue(any("DEMOTED" in m for m in r["losses"]))


class TestGains(_Base):
    def test_new_coin(self):
        r = self.run_case([], [{"id": "a"}])
        self.assertEqual(r["losses"], [])

    def test_scalar_filling_in(self):
        r = self.run_case([{"id": "a", "mint": None}],
                          [{"id": "a", "mint": "Kopenhagen"}])
        self.assertEqual(r["losses"], [])

    def test_list_growing(self):
        r = self.run_case([{"id": "a", "sources": [{"url": "u1"}]}],
                          [{"id": "a", "sources": [{"url": "u1"}, {"url": "u2"}]}])
        self.assertEqual(r["losses"], [])

    def test_fold_recognised_via_composed_of(self):
        # dedup_final_foundations pins the dropped id on the survivor.
        r = self.run_case(
            [{"id": "keep"}, {"id": "drop", "sources": [{"url": "u1"}]}],
            [{"id": "keep", "composed_of": ["drop"]}])
        self.assertEqual(r["losses"], [])
        self.assertTrue(any("folded into keep" in g for g in r["gains"]))

    def test_fold_recognised_via_absorbed_sources(self):
        # The I2 fix strips a pin that no longer resolves, so a real fold can
        # arrive with the survivor merely carrying the dropped coin's URLs —
        # which is exactly how the six Rigsbanktegn pairs ended up on disk.
        r = self.run_case(
            [{"id": "keep", "sources": [{"url": "u1"}]},
             {"id": "drop", "sources": [{"url": "u1"}, {"url": "u2"}]}],
            [{"id": "keep", "sources": [{"url": "u1"}, {"url": "u2"}]}])
        self.assertEqual(r["losses"], [])

    def test_partial_absorption_is_still_a_loss(self):
        # Survivor carries only SOME of the dropped coin's sources → not a fold.
        r = self.run_case(
            [{"id": "keep", "sources": [{"url": "u1"}]},
             {"id": "drop", "sources": [{"url": "u2"}, {"url": "u3"}]}],
            [{"id": "keep", "sources": [{"url": "u1"}, {"url": "u2"}]}])
        self.assertTrue(any("COIN GONE" in m for m in r["losses"]))


if __name__ == "__main__":
    unittest.main()
