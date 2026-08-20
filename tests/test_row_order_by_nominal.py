"""Rows of one year order by `fraction`, not by the coin id.

The 1604 gold Klippen rendered as 4 · 6 · 8 · 3 Daler. All four share a year,
so the sort fell through to its last key — the id — and ids carry provenance
(`dk-tid-163409`, `km-27-chr-iv-1604`, `unified-dk-hede-c4h13`), which has
nothing to do with denomination. The table read as unsorted.

`fraction` is the coin's size in the FUSS's own unit, so it compares a
½ Speciedaler against a 4 Skilling correctly — the bare quantities off the
nominal («½» vs «4») do not, and sorting on those alone put an 8 Skilling
after a 2 Speciedaler. It is filled in as each standard is worked through;
until then a coin falls back to the quantity its nominal displays and sorts
after the coins that do carry one, so the two scales never interleave.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from lib.categorize import _fraction_value, _nominal_magnitude  # noqa: E402


class TestFractionValue(unittest.TestCase):
    def test_whole_and_fractional(self):
        self.assertEqual(_fraction_value("4"), 4.0)
        self.assertEqual(_fraction_value("1/2"), 0.5)
        self.assertEqual(_fraction_value("3/2"), 1.5)
        self.assertEqual(_fraction_value("1/96"), 1 / 96)

    def test_absent_or_unparseable(self):
        for v in (None, "", "n/a", "1/0"):
            self.assertIsNone(_fraction_value(v), repr(v))

    def test_it_compares_across_denominations(self):
        # The point of using fraction rather than the nominal's number:
        # 4 Skilling is 1/24 of a Speciedaler, so it must sort BELOW ½.
        self.assertLess(_fraction_value("1/24"), _fraction_value("1/2"))
        # …whereas the bare nominal quantities would say the opposite.
        self.assertGreater(_nominal_magnitude("4 Skilling"),
                           _nominal_magnitude("½ Speciedaler"))


class TestMagnitude(unittest.TestCase):
    def test_whole_numbers(self):
        for nom, want in (("4 Daler", 4.0), ("8 Daler", 8.0),
                          ("10 Kroner", 10.0), ("1 Ungersk Gylden", 1.0)):
            self.assertEqual(_nominal_magnitude(nom), want, nom)

    def test_vulgar_fractions(self):
        self.assertEqual(_nominal_magnitude("½ Dukat"), 0.5)
        self.assertEqual(_nominal_magnitude("¼ Portugaløser"), 0.25)

    def test_ascii_fractions(self):
        self.assertEqual(_nominal_magnitude("1/16 Reichsthaler"), 0.0625)

    def test_a_nominal_with_no_quantity_is_none(self):
        # None means «sort last», not «sort as zero» — a zero would place it
        # ahead of every fraction.
        self.assertIsNone(_nominal_magnitude("(?)"))
        self.assertIsNone(_nominal_magnitude(""))
        self.assertIsNone(_nominal_magnitude(None))


def _key(frac, nominal, cid):
    """The row-order key, minus the year — mirrors categorize._row_order."""
    f = _fraction_value(frac)
    m = _nominal_magnitude(nominal)
    return (f is None, f if f is not None else 0.0,
            m is None, m if m is not None else 0.0, cid)


class TestTheRegressionCase(unittest.TestCase):
    def test_the_1604_klippen_come_out_ascending(self):
        rows = [("4", "4 Daler", "dk-tid-163409"),
                ("6", "6 Daler", "dk-tid-163410"),
                ("8", "8 Daler", "km-27-chr-iv-1604"),
                ("3", "3 Daler", "unified-dk-hede-c4h13")]
        rows.sort(key=lambda r: _key(*r))
        self.assertEqual([r[1] for r in rows],
                         ["3 Daler", "4 Daler", "6 Daler", "8 Daler"])

    def test_coins_without_a_fraction_sort_after_those_with_one(self):
        rows = [(None, "8 Skilling", "b"), ("1/2", "½ Speciedaler", "a")]
        rows.sort(key=lambda r: _key(*r))
        self.assertEqual([r[1] for r in rows], ["½ Speciedaler", "8 Skilling"])

    def test_unprocessed_coins_still_order_among_themselves(self):
        rows = [(None, "8 Daler", "b"), (None, "3 Daler", "a"),
                (None, "4 Daler", "c")]
        rows.sort(key=lambda r: _key(*r))
        self.assertEqual([r[1] for r in rows],
                         ["3 Daler", "4 Daler", "8 Daler"])

    def test_the_id_still_breaks_a_genuine_tie(self):
        rows = [("1", "1 Dukat", "z-id"), ("1", "1 Dukat", "a-id")]
        rows.sort(key=lambda r: _key(*r))
        self.assertEqual([r[2] for r in rows], ["a-id", "z-id"])


class TestLiveOrdering(unittest.TestCase):
    def test_the_dalerfod_table_is_ascending_in_the_built_page(self):
        """Read the nominal CELLS, not the page.

        A plain search for «4 Daler» finds the fuss description and the
        bibliography first — both quote the ordinance's denominations, and both
        sit above the table. The first version of this test did exactly that
        and reported an order that no table has. The cells also join the
        quantity to the denomination with a non-breaking space, so the literal
        «4 Daler» does not occur in them at all.
        """
        import re
        page = ROOT / "site" / "denmark" / "uk" / "index.html"
        if not page.exists():
            self.skipTest("site/ not built")
        html = page.read_text(encoding="utf-8")
        # Scope to the fuss whose ordering is under test. Searching the WHOLE
        # page was only ever right while the four 1604 Klippen were the only
        # «N Daler» rows on it; since the seed_unsorted holding pens are
        # completed from what the coins carry (43e3ed4), the kmk and ikmk pens
        # render eighteen more — un-triaged museum Daler that say nothing about
        # how one fuss's table sorts. The assertion is about row order inside a
        # standard, so it reads one standard's section.
        block = re.search(
            r'<section class="fuss-block fuss-115_5_daler_fod"[^>]*>'
            r'(.*?)(?=<section class="fuss-block |\Z)', html, re.S)
        self.assertIsNotNone(block, "115_5_daler_fod section not on the page")
        cells = [re.sub(r"\s+", " ", m.group(1)).replace("&nbsp;", " ").strip()
                 for m in re.finditer(r'class="c-nom[^"]*"[^>]*>(.{0,60}?)</td>',
                                      block.group(1), re.S)]
        dalers = [c for c in cells if re.fullmatch(r"\d+ Daler", c)]
        self.assertEqual(dalers, ["3 Daler", "4 Daler", "6 Daler", "8 Daler"])


if __name__ == "__main__":
    unittest.main()
