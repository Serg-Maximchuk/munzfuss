"""«John» alone is Hans; «John <given-name>» is somebody else.

Numista files four different men under a «John …» name, and the builder's old
rule `^\\s*John\\b` collapsed all of them to «Hans»:

    id 8940  «John»             Hans den Yngre of Sonderburg (1545-1622)  -> Hans
    (kings)  «John (Hans)»      King Hans / John I (r. 1481-1513)         -> Hans
    id 8656  «John Adolphus»    Johan Adolf of Gottorp (r. 1590-1616)     -> NOT Hans
    id 8834  «John Adolphus I»  Johann Adolf I of Norburg-Plön (1690)     -> NOT Hans

Danish sources call the Gottorp duke «Johan Adolf» and never «Hans» (da.wikipedia
«Johan Adolf af Slesvig-Holsten-Gottorp», 27 Feb 1575 - 31 Mar 1616), while the
Sonderburg one genuinely is «Hans den Yngre». The project had already settled
«Johann Adolf» as canonical for the Gottorp duke across ~413 coins (2026-06-03,
commits f5374d0 + 1e15579) — with a numeral guard keeping the Norburg-Plön «I»
distinct — but the builder destroyed the name before the merger could apply any
of it, leaving 14 Gottorp and 2 Norburg-Plön seeds reading a bare «Hans».

What follows «John» is the discriminator: nothing, a regnal numeral, or a
parenthetical gloss means Hans; another given name means another man.

Run:
    .venv/bin/python -m unittest tests.test_numista_john_narrowing -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "maintenance"))

import build_numista_seed as B  # noqa: E402


class TestJohnMeansHans(unittest.TestCase):
    """Every shape Numista actually uses for the two men who ARE Hans."""

    def test_all_four_hans_shapes(self):
        for nm in ("John", "John I", "John (Hans)", "John I (Hans I)"):
            with self.subTest(nm=nm):
                self.assertEqual(B._canon_numista_ruler(nm), "Hans")

    def test_king_hans_via_the_chrome_kings_route(self):
        # N#444264 Norway Bergen Goldgulden carries no ruler id — only
        # `kings: [{name: 'John (Hans)', reign: '1483-1513'}]`, so the name
        # rule is the ONLY thing that can canonicalise it.
        self.assertEqual(B._resolve_ruler([{"name": "John (Hans)"}]), "Hans")


class TestJohnPlusGivenNameIsSomebodyElse(unittest.TestCase):
    def test_gottorp_duke(self):
        self.assertEqual(B._canon_numista_ruler("John Adolphus"), "Johann Adolf")

    def test_norburg_plon_duke_keeps_his_numeral(self):
        got = B._canon_numista_ruler("John Adolphus I")
        self.assertEqual(got, "Johann Adolf I")
        self.assertNotEqual(got, B._canon_numista_ruler("John Adolphus"))

    def test_glossed_forms_take_numista_s_own_german(self):
        # Numista sometimes writes «<English> (<German>)». Where it supplies
        # the period form itself we take it — a choice between two spellings
        # the source publishes, not a rendering of our own.
        self.assertEqual(B._canon_numista_ruler("John Adolphus (Johann Adolf)"),
                         "Johann Adolf")
        self.assertEqual(
            B._canon_numista_ruler("John Frederick (Johann Friedrich)"),
            "Johann Friedrich")
        self.assertEqual(
            B._canon_numista_ruler(
                "John Frederick of Holstein-Gottorp "
                "(Johann Friedrich von Holstein-Gottorp)"),
            "Johann Friedrich von Holstein-Gottorp")

    def test_bare_john_frederick_stays_as_published(self):
        # Deliberately NOT folded: it already names the right man, and the
        # general exonym→period-form pass is a separate change across all
        # sources with its own gate.
        self.assertEqual(B._canon_numista_ruler("John Frederick"),
                         "John Frederick")

    def test_other_johns_are_left_for_the_merger(self):
        # Not folded here — `_normalise_ruler` has its own guarded rules for
        # these, which the old regex pre-empted by rewriting them to «Hans».
        for nm in ("John George", "John Albert", "John Casimir"):
            with self.subTest(nm=nm):
                self.assertEqual(B._canon_numista_ruler(nm), nm)

    def test_unrelated_rulers_untouched(self):
        for nm in ("Christian IV", "Frederik VI", "Johann Adolf"):
            with self.subTest(nm=nm):
                self.assertEqual(B._canon_numista_ruler(nm), nm)


if __name__ == "__main__":
    unittest.main()
