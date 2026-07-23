"""Curator `no_merges` bind the absorb layer, not just the cross-source merger.

Functions under test:
    scripts/maintenance/absorb_seeds_into_final_v2.py ::
        _load_no_merge_pairs, _entry_seed_ids, _curator_no_merged

Context — the bug this guards against (2026-07-23, reverted cross-entity
f3h39 -> 6737 merge):

`danish_norway` holds two coins the curator explicitly split by image:
  * the Hede 39 / km A119 group (dk-bruun-6737 + 6738 + numismaster-204386
    + numista-460032), and
  * dk-tid-145589 — a DIFFERENT coin whose km A119 is a ucoin mis-tag.
Four `no_merges` pairs keep them apart, and the cross-source merger honours
them, so seed_unified correctly carries two separate unified entries.

At the FINAL layer they nonetheless stayed apart only by luck: the final
foundation `unified-dk-bruun-6737` matched its unified entry 1:1 by exact id,
so no content match was ever attempted. The moment a cross-entity merge
renamed the group's unified id (bruun-6737 -> hede-f3h39, Hede outranks
Bruun), that exact-id tie broke, absorb fell back to matching by content —
shared km A119 — and folded BOTH km-A119 finals into one entry.

Three defects made that possible:
  1. The final<->final self-foundation fold consulted `no_merges` not at all —
     the primary defect, and the one that folds two FINALS together.
  2. Seed resolution never stripped the `unified-` prefix. This bites in the
     post-rename shape specifically: the foundation's only composed_of member
     was the vanished old unified id, so the stale-composed_of purge empties
     it and the `unified-dk-bruun-6737` id is all that is left to resolve —
     which never matched the curator's bare-seed `dk-bruun-6737`. (When
     composed_of still holds live members, expansion through them reached the
     bare seeds and the pre-fix lookup did fire; the strip is what makes
     resolution hold in the degenerate self-link / emptied shape.)
  3. Only the per-entity decision file was read; `_cross_entity.yml` no_merges
     were ignored entirely.

Run via:
    .venv/bin/python -m unittest tests.test_absorb_no_merges_authority -v
"""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

_spec = importlib.util.spec_from_file_location(
    "absorb_seeds_into_final_v2",
    str(PROJECT_ROOT / "scripts" / "maintenance"
        / "absorb_seeds_into_final_v2.py"),
)
_absorb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_absorb)

ENTITY = "danish_norway"

# The four curator pairs from data/v2/merge_decisions/danish_norway.yml —
# every km-A119 edge out of dk-tid-145589, closed.
_DECISION_YML = """
no_merges:
  - members: [dk-tid-145589, dk-bruun-6737]
    reason: 'Curator 2026-07-23 by image: different coin; km A119 is a ucoin mis-tag.'
  - members: [dk-tid-145589, dk-bruun-6738]
    reason: 'Same split: Sieg 139 die-variant of the Hede 39 group.'
  - members: [dk-tid-145589, dk-numismaster-204386]
    reason: 'Same split: km-A119-only, so union-find cannot reconnect it.'
  - members: [dk-tid-145589, dk-numista-460032]
    reason: 'Same split: closes the last km-A119 edge.'
"""

_CROSS_ENTITY_YML = """
no_merges:
  - members: [dk-tid-145589, dk-realm-someseed]
    reason: 'Cross-entity split — must bind the absorb too.'
"""


class NoMergesAuthorityTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        d = Path(self._tmp.name)
        (d / f"{ENTITY}.yml").write_text(_DECISION_YML, encoding="utf-8")
        (d / "_cross_entity.yml").write_text(_CROSS_ENTITY_YML, encoding="utf-8")
        self._orig = _absorb.V2_MERGE_DECISIONS
        _absorb.V2_MERGE_DECISIONS = d
        self.pairs = _absorb._load_no_merge_pairs(ENTITY)

    def tearDown(self):
        _absorb.V2_MERGE_DECISIONS = self._orig
        self._tmp.cleanup()

    # ---- loading -------------------------------------------------------

    def test_loads_entity_and_cross_entity_pairs(self):
        """Both decision files feed the pair set (cross-entity was ignored)."""
        self.assertIn(frozenset({"dk-tid-145589", "dk-bruun-6737"}), self.pairs)
        self.assertIn(frozenset({"dk-tid-145589", "dk-realm-someseed"}),
                      self.pairs)
        self.assertEqual(len(self.pairs), 5)

    # ---- seed resolution ------------------------------------------------

    def test_entry_seed_ids_strips_unified_prefix_at_every_hop(self):
        """The prefix strip is the load-bearing fix: a final foundation keyed
        `unified-X` must resolve to the bare seed `X` the curator named."""
        unified = {
            "id": "unified-dk-hede-f3h39",
            "composed_of": ["dk-bruun-6737", "dk-numista-460032"],
        }
        final = {
            "id": "unified-dk-bruun-6737",
            "composed_of": ["unified-dk-hede-f3h39"],
        }
        seeds = _absorb._entry_seed_ids(
            final, {"unified-dk-hede-f3h39": unified})
        self.assertIn("dk-bruun-6737", seeds)          # own id, prefix stripped
        self.assertIn("dk-hede-f3h39", seeds)          # member, prefix stripped
        self.assertIn("dk-numista-460032", seeds)      # member's own seed
        self.assertFalse([s for s in seeds if s.startswith("unified-")])

    # ---- the regression -------------------------------------------------

    def test_no_merge_survives_unified_id_rename(self):
        """THE regression: the pair must hold when one side's unified id
        changes (bruun-6737 -> hede-f3h39) and the exact-id tie is lost, so
        only content matching (shared km A119) would otherwise fire."""
        # Post-rename: the Hede 39 group's final foundation still carries the
        # OLD bruun-derived id, while its unified entry has been renamed. The
        # foundation's only composed_of member was the vanished old unified id,
        # so the stale-composed_of purge has already emptied it — leaving the
        # `unified-`-prefixed id as the entry's SOLE identity signal. That is
        # the shape the self-foundation fold works on, and the shape where the
        # prefix strip is load-bearing: without it nothing here resolves to the
        # curator's bare-seed member `dk-bruun-6737`.
        renamed_unified = {
            "id": "unified-dk-hede-f3h39",
            "catalog": {"km": "A119"},
            "composed_of": ["dk-bruun-6737", "dk-bruun-6738",
                            "dk-numismaster-204386", "dk-numista-460032"],
        }
        group_final = {
            "id": "unified-dk-bruun-6737",
            "catalog": {"km": "A119"},
            "composed_of": [],
        }
        tid_final = {
            "id": "unified-dk-tid-145589",
            "catalog": {"km": "A119"},
            "composed_of": ["dk-tid-145589"],
        }
        unified_by_id = {"unified-dk-hede-f3h39": renamed_unified}

        self.assertTrue(
            _absorb._curator_no_merged(
                tid_final, group_final, self.pairs, unified_by_id),
            "curator no_merge must block the km-A119 fold after the rename",
        )
        # Symmetric — argument order must not matter.
        self.assertTrue(
            _absorb._curator_no_merged(
                group_final, tid_final, self.pairs, unified_by_id))
        # And against the renamed unified entry itself (absorb-loop direction).
        self.assertTrue(
            _absorb._curator_no_merged(
                renamed_unified, tid_final, self.pairs, unified_by_id))

    def test_unrelated_pair_still_merges(self):
        """The guard must not become a blanket veto: a pair the curator never
        split stays mergeable."""
        a = {"id": "unified-dk-bruun-6737", "composed_of": ["dk-bruun-6737"]}
        b = {"id": "unified-dk-bruun-6738", "composed_of": ["dk-bruun-6738"]}
        self.assertFalse(
            _absorb._curator_no_merged(a, b, self.pairs, {}))

    def test_empty_pair_set_is_permissive(self):
        a = {"id": "unified-dk-tid-145589"}
        b = {"id": "unified-dk-bruun-6737"}
        self.assertFalse(_absorb._curator_no_merged(a, b, set(), {}))


if __name__ == "__main__":
    unittest.main()
