"""Regression: a «cf.»-class comparison in danskmoent prose must not be
captured as the page's own catalogue index.

danskmoent.dk writes cross-references as running prose — «Slået med samme
stempler som Hede 104» (struck from the same dies as…), «Som Hede 61B»,
«Bagsiden minder om Danmark Hede 82». The refs regex anchors on the bare
catalogue name, so it harvested those numbers onto the CITING page: c5h105
carried Hede ['105', '104'], nc5h7 carried ['7', '8', '9'] where the 9 is the
DANISH Hede 9 named in «Slået med same stempler som 1/4 dukat, Danmark Hede 9».

Per CLAUDE.md anti-pattern 5 a «cf.» reference points at a similar OTHER coin
and must never sit in a catalogue index field. On the Norwegian volumes it is
additionally cross-COUNTRY contamination — a Danish index landing on a
Norwegian page — which is the fuel for the Hede-series collision gated in
merge_seeds_cross_source._hede_series.

Measured effect of the guard over the 836 cached pages: 9 pages lose a foreign
number, no page loses its own. The seed layer was already immune (the builder
picks the page-canonical number), so this is defence in depth at the parse
layer, where `catalog_refs` is consumed by build_hede_denmark_seed.

Added 2026-07-25.

Run:
    .venv/bin/python -m unittest tests.test_parse_hede_crossref_guard -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import parse_hede as P  # noqa: E402


class TestCrossReferenceRejected(unittest.TestCase):
    def test_samme_stempler_som(self):
        """c5h105 — «struck from the same dies as Hede 104»."""
        txt = "Slået med samme stempler som  Hede 104 . Stemplerne er skåret af"
        self.assertIsNone(P._extract_refs(txt).get("Hede"))

    def test_bare_som(self):
        """c5h61 — «Som Hede 61B (Hede 62, …)»: the comparison is dropped, the
        parenthetical own-index is kept."""
        refs = P._extract_refs("Som Hede 61B (Hede 62, Schou 42, Sieg 59)")
        self.assertEqual(refs.get("Hede"), ["62"])

    def test_danmark_qualified_crossref(self):
        """nc5h7 — a DANISH index named on a NORWEGIAN page."""
        txt = "Slået med same stempler som 1/4 dukat, Danmark Hede 9"
        self.assertIsNone(P._extract_refs(txt).get("Hede"))

    def test_minder_om_across_a_line_break(self):
        """nc5h66 — «the reverse resembles Danmark Hede 82», wrapped."""
        self.assertIsNone(
            P._extract_refs("Bagsiden minder om \nDanmark Hede 82 .").get("Hede"))

    def test_guard_applies_to_other_catalogues_too(self):
        """A cf reference is a cf reference whatever the catalogue."""
        self.assertIsNone(P._extract_refs("som Schou 15").get("Schou"))


class TestLegitimateRefsKept(unittest.TestCase):
    def test_norwegian_page_title_is_not_a_crossref(self):
        """«Norge» must NOT be treated as a comparison word — «Christian 5.,
        Norge Hede 1» is the page's own title (55 occurrences in the cache).
        Blocking it would re-break the whole Norwegian corpus."""
        txt = "Christian 5., Norge Hede 1 Christian 5. 3 og 4 Dukat"
        self.assertEqual(P._extract_refs(txt).get("Hede"), ["1"])

    def test_own_ref_after_nominal(self):
        self.assertEqual(
            P._extract_refs("1 Dukat, Hede Norge 7 Bruttovægt").get("Hede"), ["7"])

    def test_parenthetical_own_ref(self):
        self.assertEqual(
            P._extract_refs("(Hede 108, Schou 54, Sieg 15)").get("Hede"), ["108"])


if __name__ == "__main__":
    unittest.main()
