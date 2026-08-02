"""A final's own stored metal is a derived value, not a second source.

`_enrich_final_entry` passes the FINAL entry as `members[0]` so a curated
foundation wins scalar gap-fill. `_collect_metal`'s verified-vs-verified guard
was written for a different situation — two independent SOURCES disagreeing,
the 2026-06-20 f6h17 case where a KMM museum «soelv» silently beat Hede
«copper» — and could not tell that apart from a final whose stored value simply
lags the members it is derived from. So the absorb aborted on the second case as
if it were the first, and the final could never be recomputed.

The tell was in the error text: both sides printed the SAME id —
«billon=unified-dk-bruun-8027, copper=unified-dk-bruun-8027» — because a final
named after its unified class collides with that class in the member list. The
partition therefore cannot key on id; it keys on POSITION, which is the
documented contract of `_enrich_final_entry`.

Resolution follows a rule the project already has rather than a new one: per
CLAUDE.md «Manual-override preservation», `_curation_holds` marks a value as
deliberate, and a field without one is derived and regenerable. So a held metal
stands and a loose one follows its members. Disagreement WITHIN the members is
untouched and still raises.

Measured scope when this shipped: 12 finals carried a metal no verified member
attested; 8 were the silver/billon thin line (already not a conflict) and 4 were
the Rigsbanktegn 1813-1815 finals reading `billon` against four seeds reading
`copper` — three of them verified — with no curation hold on any of them.

Run:
    .venv/bin/python -m unittest tests.test_foundation_metal_is_not_a_source -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "maintenance"))

import merge_seeds_cross_source as M  # noqa: E402


def coin(cid, metal, verified=True):
    return {"id": cid, "metal": metal, "metal_verified": verified}


class TestFoundationVsMembers(unittest.TestCase):
    """members[0] is the final itself; the rest are real sources."""

    def test_loose_foundation_follows_its_members(self):
        members = [coin("unified-dk-bruun-8027", "billon"),   # the final
                   coin("unified-dk-bruun-8027", "copper")]   # its unified twin
        self.assertEqual(
            M._collect_metal(members, foundation_first=True), "copper")

    def test_held_foundation_keeps_its_value(self):
        members = [coin("km-99", "billon"), coin("unified-x", "copper")]
        self.assertEqual(
            M._collect_metal(members, foundation_first=True,
                             foundation_holds={"metal"}),
            "billon")

    def test_several_members_agreeing_still_resolve(self):
        members = [coin("km-99", "billon"),
                   coin("a", "copper"), coin("b", "copper"), coin("c", "copper")]
        self.assertEqual(
            M._collect_metal(members, foundation_first=True), "copper")

    def test_foundation_id_colliding_with_a_member_id_is_fine(self):
        # The exact shape that made an id-based partition impossible.
        members = [coin("unified-dk-bruun-8032", "billon"),
                   coin("unified-dk-bruun-8032", "copper")]
        self.assertEqual(
            M._collect_metal(members, foundation_first=True), "copper")


class TestGenuineConflictsStillRaise(unittest.TestCase):
    def test_members_disagreeing_among_themselves(self):
        # The f6h17 case: two real sources, both verified, both wrong to pick
        # silently. Unchanged.
        members = [coin("km-99", "copper"),
                   coin("kmk-1", "silver"), coin("dk-hede-x", "copper")]
        with self.assertRaises(M.MetalConflictError):
            M._collect_metal(members, foundation_first=True)

    def test_merger_path_is_untouched(self):
        # No foundation in the merger — every member is an independent source,
        # so any verified disagreement must still abort.
        members = [coin("kmk-1", "silver"), coin("dk-hede-x", "copper")]
        with self.assertRaises(M.MetalConflictError):
            M._collect_metal(members)

    def test_default_keeps_the_old_behaviour_for_the_same_input(self):
        members = [coin("unified-dk-bruun-8027", "billon"),
                   coin("unified-dk-bruun-8027", "copper")]
        with self.assertRaises(M.MetalConflictError):
            M._collect_metal(members)


class TestUnrelatedPathsUnchanged(unittest.TestCase):
    def test_thin_line_still_resolves_by_authority(self):
        # silver <-> billon is the same metal under looser/tighter labels.
        members = [coin("kmk-1", "silver"), coin("dk-hede-x", "billon")]
        self.assertIn(M._collect_metal(members, foundation_first=True),
                      {"silver", "billon"})

    def test_unanimous_members_need_no_special_case(self):
        members = [coin("a", "gold"), coin("b", "gold")]
        self.assertEqual(M._collect_metal(members, foundation_first=True), "gold")

    def test_unverified_foundation_never_reached_the_guard(self):
        # §4 tier 1 already prefers the verified member; no conflict arises.
        members = [coin("km-99", "billon", verified=False), coin("a", "copper")]
        self.assertEqual(
            M._collect_metal(members, foundation_first=True), "copper")


if __name__ == "__main__":
    unittest.main()
