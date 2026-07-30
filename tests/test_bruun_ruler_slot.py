"""Regression: the Bruun builder reads the ruler from its slot, not from prose.

Function under test:
    scripts/maintenance/build_bruun_denmark_seed.py :: parse_ruler_from_meta

Stack's Bowers writes every lot to one shape and gives the ruler its own slot:

    <COUNTRY>. <Type>, <year>. [<Mint> Mint[; mm: X].] <RULER>. <GRADER> …

The previous implementation promised exactly that in its docstring and then
ignored position: it concatenated meta_line + body PROSE, scanned a hard-coded
four-name allowlist and returned the first hit in LIST order, overriding a
correct hint. Five coins reached data/ with the wrong ruler.

Every negative case below is a real lot that broke one of the four drafts of
the fix — the prose bleed, the bare mint left in the slot by a cut line, a line
cut before the year, and a line ending in a full stop.

Run:
    .venv/bin/python -m unittest tests.test_bruun_ruler_slot -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "maintenance"))

from build_bruun_denmark_seed import parse_ruler_from_meta as P  # noqa: E402


class TestSlotIsRead(unittest.TestCase):
    """The plain shape — the ruler is the segment before the grading token."""

    def test_simple(self):
        self.assertEqual(
            P("DENMARK. Skilling, 1524. Ribe Mint. Frederik I. NGC AU Details—"
              "Environmental Damage. Galster-70; Sieg-21;", "", "Hans"),
            "Frederik I")

    def test_ruler_before_mint_inversion(self):
        """Lot 13066 puts the mint after the ruler; step over it once."""
        self.assertEqual(
            P("DENMARK. Largesse Ducat Klippe, 1648. Frederik III. Copenhagen "
              "Mint. NGC AU-58. Fr-75; KM-", "", None),
            "Frederik III")

    def test_country_heading_is_never_the_ruler(self):
        self.assertIsNone(
            P("DENMARK. 2 Skilling, 1533. Malmö Mint. NGC MS-62. Gal-", "", None))

    def test_ecclesiastical_issuer_needs_no_special_case(self):
        """«Hans Mule» used to be hard-coded; Olav Engelbrektsson was not, and
        so came out as Christian III. Both sit in the slot."""
        self.assertEqual(
            P("NORW AY . Double Hvid, ND (1523-24). Oslo Mint. Hans Mule. NGC "
              "VF Details - Environmental Damage.", "", "Hans"),
            "Hans Mule")
        self.assertEqual(
            P("NORW AY . Skilling, ND (1522-38). Nidaros (Trondheim) Mint. Olav "
              "Engelbrektsson. NGC EF Details—Bent. Gal-", "", None),
            "Olav Engelbrektsson")


class TestProseNeverWins(unittest.TestCase):
    """The four-name allowlist scanned narrative prose. These are the lots it
    got wrong, verified against scripts/cache/bruun/lots/."""

    def test_unrelated_foreign_prince_in_the_prose(self):
        """Bruun-4634: the body names the Duke-Elector of Saxony, Christian II,
        on a coin of Christian IV — 80 years out."""
        meta = ("DENMARK. 1/4 Speciedaler, 1602. Christian IV . NGC EF Details—"
                "Cleaned. KM-48; Hede-48; Sieg-91; Schou-1;")
        body = (meta + " … the King's younger sister, Hedvig and the "
                "Duke-Elector of Saxony, Christian II on September 12th 1602. The …")
        self.assertEqual(P(meta, body, "Christian IV"), "Christian IV")

    def test_ordinance_author_in_the_prose(self):
        """Bruun-4398: «the 1544 decree of Christian III» on a Frederik II Mark."""
        meta = ("DENMARK. Mark, 1559. Copenhagen Mint. Frederik II. NGC AU-53. "
                "Hede-9A; Sieg-15.1; Schou-1; Bruun-4398.")
        body = meta + " … and the only one struck in accordance to the 1544 decree of Christian III. …"
        self.assertEqual(P(meta, body, "Frederik II"), "Frederik II")

    def test_predecessor_named_in_the_prose(self):
        """Bruun-3964: the meta names Frederik I at char 36, the prose names
        Christian II at char 569 — and the allowlist ordered Christian II
        first, so list order beat document order."""
        meta = "DENMARK. Skilling, 1524. Ribe Mint. Frederik I. NGC AU Details—Environmental Damage."
        body = meta + " … chosen for the reverse just like the preceding Skillings from Christian II and Hans, the armored figure …"
        self.assertEqual(P(meta, body, "Hans"), "Frederik I")

    def test_engraver_and_mintmaster_never_leak(self):
        """The first repair attempt completed a truncated «Chris -» FROM the
        prose and picked up the engraver / mint-master instead."""
        meta = "DENMARK. 32 Rigsbankskilling, 1843. Altona Mint. Chris -"
        body = ("DENMARK. 32 Rigsbankskilling, 1843. Altona Mint. Chris - tian "
                "VIII. NGC MS-66. KM-734; Hede-5A; Sieg-11; Schou-5; Bruun-8163. "
                "Mintmaster: Johan Friedrich Freund. Engraver: Frederik "
                "Christopher Krohn. NGC TOP POP .")
        self.assertEqual(P(meta, body, "Christian VIII"), "Christian VIII")

        meta2 = "NORW AY . 4 Mark (Krone), 1686. Kongsberg Mint. Chris -"
        body2 = ("NORW AY . 4 Mark (Krone), 1686. Kongsberg Mint. Chris - tian V . "
                 "NGC AU-53. Dav-3665; KM-157; Hede-67A. Weight: 22.02 gms. Mint- "
                 "master: Henning Christopher Meyer, the elder. Beautifully")
        self.assertEqual(P(meta2, body2, "Christian V"), "Christian V")


class TestTruncatedLines(unittest.TestCase):
    """meta_line is a copy cut at the PDF line break; body_excerpt is the full
    line, hyphenated across the break."""

    def test_bare_mint_left_in_the_slot_is_rejected(self):
        """Cut right after the mint name, before the word «Mint»."""
        for meta in ("DENMARK. 12 Mark (Courant Ducat), 1763-K. Copenhagen",
                     "DENMARK. 12 Mark (Courant Ducat), 1783-W/CHL. Altona",
                     "NORW AY . Gold Off-Metal Strike 8 Skilling, 1783. Kongsberg",
                     "DENMARK. Speciedaler (Reichstaler), 1627. Wolfenbüttel"):
            with self.subTest(meta=meta):
                self.assertEqual(P(meta, "", "Frederik V"), "Frederik V")

    def test_line_cut_before_the_year_has_no_anchor(self):
        """No «<Type>, <year>» segment: without the digit guard the
        denomination itself reads as a name."""
        self.assertEqual(
            P("DENMARK. Schleswig-Holstein. Silver Speciedaler Pattern", "",
              "Christian VII"),
            "Christian VII")
        self.assertEqual(
            P("DENMARK. Silver Issue of Approximate Mark Weight, ND", "",
              "Christian V"),
            "Christian V")

    def test_line_ending_in_a_full_stop_still_yields_its_ruler(self):
        """«… Frederik I.» leaves an empty final split element."""
        self.assertEqual(
            P("DENMARK. 14 Penning, 1524. Malmö Mint. Frederik I.", "", None),
            "Frederik I")

    def test_single_bare_word_attributes_nothing(self):
        self.assertIsNone(
            P("DENMARK. 14 Penning, 1524. Copenhagen Mint. Frederik", "", None))


class TestHintReconciliation(unittest.TestCase):
    """Same person in two forms: keep the fuller, tie goes to the hint."""

    def test_fuller_slot_wins(self):
        self.assertEqual(
            P("GERMANY . Schleswig-Holstein-Schaumburg-Pinneberg. 3 Taler, 1598. "
              "Altona Mint. Adolf XIII. NGC A", "", "Adolf"),
            "Adolf XIII")
        self.assertEqual(
            P("SWEDEN. Bremen & Verden. 4 Mark, 1660-MM. Stade Mint. Karl X "
              "Gustav. NGC AU Details—Scratches.", "", "Karl X"),
            "Karl X Gustav")

    def test_canonical_spelling_survives_on_a_tie(self):
        """The catalogue's «Carl» / misprinted «Friederich» must not displace
        the project's canonical form when both name the same person."""
        self.assertEqual(
            P("NORW AY . Speciedaler, 1824. Kongsberg Mint. Carl XIV Johan. NGC "
              "MS-66. KM-290;", "", "Karl XIV Johan"),
            "Karl XIV Johan")
        self.assertEqual(
            P("GERMANY . Schleswig-Holstein-Gottorp. Ducat, 1642-HG. Friederich "
              "III. NGC AU-53.", "", "Friedrich III"),
            "Friedrich III")

    def test_a_different_person_replaces_the_hint(self):
        self.assertEqual(
            P("SWEDEN. 4 Skilling, 1535. Stockholm Mint. Gustav Vasa. NGC VF-35. "
              "Galster-251;", "", "Christian III"),
            "Gustav Vasa")


if __name__ == "__main__":
    unittest.main()
