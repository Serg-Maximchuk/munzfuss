"""A retired foundation's citations must reach the peer it merged into.

THE DEFECT
----------
`process_entity`'s stale-foundation purge drops a V1-bootstrap foundation once
the merger has consolidated its source seed into a DIFFERENT unified host, and
snapshots what must survive into `curator_migrations[host]`: the curator
classification under plain keys, and — under `__merge__sources` — the
foundation's OWN citations. The purge then prints «N entries dropped (merged
into peers)».

`curator_migrations` was read on the BULK-PROMOTE path only. A host that is
already a final is never bulk-promoted, so for those hosts the table was built
and then silently discarded: the classification migration was a no-op (harmless
— an existing final already carries its own) and the `sources` union never
happened (not harmless — every citation living solely on the retired foundation
went with it). The purge line still said «merged into peers»; the merge never
reached the peer.

That is CLAUDE.md §9a — «Deduplication is data merge, not data drop» and
«Reconciliation NEVER replaces `sources` — always UNION» — violated at the one
layer where nothing else could catch it: `audit_lost_citations` compares a final
against its own current members and the retired foundation is not one of them,
so it reported 0.

MEASURED SCOPE WHEN THIS SHIPPED
--------------------------------
The 2026-08-02 re-flow (abstain fix `6cf1c57` + foundation metal `e35973b`)
retired `unified-kmk-279034` into `unified-kmk-132460` and `unified-kmk-642893`
into `unified-dk-galster-hg-36` — both hosts already finals. Three KMM museum
specimens present in the harvest cache — 307931, 307934, 642976 — were cited by
nothing afterwards. Every other citation on those two foundations survived,
because it happened to be re-attested by a member; the three that did not were
foundation-only.

WHY ONLY THE MERGE-SHAPED FIELDS
--------------------------------
The fix applies `__merge__*` keys and deliberately leaves the replace-shaped
classification fields on the bulk-promote path. An existing final already
carries its own curator classification (fuss / phase / kind / mintmaster), and a
retired peer must not clobber it — that would trade a citation loss for a
curation loss.

Run:
    .venv/bin/python -m unittest tests.test_stale_foundation_sources_migrate -v
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "maintenance"))

_spec = importlib.util.spec_from_file_location(
    "absorb_v2",
    PROJECT_ROOT / "scripts" / "maintenance" / "absorb_seeds_into_final_v2.py")
AB = importlib.util.module_from_spec(_spec)
sys.modules["absorb_v2"] = AB
_spec.loader.exec_module(AB)

apply_migrated = AB._apply_migrated_merge_fields


def _src(url, ref=None):
    s = {"url": url, "type": "museum"}
    if ref:
        s["ref"] = ref
    return s


class TestSourcesReachTheNewHost(unittest.TestCase):

    def test_foundation_only_citation_lands_on_the_host(self):
        """The regression itself: KMM 307931 had no other attestation."""
        host = {"id": "unified-kmk-132460", "sources": [_src("kmm/132460")]}
        migrations = {
            "unified-kmk-132460": {
                "__merge__sources": [_src("kmm/279034"),
                                     _src("kmm/307931", "KMM 307931")],
            }
        }
        apply_migrated(host, "unified-kmk-132460", [], migrations)
        self.assertEqual(
            {s["url"] for s in host["sources"]},
            {"kmm/132460", "kmm/279034", "kmm/307931"},
        )

    def test_union_never_replaces(self):
        """§9a: the host's own citations survive the migration."""
        host = {"id": "h", "sources": [_src("a"), _src("b")]}
        apply_migrated(host, "h", [], {"h": {"__merge__sources": [_src("c")]}})
        self.assertEqual([s["url"] for s in host["sources"]], ["a", "b", "c"])

    def test_duplicate_url_is_not_doubled(self):
        host = {"id": "h", "sources": [_src("a")]}
        apply_migrated(host, "h", [],
                       {"h": {"__merge__sources": [_src("a"), _src("b")]}})
        self.assertEqual([s["url"] for s in host["sources"]], ["a", "b"])

    def test_host_reached_through_composed_of(self):
        """A `km-*` foundation hosts the unified class under another id."""
        final = {"id": "km-x005-chr-iv-1620", "sources": [_src("a")]}
        apply_migrated(
            final, "km-x005-chr-iv-1620", ["unified-dk-numista-142941"],
            {"unified-dk-numista-142941": {"__merge__sources": [_src("b")]}})
        self.assertEqual([s["url"] for s in final["sources"]], ["a", "b"])

    def test_no_migration_leaves_the_entry_untouched(self):
        host = {"id": "h", "sources": [_src("a")]}
        apply_migrated(host, "h", [], {})
        self.assertEqual(host, {"id": "h", "sources": [_src("a")]})

    def test_classification_fields_are_not_applied(self):
        """Replace-shaped keys stay on the bulk-promote path.

        An existing final's own curator classification must not be clobbered by
        a retired peer — that would trade a citation loss for a curation loss.
        """
        host = {"id": "h", "fuss": "reichsdukatenfuss", "phase": "I"}
        apply_migrated(host, "h", [],
                       {"h": {"fuss": "kurantmoentfod", "phase": "III",
                              "__merge__sources": [_src("a")]}})
        self.assertEqual(host["fuss"], "reichsdukatenfuss")
        self.assertEqual(host["phase"], "I")
        self.assertEqual([s["url"] for s in host["sources"]], ["a"])

    def test_host_with_no_sources_yet(self):
        host = {"id": "h"}
        apply_migrated(host, "h", [], {"h": {"__merge__sources": [_src("a")]}})
        self.assertEqual([s["url"] for s in host["sources"]], ["a"])

    def test_direct_id_match_wins_over_composed_of(self):
        host = {"id": "h", "sources": []}
        apply_migrated(host, "h", ["other"],
                       {"h": {"__merge__sources": [_src("mine")]},
                        "other": {"__merge__sources": [_src("theirs")]}})
        self.assertEqual([s["url"] for s in host["sources"]], ["mine"])


if __name__ == "__main__":
    unittest.main()
