"""Regression: an ABSENT field must never veto a merge.

CLAUDE.md §4 fixes the rule for an unverified value — «A `*_verified: false`
value cannot DISPROVE a merge»: the comparator returns `unknown` (None), never
False, and the primary-signal majority decides. An ABSENT value is strictly
weaker still — it asserts nothing at all — so it must be at least as inert.

Every per-field comparator already honoured that (`_normalise_metal`,
`_weight_diverges`, `_mints_overlap`, `_catalog_chain_consistent` all return
None on absence). The defect was one layer up, in how `_match_pair_core`
LABELLED the resulting verdict: with nothing to affirm the merge and nothing
disagreeing either, it fell through to `no_match` — the same token PASS 2 turns
into a TRANSITIVE `UnionFind.no_merge` constraint. So a record that merely
fails to describe itself could veto unions between OTHER records that matched
confidently.

Measured case (2026-08-01, entity `danish_realm`): KMM museum records of the
1813-1815 Rigsbanktegn carry no metal and no weight. `denmark-numismaster-66282`
carries no ruler. The pair scored primary_true=0 with ZERO disagreements, was
recorded as `no_match`, and the resulting no_merge blocked
`kmk-122613 ↔ kmk-152042` — a `confident` pair agreeing on hede 23 + nominal +
ruler — expelling 15 specimens into kmk-only classes.

Fix: that tail returns `abstain`, which PASS 1 (collects only confident /
low_confidence) and PASS 2 (tests `== "no_match"`) both ignore. `no_match` now
means CONTRADICTED; `abstain` means NOT ENOUGH EVIDENCE.

Run:
    .venv/bin/python -m unittest tests.test_absence_does_not_veto -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "maintenance"))

import merge_seeds_cross_source as M  # noqa: E402

ENTITY = "danish_realm"


def _coin(cid, **kw):
    """A 1815 2-Rigsbankskilling shaped like the real seeds. Any field passed
    as None is left ABSENT rather than set — that is the case under test."""
    base = {
        "id": cid,
        "nominal": "2 Rigsbankskilling",
        "ruler": "Frederik 6",
        "year_first": 1815,
        "year_last": 1815,
        "catalog": {"hede": "23"},
    }
    base.update(kw)
    return {k: v for k, v in base.items() if v is not None}


class TestAbsenceDoesNotVeto(unittest.TestCase):
    """An absent value abstains; it never disproves and never vetoes."""

    def test_absent_metal_vs_present_metal_does_not_block(self):
        """The exact expelled pair: metal absent on one side, attested on the
        other, everything else agreeing. Must stay mergeable."""
        a = _coin("kmk-122613")                                   # no metal
        b = _coin("kmk-152042", metal="copper", metal_verified=True)
        r = M.match_pair(a, b, ENTITY)
        self.assertEqual(r["decision"], "confident", r["why"])
        self.assertIsNone(r["primary"]["metal"],
                          "absent metal must be unknown, not False")

    def test_absent_everywhere_abstains_never_no_match(self):
        """`denmark-numismaster-66282` (no ruler, different nominal label,
        different catalogue register) vs a KMM record (no metal, no weight).
        Nothing disagrees; nothing affirms. Must abstain, NOT no_match —
        no_match would become a transitive no_merge and expel the peers."""
        a = _coin("denmark-numismaster-66282", nominal="2 Skilling",
                  ruler=None, metal="copper", metal_verified=True,
                  weight_rough_g=1.5, catalog={"km": "Tn4"})
        b = _coin("kmk-122613")
        r = M.match_pair(a, b, ENTITY)
        self.assertEqual(r["decision"], "abstain", r["why"])
        self.assertNotIn(False, list(r["primary"].values()),
                         "abstain must rest on absence, not on a disagreement")

    def test_abstain_is_inert_in_pass2(self):
        """PASS 2 registers a no_merge only for `no_match`. Guard the contract
        the fix depends on: abstain must not be spelled no_match."""
        a = _coin("denmark-numismaster-66282", nominal="2 Skilling",
                  ruler=None, metal="copper", metal_verified=True,
                  weight_rough_g=1.5, catalog={"km": "Tn4"})
        b = _coin("kmk-122613")
        self.assertNotEqual(M.match_pair(a, b, ENTITY)["decision"], "no_match")

    def test_unverified_vs_verified_metal_still_deferred(self):
        """§4 consequence #1, already shipped — assert it did not regress."""
        a = _coin("dk-tid-81021", metal="billon", metal_verified=False)
        b = _coin("denmark-numismaster-66285", metal="copper",
                  metal_verified=True)
        r = M.match_pair(a, b, ENTITY)
        self.assertIsNone(r["primary"]["metal"],
                          "an unverified metal cannot disprove a verified one")
        self.assertNotEqual(r["decision"], "no_match", r["why"])

    def test_both_verified_and_different_still_blocks(self):
        """The fix must not soften a REAL disagreement: two attested, differing
        metals remain a hard no_match."""
        a = _coin("x-1", metal="silver", metal_verified=True)
        b = _coin("x-2", metal="copper", metal_verified=True)
        r = M.match_pair(a, b, ENTITY)
        self.assertEqual(r["decision"], "no_match", r["why"])
        self.assertIs(r["primary"]["metal"], False)

    def test_disagreeing_catalogue_still_blocks(self):
        """Contradiction on the load-bearing catalogue key stays no_match."""
        a = _coin("y-1", catalog={"hede": "23"}, metal="copper",
                  metal_verified=True)
        b = _coin("y-2", catalog={"hede": "99"}, metal="copper",
                  metal_verified=True)
        r = M.match_pair(a, b, ENTITY)
        self.assertEqual(r["decision"], "no_match", r["why"])


if __name__ == "__main__":
    unittest.main()
