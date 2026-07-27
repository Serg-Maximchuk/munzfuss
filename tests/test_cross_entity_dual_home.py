"""Regression: the cross-entity stamp dual-homes occupation coinage.

A class holding a curator-pulled member is stamped `issuing_entity` from the
merged MINT, so a joint-mint coin keeps its full list form. But when the mint
resolves to an entity that does NOT include the pull target, the two signals
disagree — the coin was struck in one jurisdiction's mint town and issued in
another's name (Christian IV's 1627 Wolfenbuettel Ducat, dk-bruun-5528 +
kmk-290902). Letting the mint win contradicted the curator's pull AND broke the
I1 home-file invariant: the class is written to the target's file while its
issuing_entity claims it belongs elsewhere. Added 2026-07-27 after that exact
I1 violation blocked a commit.

Run:
    .venv/bin/python -m unittest tests.test_cross_entity_dual_home -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "maintenance"))

import merge_seeds_cross_source as M  # noqa: E402


class TestCrossEntityIssuingEntity(unittest.TestCase):
    def test_unresolvable_mint_falls_back_to_pull_target(self):
        # never drop the class to _unclassified
        self.assertEqual(M._xentity_issuing_entity(None, "danish_realm"),
                         "danish_realm")
        self.assertEqual(M._xentity_issuing_entity("", "danish_realm"),
                         "danish_realm")

    def test_mint_entity_equal_to_target_passes_through(self):
        self.assertEqual(M._xentity_issuing_entity("gottorp_duchy", "gottorp_duchy"),
                         "gottorp_duchy")

    def test_joint_mint_list_covering_target_kept_verbatim(self):
        # KM 631 struck Altona + Kopenhagen — full list form survives, so the
        # coin stays visible on both pages via Pass 1.
        joint = ["danish_realm", "royal_holstein"]
        self.assertEqual(M._xentity_issuing_entity(joint, "royal_holstein"), joint)

    def test_occupation_coinage_dual_homes_instead_of_relocating(self):
        # Wolfenbuettel mint -> herzogtum_braunschweig_lueneburg, but the coin
        # was pulled into danish_realm. Union, do not relocate.
        got = M._xentity_issuing_entity("herzogtum_braunschweig_lueneburg",
                                        "danish_realm")
        self.assertEqual(got, ["danish_realm", "herzogtum_braunschweig_lueneburg"])

    def test_dual_home_result_is_sorted_so_home_file_is_deterministic(self):
        # home file = alphabetically first member (v2_seed_writer §3.10)
        got = M._xentity_issuing_entity("aaa_entity", "zzz_entity")
        self.assertEqual(got, ["aaa_entity", "zzz_entity"])
        self.assertEqual(got[0], "aaa_entity")


if __name__ == "__main__":
    unittest.main()
