"""An off-strike aside must not donate its catalogue number to the mother coin.

A danskmoent page cites the numbers of off-strikes struck from the same dies
alongside the coin's own. Harvested indiscriminately, the mother ends up
carrying another coin's index — and `schou/<ruler>` is a matcher key, so that
is a FALSE §9.4 unifying edge, not merely a wrong cell. 22 pages were affected;
the «a» suffix is the afslag notation, as dk-bruun-7396 «Schou 1a» and
dk-bruun-7894 «Schou 7a» independently confirm.

The masking is easy to get wrong in BOTH directions, and each of these tests
pins a mistake that was actually made while writing it (2026-08-07):

  * blanking the whole clause emptied six pages' OWN Sieg/Hede/Schou, because
    the page's closing «, Sieg 156» sits inside the same parenthetical as the
    aside;
  * masking writes spaces to keep offsets valid, and the ref regex bridges
    whitespace — so removing «Schou 7a» from «Schou 7a og 7b» let the preceding
    match swallow « og 7b»;
  * a row that OPENS with the marker («Sølvafslag 1673, Schou 7b») governs a
    YEAR, so masking just the governed token left «, Schou 7b» behind.
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "parse_hede", Path(__file__).resolve().parent.parent / "scripts" / "parse_hede.py")
PH = importlib.util.module_from_spec(_spec)
sys.modules["parse_hede"] = PH
_spec.loader.exec_module(PH)


def schou(text):
    return PH._extract_refs(text).get("Schou")


def refs(text):
    return PH._extract_refs(text)


class TestAsideIsDropped(unittest.TestCase):
    def test_inline_after_full_stop(self):
        # nc5h10 — the sølvafslag's 3a-3c must not join Hede Norge 10's Schou 3.
        self.assertEqual(
            schou("(Hede Norge 10, Schou 3. Sølvafslag Schou 3a-3c)"), ["3"])

    def test_inline_after_semicolon(self):
        # nc5h15
        self.assertEqual(
            schou("(Hede Norge 15, Schou 1; Sølvafslag Schou 1a)"), ["1"])

    def test_nested_parenthetical(self):
        # nc5h18 — both Schou 1s survive; only the nested 1c goes.
        self.assertEqual(
            schou("(Hede Norge 18, Schou hhv. 1 (Sølvafslag 1c) og 1)"), ["1"])

    def test_multiline_findes_ogsaa_i_guld(self):
        # c7h25 — one sentence broken across four cache lines.
        self.assertEqual(
            schou("(Hede 25, Schou 7, Sieg 26.\nFindes også i guld\n(\n"
                  "20 dukat\n; Schou 7a, RR)."), ["7"])

    def test_og_chain_after_the_marker(self):
        # c5h3 — «Schou 7a og 7b»: the chain must go too, or the preceding
        # «Schou 7» match bridges the blanked span and picks 7b up.
        self.assertEqual(
            schou("(Hede 3, Schou 7, Sieg 118; Sølvafslag Schou 7a og 7b)"),
            ["7"])

    def test_specimen_row_with_trailing_marker(self):
        # nc5h13 / nc5h10 Zincksamlingen rows.
        self.assertIsNone(schou("1673, Schou 6a, sølvafslag"))

    def test_specimen_row_with_leading_marker(self):
        # c5h3 — the marker governs the YEAR here, not the reference.
        self.assertIsNone(schou("Sølvafslag 1673, Schou 7b"))

    def test_specimen_row_marker_in_the_middle(self):
        self.assertIsNone(schou("u. år (1699), Sølvafslag, Schou 1c"))


class TestThePagesOwnRefsSurvive(unittest.TestCase):
    """Every one of these was emptied by the first version of the mask."""

    def test_closing_sieg_of_the_parenthetical_is_kept(self):
        # c4h9 — Sieg 156 closes the whole bracket and belongs to Hede 9.
        r = refs("(Hede 9, Schou 1-6; sølvafslag Schou 30 RRR, Sieg 156)")
        self.assertEqual(r.get("Sieg"), ["156"])
        self.assertEqual(r.get("Schou"), ["1-6"])

    def test_bare_numbered_afslag_does_not_eat_the_sieg(self):
        # f4h1 — «sølvafslag 1b-1e» has no catalogue word of its own.
        r = refs("(Hede 1, Schou 1; sølvafslag 1b-1e, Sieg 52)")
        self.assertEqual(r.get("Sieg"), ["52"])
        self.assertEqual(r.get("Schou"), ["1"])

    def test_som_guldafslag_describes_this_very_coin(self):
        # f3hej — Hede itself calls the page's coin an off-strike, so Hede 72
        # is its OWN number, not another piece's.
        self.assertEqual(
            refs("Anføres af Hede som guldafslag af 1/2 speciedaler (Hede 72)"
                 ).get("Hede"), ["72"])

    def test_a_page_with_no_aside_is_untouched(self):
        r = refs("(Hede 28A, Schou hhv. 3-4 og 3, Sieg 133)")
        self.assertEqual(r.get("Schou"), ["3-4", "3"])
        self.assertEqual(r.get("Sieg"), ["133"])


class TestMaskingMechanics(unittest.TestCase):
    def test_offsets_are_preserved(self):
        # Callers slice the text by position, so the mask must replace with
        # spaces rather than delete.
        t = "(Hede Norge 15, Schou 1; Sølvafslag Schou 1a)"
        self.assertEqual(len(PH._mask_afslag_spans(t)), len(t))

    def test_line_structure_is_preserved(self):
        t = "a\nSølvafslag 1673, Schou 7b\nb"
        self.assertEqual(PH._mask_afslag_spans(t).count("\n"), t.count("\n"))


if __name__ == "__main__":
    unittest.main()
