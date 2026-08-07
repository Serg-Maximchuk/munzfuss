"""A source's misspelling of a king must not cost the Galster volume scope.

Galster restarts its numbering per reign, so `_catalog_refs` keys it
`galster/<vol>` and derives the volume from the ruler when the record carries
no `galster_volume` of its own. natmus.dk publishes some rulers misspelled in
its OWN `authority` field — «Cristian 3» (kmk-317953), «Chrsitian 2»
(kmk-684506), «Chrsitan 2» (kmk-733358) — and the seeds record that verbatim,
which is correct: changing the stored value would be a §CN source erratum and
needs the curator. Changing how a KEY is derived from it does not.

Without the aliases those records fall to the bare `galster` scope, which never
overlaps `galster/c2g` or `galster/c3g`, so a legitimate merge on a shared
Galster number is silently refused. Measured 2026-08-07: 14 Galster values sat
in both the bare and a scoped bucket; these three account for two of them.

The table is explicit on purpose. A similarity threshold would also map
«Christian» (no ordinal, genuinely ambiguous) and the non-regnal authorities
Galster catalogues inside a king's volume — Rigsraadet, Interregnum, Soeren
Nordby, the Norwegian archbishops — whose volume is historical knowledge, not
a spelling question, and therefore a curator call (§8a).
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))
_spec = importlib.util.spec_from_file_location(
    "merge_seeds_cross_source",
    ROOT / "scripts" / "maintenance" / "merge_seeds_cross_source.py")
MG = importlib.util.module_from_spec(_spec)
sys.modules["merge_seeds_cross_source"] = MG
_spec.loader.exec_module(MG)


def galster_key(ruler, galster="100", vol=None):
    coin = {"id": "t", "ruler": ruler, "catalog": {"galster": galster}}
    if vol:
        coin["catalog"]["galster_volume"] = vol
    return [k for k in MG._catalog_refs(coin, "danish_realm")
            if k.startswith("galster")]


class TestSourceMisspellingsResolve(unittest.TestCase):
    def test_cristian_3(self):
        self.assertEqual(galster_key("Cristian 3"), ["galster/c3g"])

    def test_chrsitian_2(self):
        self.assertEqual(galster_key("Chrsitian 2"), ["galster/c2g"])

    def test_chrsitan_2(self):
        self.assertEqual(galster_key("Chrsitan 2"), ["galster/c2g"])

    def test_they_land_in_the_same_bucket_as_the_correct_spelling(self):
        self.assertEqual(galster_key("Cristian 3"), galster_key("Christian 3"))
        self.assertEqual(galster_key("Chrsitian 2"), galster_key("Christian II"))


class TestTheTableStaysNarrow(unittest.TestCase):
    """What must NOT be silently resolved."""

    def test_no_ordinal_is_ambiguous_and_stays_bare(self):
        # «Christian» alone spans Christian I-X; guessing a volume here would
        # be inventing an attribution.
        self.assertEqual(galster_key("Christian"), ["galster"])
        self.assertEqual(galster_key("Frederik"), ["galster"])

    def test_non_regnal_authorities_stay_bare(self):
        # Galster catalogues these inside a king's volume, but WHICH king is
        # historical knowledge, not derivable from the name — a curator call.
        for r in ("Rigsrådet", "Interregnum", "Søren Nordby",
                  "Gaute Ivarsson", "Olav Engelbrektsson"):
            self.assertEqual(galster_key(r), ["galster"], r)

    def test_an_explicit_volume_always_wins_over_the_derivation(self):
        self.assertEqual(galster_key("Cristian 3", vol="hg"), ["galster/hg"])

    def test_a_correctly_spelled_ruler_is_unaffected(self):
        self.assertEqual(galster_key("Hans"), ["galster/hg"])
        self.assertEqual(galster_key("Frederik I"), ["galster/f1g"])


if __name__ == "__main__":
    unittest.main()
