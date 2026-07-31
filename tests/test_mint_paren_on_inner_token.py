"""A paren gloss on a non-final mint token kept one mint rendering as two.

`_canonicalise_mint` strips a parenthetical tail once, from the WHOLE string,
and only then splits on commas. Numista's chrome-route mint reads

    «Royal Danish Mint (Den Kongelige Mønt), Copenhagen, Denmark (1739-date)»

so the outer strip removed «(1739-date)» and the first token kept its own
gloss. «Royal Danish Mint (Den Kongelige Mønt)» is not in the alias table —
«Royal Danish» is, and maps to Kopenhagen — so the institution survived beside
the city and 37 seed entries carried the same mint twice, as
`['Kopenhagen', 'Royal Danish Mint (Den Kongelige Mønt)']`.

That duplicate then read as a genuine multi-mint list downstream, which is how
NumisMaster appeared to «beat» Numista on mint accuracy in 27 of 43
head-to-head comparisons — an artefact, not a reliability difference.

mint_registry's own comment already assumed the suffix-strip would reach that
token. Stripping the paren per token as well makes it so; every other behaviour
of the canonicaliser is unchanged.

Run:
    .venv/bin/python -m unittest tests.test_mint_paren_on_inner_token -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from lib.v2_seed_writer import _canonicalise_mint  # noqa: E402


class TestParenOnInnerToken(unittest.TestCase):
    def test_the_numista_chrome_blob_collapses_to_one_mint(self):
        raw = ("Royal Danish Mint (Den Kongelige Mønt), Copenhagen, "
               "Denmark (1739-date)")
        self.assertEqual(_canonicalise_mint(raw), "Kopenhagen")

    def test_institution_and_city_in_a_list_collapse_too(self):
        self.assertEqual(
            _canonicalise_mint(["Royal Danish Mint", "Copenhagen"]), "Kopenhagen")


class TestNothingElseChanged(unittest.TestCase):
    def test_genuine_joint_mint_survives(self):
        self.assertEqual(
            _canonicalise_mint(["Royal Danish Mint", "Altona, Schleswig-Holstein"]),
            ["Altona", "Kopenhagen"])

    def test_mintmaster_paren_still_stripped(self):
        self.assertEqual(_canonicalise_mint("Altona (FK VS)"), "Altona")

    def test_region_suffix_still_dropped(self):
        self.assertEqual(_canonicalise_mint("Glückstadt, Schleswig-Holstein"),
                         "Glückstadt")

    def test_repeated_identical_entries_still_dedupe(self):
        self.assertEqual(_canonicalise_mint(["Copenhagen"] * 3), "Kopenhagen")

    def test_uncertainty_marker_survives(self):
        self.assertEqual(_canonicalise_mint("København?"), "Kopenhagen?")

    def test_certain_still_beats_uncertain(self):
        self.assertEqual(_canonicalise_mint(["København?", "Copenhagen"]),
                         "Kopenhagen")

    def test_empty_and_none(self):
        self.assertIsNone(_canonicalise_mint(None))
        self.assertIsNone(_canonicalise_mint([]))
        self.assertIsNone(_canonicalise_mint("Denmark"))  # country-only


if __name__ == "__main__":
    unittest.main()
